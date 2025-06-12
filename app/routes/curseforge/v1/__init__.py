from fastapi import APIRouter, Depends, Response, Query
from typing import List, Optional, Annotated
from pydantic import BaseModel, Field
from odmantic import query, AIOEngine
from enum import Enum

from app.sync_queue.curseforge import (
    add_curseforge_modIds_to_queue,
    add_curseforge_fileIds_to_queue,
    add_curseforge_fingerprints_to_queue,
)
from app.models.database.curseforge import Mod, File, Fingerprint, Category
from app.models.response.curseforge import (
    _FingerprintResult,
    Pagination,
    SearchResponse,
    ModResponse,
    ModsResponse,
    ModFilesResponse,
    FileResponse,
    FilesResponse,
    DownloadUrlResponse,
    FingerprintResponse,
    CaregoriesResponse,
)
from app.config.mcim import MCIMConfig
from app.utils.response import TrustableResponse, UncachedResponse
from app.utils.network import request as request_async
from app.exceptions import ResponseCodeException
from app.utils.loger import log
from app.utils.response_cache import cache
from app.database.mongodb import get_aio_mongodb_engine

mcim_config = MCIMConfig.load()

API = mcim_config.curseforge_api

x_api_key = mcim_config.curseforge_api_key
HEADERS = {"x-api-key": x_api_key}

v1_router = APIRouter(prefix="/v1", tags=["curseforge"])

SEARCH_TIMEOUT = 3


class ModsSearchSortField(int, Enum):
    """
    https://docs.curseforge.com/rest-api/#tocS_ModsSearchSortField
    """

    Featured = 1
    Popularity = 2
    LastUpdated = 3
    Name = 4
    Author = 5
    TotalDownloads = 6
    Category = 7
    GameVersion = 8
    EarlyAccess = 9
    FeaturedReleased = 10
    ReleasedDate = 11
    Rating = 12


class ModLoaderType(int, Enum):
    """
    https://docs.curseforge.com/rest-api/#tocS_ModLoaderType
    """

    Any = 0
    Forge = 1
    Cauldron = 2
    LiteLoader = 3
    Fabric = 4
    Quilt = 5
    NeoForge = 6


class ModsSearchSortOrder(str, Enum):
    """
    'asc' if sort is in ascending order, 'desc' if sort is in descending order
    """

    ASC = "asc"
    DESC = "desc"


async def check_search_result(res: dict, aio_mongo_engine: AIOEngine):
    modids = set()
    for mod in res["data"]:
        # 排除小于 30000 的 modid
        if mod["id"] >= 30000:
            modids.add(mod["id"])

    # check if modids in db
    if modids:
        mod_models: List[Mod] = await aio_mongo_engine.find(
            Mod, query.in_(Mod.id, list(modids))
        )

        not_found_modids = modids - set([mod.id for mod in mod_models])

        if not_found_modids:
            await add_curseforge_modIds_to_queue(modIds=list(not_found_modids))
            log.debug(f"modIds: {not_found_modids} not found, add to queue.")
        else:
            log.debug("All Mods have been found.")
    else:
        log.debug("Search esult is empty")


@v1_router.get(
    "/mods/search",
    description="Curseforge Category 信息",
    response_model=SearchResponse,
)
@cache(expire=mcim_config.expire_second.curseforge.search)
async def curseforge_search(
    gameId: int = 432,
    classId: Optional[int] = None,
    categoryId: Optional[int] = None,
    categoryIds: Optional[str] = None,
    gameVersion: Optional[str] = None,
    gameVersions: Optional[str] = None,
    searchFilter: Optional[str] = None,
    sortField: Optional[ModsSearchSortField] = None,
    sortOrder: Optional[ModsSearchSortOrder] = None,
    modLoaderType: Optional[ModLoaderType] = None,
    modLoaderTypes: Optional[str] = None,
    gameVersionTypeId: Optional[int] = None,
    authorId: Optional[int] = None,
    primaryAuthorId: Optional[int] = None,
    slug: Optional[str] = None,
    index: Optional[int] = Query(
        le=10000,
        default=0,
        description="A zero based index of the first item to include in the response, the limit is: (index + pageSize <= 10,000).",
    ),
    pageSize: Optional[int] = Query(
        default=50,
        le=50,
        description="The number of items to include in the response, the default/maximum value is 50.",
    ),
    aio_mongo_engine: AIOEngine = Depends(get_aio_mongodb_engine),
):
    if index is not None and pageSize is not None and index + pageSize > 10000:
        return Response(
            status_code=400, content="The limit is: (index + pageSize <= 10,000)"
        )
    params = {
        "gameId": gameId,
        "classId": classId,
        "categoryId": categoryId,
        "categoryIds": categoryIds,
        "gameVersion": gameVersion,
        "gameVersions": gameVersions,
        "searchFilter": searchFilter,
        "sortField": sortField.value if sortField is not None else None,
        "sortOrder": sortOrder.value if sortOrder is not None else None,
        "modLoaderType": modLoaderType.value if modLoaderType is not None else None,
        "modLoaderTypes": modLoaderTypes,
        "gameVersionTypeId": gameVersionTypeId,
        "authorId": authorId,
        "primaryAuthorId": primaryAuthorId,
        "slug": slug,
        "index": index,
        "pageSize": pageSize,
    }
    try:
        res = (
            await request_async(
                f"{API}/v1/mods/search",
                params=params,
                headers=HEADERS,
                timeout=SEARCH_TIMEOUT,
            )
        ).json()
        await check_search_result(res=res, aio_mongo_engine=aio_mongo_engine)
        return TrustableResponse(content=SearchResponse(**res))
    except ResponseCodeException as e:
        if e.status_code == 400:
            return Response(
                status_code=400,
                content="The limit is: (index + pageSize <= 10,000)"
                if index + pageSize > 10000
                else "Bad Request",
            )
        raise e


