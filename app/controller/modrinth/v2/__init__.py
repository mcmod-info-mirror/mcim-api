from fastapi import APIRouter, Query, Path, Request, BackgroundTasks
from typing import List, Optional, Union, Dict, Annotated
from enum import Enum
from pydantic import BaseModel, Field
from odmantic import query
import json
import time
from datetime import datetime

from app.sync import *
from app.models.database.modrinth import Project, Version, File
from app.models.response.modrinth import SearchResponse
from app.sync.modrinth import async_tags
from app.sync_queue.modrinth import (
    add_modrinth_project_ids_to_queue,
    add_modrinth_version_ids_to_queue,
    add_modrinth_hashes_to_queue,
)
from app.config.mcim import MCIMConfig
from app.utils.response import (
    TrustableResponse,
    UncachedResponse,
    BaseResponse,
)
from app.utils.network import request as request_async
from app.utils.loger import log
from app.utils.response_cache import cache

mcim_config = MCIMConfig.load()

API = mcim_config.modrinth_api
v2_router = APIRouter(prefix="/v2", tags=["modrinth"])

SEARCH_TIMEOUT = 3


class ModrinthStatistics(BaseModel):
    projects: int
    versions: int
    files: int


@v2_router.get(
    "/statistics",
    description="Modrinth 缓存统计信息",
    response_model=ModrinthStatistics,
    include_in_schema=False,
)
@cache(expire=3600)
async def modrinth_statistics(request: Request):
    """
    没有统计 author
    """
    # count
    project_count = await request.app.state.aio_mongo_engine.count(Project)
    version_count = await request.app.state.aio_mongo_engine.count(Version)
    file_count = await request.app.state.aio_mongo_engine.count(File)
    return BaseResponse(
        content=ModrinthStatistics(
            projects=project_count, versions=version_count, files=file_count
        )
    )


@v2_router.get(
    "/project/{idslug}",
    description="Modrinth Project 信息",
    response_model=Project,
)
@cache(expire=mcim_config.expire_second.modrinth.project)
async def modrinth_project(request: Request, idslug: str):
    trustable = True
    model: Optional[Project] = await request.app.state.aio_mongo_engine.find_one(
        Project, query.or_(Project.id == idslug, Project.slug == idslug)
    )
    if model is None:
        await add_modrinth_project_ids_to_queue(project_ids=[idslug])
        log.debug(f"Project {idslug} not found, add to queue.")
        return UncachedResponse()
    return TrustableResponse(content=model.model_dump(), trustable=trustable)


@v2_router.get(
    "/projects",
    description="Modrinth Projects 信息",
    response_model=List[Project],
)
@cache(expire=mcim_config.expire_second.modrinth.project)
async def modrinth_projects(ids: str, request: Request):
    ids_list: List[str] = json.loads(ids)
    trustable = True
    # id or slug
    models: Optional[List[Project]] = await request.app.state.aio_mongo_engine.find(
        Project,
        query.and_(
            query.or_(
                query.in_(Project.id, ids_list), query.in_(Project.slug, ids_list)
            ),
        ),
    )
    models_count = len(models)
    ids_count = len(ids_list)
    if not models:
        await add_modrinth_project_ids_to_queue(project_ids=ids_list)
        log.debug(f"Projects {ids_list} not found, add to queue.")
        return UncachedResponse()
    elif models_count != ids_count:
        # 找出没找到的 project_id
        not_match_ids = list(set(ids_list) - set([model.id for model in models]))
        await add_modrinth_project_ids_to_queue(project_ids=not_match_ids)
        log.debug(
            f"Projects {not_match_ids} {not_match_ids}/{ids_count} not found, add to queue."
        )
        trustable = False
    return TrustableResponse(
        content=[model.model_dump() for model in models], trustable=trustable
    )