@v1_router.get(
    "/mods/{modId}",
    description="Curseforge Mod 信息",
    response_model=ModResponse,
)
@cache(expire=mcim_config.expire_second.curseforge.mod)
async def curseforge_mod(
    modId: Annotated[int, Field(ge=30000, lt=9999999)], aio_mongo_engine: AIOEngine = Depends(get_aio_mongodb_engine)
):
    trustable: bool = True
    mod_model: Optional[Mod] = await aio_mongo_engine.find_one(
        Mod, Mod.id == modId
    )
    if mod_model is None:
        await add_curseforge_modIds_to_queue(modIds=[modId])
        log.debug(f"modId: {modId} not found, add to queue.")
        return UncachedResponse()
    return TrustableResponse(
        content=ModResponse(data=mod_model),
        trustable=trustable,
    )


class modIds_item(BaseModel):
    modIds: List[Annotated[int, Field(ge=30000, lt=9999999)]]
    filterPcOnly: Optional[bool] = True


@v1_router.post(
    "/mods",
    description="Curseforge Mods 信息",
    response_model=ModsResponse,
)
# @cache(expire=mcim_config.expire_second.curseforge.mod)
async def curseforge_mods(item: modIds_item, aio_mongo_engine: AIOEngine = Depends(get_aio_mongodb_engine)):
    trustable: bool = True
    mod_models: Optional[List[Mod]] = await aio_mongo_engine.find(
        Mod, query.in_(Mod.id, item.modIds)
    )
    mod_model_count = len(mod_models)
    item_count = len(item.modIds)
    if not mod_models:
        await add_curseforge_modIds_to_queue(modIds=item.modIds)
        log.debug(f"modIds: {item.modIds} not found, add to queue.")
        return TrustableResponse(
            content=ModsResponse(data=[]).model_dump(),
            trustable=False,
        )
    elif mod_model_count != item_count:
        # 找到不存在的 modid
        not_match_modids = list(set(item.modIds) - set([mod.id for mod in mod_models]))
        await add_curseforge_modIds_to_queue(modIds=not_match_modids)
        log.debug(
            f"modIds: {item.modIds} {mod_model_count}/{item_count} not found, add to queue."
        )
        trustable = False
    return TrustableResponse(
        content=ModsResponse(data=mod_models),
        trustable=trustable,
    )


def convert_modloadertype(type_id: int) -> Optional[str]:
    match type_id:
        case 1:
            return "Forge"
        case 2:
            return "Cauldron"
        case 3:
            return "LiteLoader"
        case 4:
            return "Fabric"
        case 5:
            return "Quilt"
        case 6:
            return "NeoForge"
        case _:
            return None