@v2_router.get(
    "/project/{idslug}/version",
    description="Modrinth Projects 全部版本信息",
    response_model=List[Project],
)
@cache(expire=mcim_config.expire_second.modrinth.version)
async def modrinth_project_versions(idslug: str, request: Request):
    """
    先查 Project 的 Version 列表再拉取...避免遍历整个 Version 表
    """
    trustable = True
    project_model: Optional[Project] = (
        await request.app.state.aio_mongo_engine.find_one(
            Project, query.or_(Project.id == idslug, Project.slug == idslug)
        )
    )
    if not project_model:
        await add_modrinth_project_ids_to_queue(project_ids=[idslug])
        log.debug(f"Project {idslug} not found, add to queue.")
        return UncachedResponse()
    else:
        version_list = project_model.versions
        version_model_list: Optional[List[Version]] = (
            await request.app.state.aio_mongo_engine.find(
                Version, query.in_(Version.id, version_list)
            )
        )

        return TrustableResponse(
            content=(
                [version.model_dump() for version in version_model_list]
                if version_model_list
                else []
            ),
            trustable=trustable,
        )


async def check_search_result(request: Request, search_result: dict):
    project_ids = set([project["project_id"] for project in search_result["hits"]])

    if project_ids:
        # check project in db
        project_models: List[Project] = await request.app.state.aio_mongo_engine.find(
            Project, query.in_(Project.id, list(project_ids))
        )

        not_found_project_ids = project_ids - set(
            [project.id for project in project_models]
        )

        if not_found_project_ids:
            await add_modrinth_project_ids_to_queue(
                project_ids=list(not_found_project_ids)
            )
            log.debug(f"Projects {not_found_project_ids} not found, add to queue.")
        else:
            log.debug(f"All Projects found.")
    else:
        log.debug("Search esult is empty")


class SearchIndex(str, Enum):
    relevance = "relevance"
    downloads = "downloads"
    follows = "follows"
    newest = "newest"
    updated = "updated"


@v2_router.get(
    "/search",
    description="Modrinth Projects 搜索",
    response_model=SearchResponse,
)
@cache(expire=mcim_config.expire_second.modrinth.search)
async def modrinth_search_projects(
    request: Request,
    query: Optional[str] = None,
    facets: Optional[str] = None,
    offset: Optional[int] = 0,
    limit: Optional[int] = 10,
    index: Optional[SearchIndex] = SearchIndex.relevance,
):
    res = (
        await request_async(
            f"{API}/v2/search",
            params={
                "query": query,
                "facets": facets,
                "offset": offset,
                "limit": limit,
                "index": index.value,
            },
            timeout=SEARCH_TIMEOUT,
        )
    ).json()
    await check_search_result(request=request, search_result=res)
    return TrustableResponse(content=res)


@v2_router.get(
    "/version/{id}",
    description="Modrinth Version 信息",
    response_model=Version,
)
@cache(expire=mcim_config.expire_second.modrinth.version)
async def modrinth_version(
    version_id: Annotated[str, Path(alias="id", pattern=r"[a-zA-Z0-9]{8}")],
    request: Request,
):
    trustable = True
    model: Optional[Version] = await request.app.state.aio_mongo_engine.find_one(
        Version,
        Version.id == version_id,
    )
    if model is None:
        await add_modrinth_version_ids_to_queue(version_ids=[version_id])
        log.debug(f"Version {version_id} not found, add to queue.")
        return UncachedResponse()
    return TrustableResponse(content=model.model_dump(), trustable=trustable)


@v2_router.get(
    "/versions",
    description="Modrinth Versions 信息",
    response_model=List[Version],
)
@cache(expire=mcim_config.expire_second.modrinth.version)
async def modrinth_versions(ids: str, request: Request):
    trustable = True
    ids_list = json.loads(ids)
    models: List[Version] = await request.app.state.aio_mongo_engine.find(
        Version, query.and_(query.in_(Version.id, ids_list))
    )
    models_count = len(models)
    ids_count = len(ids_list)
    if not models:
        await add_modrinth_version_ids_to_queue(version_ids=ids_list)
        log.debug(f"Versions {ids_list} not found, add to queue.")
        return UncachedResponse()
    elif models_count != ids_count:
        await add_modrinth_version_ids_to_queue(version_ids=ids_list)
        log.debug(
            f"Versions {ids_list} {models_count}/{ids_count} not completely found, add to queue."
        )
        trustable = False
    return TrustableResponse(
        content=[model.model_dump() for model in models], trustable=trustable
    )


class Algorithm(str, Enum):
    sha1 = "sha1"
    sha512 = "sha512"


@v2_router.get(
    "/version_file/{hash}",
    description="Modrinth File 信息",
    response_model=Version,
)
@cache(expire=mcim_config.expire_second.modrinth.file)
async def modrinth_file(
    request: Request,
    hash_: Annotated[str, Path(alias="hash", pattern=r"[a-zA-Z0-9]{40}|[a-zA-Z0-9]{128}")],
    algorithm: Optional[Algorithm] = Algorithm.sha1,
):
    trustable = True
    # ignore algo
    file: Optional[File] = await request.app.state.aio_mongo_engine.find_one(
        File,
        (
            File.hashes.sha512 == hash_
            if algorithm == Algorithm.sha512
            else File.hashes.sha1 == hash_
        ),
    )
    if file is None:
        await add_modrinth_hashes_to_queue([hash_], algorithm=algorithm.value)
        log.debug(f"File {hash_} not found, add to queue.")
        return UncachedResponse()

    # get version object
    version: Optional[Version] = await request.app.state.aio_mongo_engine.find_one(
        Version, query.and_(Version.id == file.version_id)
    )
    if version is None:
        await add_modrinth_version_ids_to_queue(version_ids=[file.version_id])
        log.debug(f"Version {file.version_id} not found, add to queue.")
        return UncachedResponse()

    return TrustableResponse(content=version, trustable=trustable)


class HashesQuery(BaseModel):
    hashes: List[Annotated[str, Field(pattern=r"[a-zA-Z0-9]{40}|[a-zA-Z0-9]{128}")]]
    algorithm: Algorithm


@v2_router.post(
    "/version_files",
    description="Modrinth Files 信息",
    response_model=Dict[str, Version],
)
# @cache(expire=mcim_config.expire_second.modrinth.file)
async def modrinth_files(items: HashesQuery, request: Request):
    trustable = True
    # ignore algo
    files_models: List[File] = await request.app.state.aio_mongo_engine.find(
        File,
        query.and_(
            (
                query.in_(File.hashes.sha1, items.hashes)
                if items.algorithm == Algorithm.sha1
                else query.in_(File.hashes.sha512, items.hashes)
            ),
        ),
    )
    model_count = len(files_models)
    hashes_count = len(items.hashes)
    if not files_models:
        await add_modrinth_hashes_to_queue(
            items.hashes, algorithm=items.algorithm.value
        )
        log.debug("Files not found, add to queue.")
        return UncachedResponse()
    elif model_count != hashes_count:
        # 找出未找到的文件
        not_found_hashes = list(
            set(items.hashes)
            - set(
                [
                    (
                        file.hashes.sha1
                        if items.algorithm == Algorithm.sha1
                        else file.hashes.sha512
                    )
                    for file in files_models
                ]
            )
        )
        if not_found_hashes:
            await add_modrinth_hashes_to_queue(
                not_found_hashes, algorithm=items.algorithm.value
            )
            log.debug(
                f"Files {not_found_hashes} {len(not_found_hashes)}/{hashes_count} not completely found, add to queue."
            )
            trustable = False

    version_ids = [file.version_id for file in files_models]
    version_models: List[Version] = await request.app.state.aio_mongo_engine.find(
        Version, query.in_(Version.id, version_ids)
    )

    version_model_count = len(version_models)
    file_model_count = len(files_models)
    if not version_models:
        # 一个版本都没找到，直接重新同步
        await add_modrinth_version_ids_to_queue(version_ids=version_ids)
        log.debug("Versions not found, add to queue.")
        return UncachedResponse()
    elif version_model_count != file_model_count:
        # 找出未找到的版本
        not_found_version_ids = list(
            set(version_ids) - set([version.id for version in version_models])
        )
        if not_found_version_ids:
            await add_modrinth_version_ids_to_queue(version_ids=not_found_version_ids)
            log.debug(
                f"Versions {not_found_version_ids} {len(not_found_version_ids)}/{file_model_count} not completely found, add to queue."
            )
            trustable = False
    result = {}
    for version in version_models:
        result[
            (
                version.files[0].hashes.sha1
                if items.algorithm == Algorithm.sha1
                else version.files[0].hashes.sha2
            )
        ] = version.model_dump()

    return TrustableResponse(content=result, trustable=trustable)


class UpdateItems(BaseModel):
    loaders: List[str]
    game_versions: List[str]