@v1_router.get(
    "/mods/{modId}/files",
    description="Curseforge Mod 文件信息",
    response_model=ModFilesResponse,
)
@cache(expire=mcim_config.expire_second.curseforge.file)
async def curseforge_mod_files(
    modId: Annotated[int, Field(gt=30000, lt=9999999)],
    gameVersion: Optional[str] = None,
    modLoaderType: Optional[int] = None,
    index: Optional[int] = 0,
    pageSize: Optional[
        int
    ] = 50,  # curseforge 官方的 limit 是摆设，启动器依赖此 bug 运行，不能设置 gt...
    aio_mongo_engine: AIOEngine = Depends(get_aio_mongodb_engine),
):
    # 定义聚合管道
    match_conditions = {"modId": modId}
    gameVersionFilter = []
    if gameVersion:
        gameVersionFilter.append(gameVersion)
    if modLoaderType:
        modLoaderType = convert_modloadertype(modLoaderType)
        if modLoaderType:
            gameVersionFilter.append(modLoaderType)
    if len(gameVersionFilter) != 0:
        match_conditions["gameVersions"] = {"$all": gameVersionFilter}

    pipeline = [
        {"$match": match_conditions},
        {
            "$facet": {
                "resultCount": [
                    {"$count": "count"},
                ],
                "totalCount": [
                    {"$match": {"modId": modId}},
                    {"$count": "count"},
                ],
                "documents": [
                    {"$skip": index if index else 0},
                    {"$limit": pageSize},
                ],
            }
        },
    ]

    # 执行聚合查询
    files_collection = aio_mongo_engine.get_collection(File)
    result = await files_collection.aggregate(pipeline).to_list(length=None)

    if not result or not result[0]["documents"]:
        await add_curseforge_modIds_to_queue(modIds=[modId])
        log.debug(f"modId: {modId} not found, add to queue.")
        return UncachedResponse()

    total_count = result[0]["totalCount"][0]["count"]
    result_count = result[0]["resultCount"][0]["count"]
    documents = result[0]["documents"]

    doc_results = []
    for doc in documents:
        _id = doc.pop("_id")
        doc["id"] = _id
        doc_results.append(doc)

    return TrustableResponse(
        content=ModFilesResponse(
            data=doc_results,
            pagination=Pagination(
                index=index,
                pageSize=pageSize,
                resultCount=result_count,
                totalCount=total_count,
            ),
        )
    )


class fileIds_item(BaseModel):
    fileIds: List[Annotated[int, Field(ge=530000, lt=99999999)]]


# get files
@v1_router.post(
    "/mods/files",
    description="Curseforge Mod 文件信息",
    response_model=FilesResponse,
)
# @cache(expire=mcim_config.expire_second.curseforge.file)
async def curseforge_files(item: fileIds_item, aio_mongo_engine: AIOEngine = Depends(get_aio_mongodb_engine)):
    trustable = True
    file_models: Optional[List[File]] = await aio_mongo_engine.find(
        File, query.in_(File.id, item.fileIds)
    )
    if not file_models:
        await add_curseforge_fileIds_to_queue(fileIds=item.fileIds)
        return UncachedResponse()
    elif len(file_models) != len(item.fileIds):
        # 找到不存在的 fileid
        not_match_fileids = list(
            set(item.fileIds) - set([file.id for file in file_models])
        )
        await add_curseforge_fileIds_to_queue(fileIds=not_match_fileids)
        trustable = False
    return TrustableResponse(
        content=FilesResponse(data=file_models),
        trustable=trustable,
    )


# get file
@v1_router.get(
    "/mods/{modId}/files/{fileId}",
    description="Curseforge Mod 文件信息",
    response_model=FileResponse,
)
@cache(expire=mcim_config.expire_second.curseforge.file)
async def curseforge_mod_file(
    modId: Annotated[int, Field(ge=30000, lt=9999999)],
    fileId: Annotated[int, Field(ge=530000, lt=99999999)],
    aio_mongo_engine: AIOEngine = Depends(get_aio_mongodb_engine),
):
    trustable = True
    model: Optional[File] = await aio_mongo_engine.find_one(
        File, File.modId == modId, File.id == fileId
    )
    if model is None:
        await add_curseforge_fileIds_to_queue(fileIds=[fileId])
        return UncachedResponse()
    return TrustableResponse(
        content=FileResponse(data=model),
        trustable=trustable,
    )


@v1_router.get(
    "/mods/{modId}/files/{fileId}/download-url",
    description="Curseforge Mod 文件下载地址",
    response_model=DownloadUrlResponse,
)
# @cache(expire=mcim_config.expire_second.curseforge.file)
async def curseforge_mod_file_download_url(
    modId: Annotated[int, Field(ge=30000, lt=9999999)],
    fileId: Annotated[int, Field(ge=530000, lt=99999999)],
    aio_mongo_engine: AIOEngine = Depends(get_aio_mongodb_engine),
):
    model: Optional[File] = await aio_mongo_engine.find_one(
        File, File.modId == modId, File.id == fileId
    )
    if (
        model is None or model.downloadUrl is None
    ):  # 有 134539+ 的文件没有 downloadCount
        await add_curseforge_fileIds_to_queue(fileIds=[fileId])
        return UncachedResponse()
    return TrustableResponse(
        content=DownloadUrlResponse(data=model.downloadUrl),
        trustable=True,
    )


class fingerprints_item(BaseModel):
    fingerprints: List[Annotated[int, Field(lt=99999999999)]]