@v2_router.post("/version_file/{hash}/update")
@cache(expire=mcim_config.expire_second.modrinth.file)
async def modrinth_file_update(
    request: Request,
    items: UpdateItems,
    hash_: Annotated[str, Path(alias="hash", pattern=r"[a-zA-Z0-9]{40}|[a-zA-Z0-9]{128}")],
    algorithm: Optional[Algorithm] = Algorithm.sha1,
):
    trustable = True
    files_collection = request.app.state.aio_mongo_engine.get_collection(File)
    pipeline = [
        (
            {"$match": {"_id.sha1": hash_}}
            if algorithm is Algorithm.sha1
            else {"$match": {"_id.sha512": hash_}}
        ),
        {
            "$project": (
                {"_id.sha1": 1, "project_id": 1}
                if algorithm is Algorithm.sha1
                else {"_id.sha512": 1, "project_id": 1}
            )
        },
        {
            "$lookup": {
                "from": "modrinth_versions",
                "localField": "project_id",
                "foreignField": "project_id",
                "as": "versions_fields",
            }
        },
        {"$unwind": "$versions_fields"},
        {
            "$match": {
                "versions_fields.game_versions": {"$in": items.game_versions},
                "versions_fields.loaders": {"$in": items.loaders},
            }
        },
        {"$sort": {"versions_fields.date_published": -1}},
        {"$replaceRoot": {"newRoot": "$versions_fields"}},
    ]
    version_result = await files_collection.aggregate(pipeline).to_list(length=None)
    if len(version_result) != 0:
        version_result = version_result[0]
        if not (
            datetime.strptime(
                version_result["sync_at"], "%Y-%m-%dT%H:%M:%SZ"
            ).timestamp()
            + mcim_config.expire_second.modrinth.file
            > time.time()
        ):
            trustable = False
    else:
        await add_modrinth_hashes_to_queue([hash_], algorithm=algorithm.value)
        log.debug(f"Hash {hash_} not found, send sync task")
        return UncachedResponse()
    return TrustableResponse(content=version_result, trustable=trustable)


class MultiUpdateItems(BaseModel):
    hashes: List[Annotated[str, Field(pattern=r"[a-zA-Z0-9]{40}|[a-zA-Z0-9]{128}")]]
    algorithm: Algorithm
    loaders: Optional[List[str]]
    game_versions: Optional[List[str]]


@v2_router.post("/version_files/update")
# @cache(expire=mcim_config.expire_second.modrinth.file)
async def modrinth_mutil_file_update(request: Request, items: MultiUpdateItems):
    trustable = True
    files_collection = request.app.state.aio_mongo_engine.get_collection(File)
    pipeline = [
        (
            {"$match": {"_id.sha1": {"$in": items.hashes}}}
            if items.algorithm is Algorithm.sha1
            else {"$match": {"_id.sha512": {"$in": items.hashes}}}
        ),
        {
            "$project": (
                {"_id.sha1": 1, "project_id": 1}
                if items.algorithm is Algorithm.sha1
                else {"_id.sha512": 1, "project_id": 1}
            )
        },
        {
            "$lookup": {
                "from": "modrinth_versions",
                "localField": "project_id",
                "foreignField": "project_id",
                "as": "versions_fields",
            }
        },
        {"$unwind": "$versions_fields"},
        {
            "$match": {
                "versions_fields.game_versions": {"$in": items.game_versions},
                "versions_fields.loaders": {"$in": items.loaders},
            }
        },
        {"$sort": {"versions_fields.date_published": -1}},
        {
            "$group": {
                "_id": (
                    "$_id.sha1" if items.algorithm is Algorithm.sha1 else "$_id.sha512"
                ),
                "latest_date": {"$first": "$versions_fields.date_published"},
                "detail": {"$first": "$versions_fields"},  # 只保留第一个匹配版本
            }
        },
    ]
    versions_result = await files_collection.aggregate(pipeline).to_list(length=None)
    if len(versions_result) == 0:
        await add_modrinth_hashes_to_queue(
            items.hashes, algorithm=items.algorithm.value
        )
        log.debug(f"Hashes {items.hashes} not found, send sync task")
        return UncachedResponse()
    elif len(versions_result) != len(items.hashes):
        # 找出未找到的文件
        not_found_hashes = list(
            set(items.hashes) - set([version["_id"] for version in versions_result])
        )
        if not_found_hashes:
            await add_modrinth_hashes_to_queue(
                not_found_hashes, algorithm=items.algorithm.value
            )
            log.debug(f"Hashes {not_found_hashes} not completely found, add to queue.")
            trustable = False
    else:
        # check expire
        resp = {}
        for version_result in versions_result:
            original_hash = version_result["_id"]
            version_detail = version_result["detail"]
            resp[original_hash] = version_detail
            if not (
                datetime.strptime(
                    version_detail["sync_at"], "%Y-%m-%dT%H:%M:%SZ"
                ).timestamp()
                + mcim_config.expire_second.modrinth.file
                > time.time()
            ):
                trustable = False
        return TrustableResponse(content=resp, trustable=trustable)


@v2_router.get(
    "/tag/category",
    description="Modrinth Category 信息",
    response_model=List,
)
@cache(expire=mcim_config.expire_second.modrinth.category)
async def modrinth_tag_categories(request: Request):
    category = await request.app.state.aio_redis_engine.hget("modrinth", "categories")
    if category is None:
        await async_tags()
        log.debug("Category not found, sync.")
        category = await request.app.state.aio_redis_engine.hget(
            "modrinth", "categories"
        )
    return TrustableResponse(content=json.loads(category))


@v2_router.get(
    "/tag/loader",
    description="Modrinth Loader 信息",
    response_model=List,
)
@cache(expire=mcim_config.expire_second.modrinth.category)
async def modrinth_tag_loaders(request: Request):
    loader = await request.app.state.aio_redis_engine.hget("modrinth", "loaders")
    if loader is None:
        await async_tags()
        log.debug("Loader not found, sync.")
        loader = await request.app.state.aio_redis_engine.hget("modrinth", "loaders")
    return TrustableResponse(content=json.loads(loader))


@v2_router.get(
    "/tag/game_version",
    description="Modrinth Game Version 信息",
    response_model=List,
)
@cache(expire=mcim_config.expire_second.modrinth.category)
async def modrinth_tag_game_versions(request: Request):
    game_version = await request.app.state.aio_redis_engine.hget(
        "modrinth", "game_versions"
    )
    if game_version is None:
        await async_tags()
        log.debug("Game Version not found, sync.")
        game_version = await request.app.state.aio_redis_engine.hget(
            "modrinth", "game_versions"
        )
    return TrustableResponse(content=json.loads(game_version))


@v2_router.get(
    "/tag/donation_platform",
    description="Modrinth Donation Platform 信息",
    response_model=List,
)
@cache(expire=mcim_config.expire_second.modrinth.category)
async def modrinth_tag_donation_platforms(request: Request):
    donation_platform = await request.app.state.aio_redis_engine.hget(
        "modrinth", "donation_platform"
    )
    if donation_platform is None:
        await async_tags()
        log.debug("Donation Platform not found, sync.")
        donation_platform = await request.app.state.aio_redis_engine.hget(
            "modrinth", "donation_platform"
        )
    return TrustableResponse(content=json.loads(donation_platform))


@v2_router.get(
    "/tag/project_type",
    description="Modrinth Project Type 信息",
    response_model=List,
)
@cache(expire=mcim_config.expire_second.modrinth.category)
async def modrinth_tag_project_types(request: Request):
    project_type = await request.app.state.aio_redis_engine.hget(
        "modrinth", "project_type"
    )
    if project_type is None:
        await async_tags()
        log.debug("Project Type not found, sync.")
        project_type = await request.app.state.aio_redis_engine.hget(
            "modrinth", "project_type"
        )
    return TrustableResponse(content=json.loads(project_type))


@v2_router.get(
    "/tag/side_type",
    description="Modrinth Side Type 信息",
    response_model=List,
)
@cache(expire=mcim_config.expire_second.modrinth.category)
async def modrinth_tag_side_types(request: Request):
    side_type = await request.app.state.aio_redis_engine.hget("modrinth", "side_type")
    if side_type is None:
        await async_tags()
        log.debug("Side Type not found, sync.")
        side_type = await request.app.state.aio_redis_engine.hget(
            "modrinth", "side_type"
        )
    return TrustableResponse(content=json.loads(side_type))