@v1_router.post(
    "/fingerprints",
    description="Curseforge Fingerprint 文件信息",
    response_model=FingerprintResponse,
)
# @cache(expire=mcim_config.expire_second.curseforge.fingerprint)
async def curseforge_fingerprints(item: fingerprints_item, aio_mongo_engine: AIOEngine = Depends(get_aio_mongodb_engine)):
    trustable = True
    fingerprints_models: List[
        Fingerprint
    ] = await aio_mongo_engine.find(
        Fingerprint, query.in_(Fingerprint.id, item.fingerprints)
    )
    not_match_fingerprints = list(
        set(item.fingerprints)
        - set([fingerprint.id for fingerprint in fingerprints_models])
    )
    if not fingerprints_models:
        await add_curseforge_fingerprints_to_queue(fingerprints=item.fingerprints)
        trustable = False
        return TrustableResponse(
            content=FingerprintResponse(
                data=_FingerprintResult(unmatchedFingerprints=item.fingerprints)
            ),
            trustable=trustable,
        )
    elif len(fingerprints_models) != len(item.fingerprints):
        # 找到不存在的 fingerprint
        await add_curseforge_fingerprints_to_queue(fingerprints=not_match_fingerprints)
        trustable = False
    exactFingerprints = []
    result_fingerprints_models = []
    for fingerprint_model in fingerprints_models:
        # fingerprint_model.id = fingerprint_model.file.id
        # 神奇 primary_key 不能修改，没辙只能这样了
        fingerprint = fingerprint_model.model_dump()
        fingerprint["id"] = fingerprint_model.file.id
        result_fingerprints_models.append(fingerprint)
        exactFingerprints.append(fingerprint_model.id)
    return TrustableResponse(
        content=FingerprintResponse(
            data=_FingerprintResult(
                isCacheBuilt=True,
                exactFingerprints=exactFingerprints,
                exactMatches=result_fingerprints_models,
                unmatchedFingerprints=not_match_fingerprints,
                installedFingerprints=[],
            )
        ),
        trustable=trustable,
    )


@v1_router.post(
    "/fingerprints/432",
    description="Curseforge Fingerprint 文件信息",
    response_model=FingerprintResponse,
)
# @cache(expire=mcim_config.expire_second.curseforge.fingerprint)
async def curseforge_fingerprints_432(item: fingerprints_item, aio_mongo_engine: AIOEngine = Depends(get_aio_mongodb_engine)):
    trustable = True
    fingerprints_models: List[
        Fingerprint
    ] = await aio_mongo_engine.find(
        Fingerprint, query.in_(Fingerprint.id, item.fingerprints)
    )
    not_match_fingerprints = list(
        set(item.fingerprints)
        - set([fingerprint.id for fingerprint in fingerprints_models])
    )
    if not fingerprints_models:
        await add_curseforge_fingerprints_to_queue(fingerprints=item.fingerprints)
        trustable = False
        return TrustableResponse(
            content=FingerprintResponse(
                data=_FingerprintResult(unmatchedFingerprints=item.fingerprints)
            ),
            trustable=trustable,
        )
    elif len(fingerprints_models) != len(item.fingerprints):
        await add_curseforge_fingerprints_to_queue(fingerprints=not_match_fingerprints)
        trustable = False
    exactFingerprints = []
    result_fingerprints_models = []
    for fingerprint_model in fingerprints_models:
        # fingerprint_model.id = fingerprint_model.file.id
        # 神奇 primary_key 不能修改，没辙只能这样了
        fingerprint = fingerprint_model.model_dump()
        fingerprint["id"] = fingerprint_model.file.id
        result_fingerprints_models.append(fingerprint)
        exactFingerprints.append(fingerprint_model.id)
    return TrustableResponse(
        content=FingerprintResponse(
            data=_FingerprintResult(
                isCacheBuilt=True,
                exactFingerprints=exactFingerprints,
                exactMatches=result_fingerprints_models,
                unmatchedFingerprints=not_match_fingerprints,
                installedFingerprints=[],
            )
        ),
        trustable=trustable,
    )


@v1_router.get(
    "/categories",
    description="Curseforge Categories 信息",
    response_model=CaregoriesResponse,
)
@cache(expire=mcim_config.expire_second.curseforge.categories)
async def curseforge_categories(
    gameId: int,
    classId: Optional[int] = None,
    classOnly: Optional[bool] = None,
    aio_mongo_engine: AIOEngine = Depends(get_aio_mongodb_engine),
):
    if classId:
        categories: Optional[
            List[Category]
        ] = await aio_mongo_engine.find(
            Category,
            query.and_(Category.gameId == gameId, Category.classId == classId),
        )
    elif classOnly:
        categories: Optional[
            List[Category]
        ] = await aio_mongo_engine.find(
            Category, Category.gameId == gameId, Category.isClass == True
        )
    else:
        categories: Optional[
            List[Category]
        ] = await aio_mongo_engine.find(
            Category, Category.gameId == gameId
        )
    if not categories:
        return UncachedResponse()
    return TrustableResponse(
        content=CaregoriesResponse(data=categories),
        trustable=True,
    )
