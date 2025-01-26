from fastapi import APIRouter, Request, Query
from fastapi.responses import RedirectResponse, JSONResponse
from odmantic import query
from typing import Optional
import time
import hashlib
from email.utils import formatdate

from app.models.database.curseforge import File as cfFile
from app.models.database.modrinth import File as mrFile
from app.models.database.file_cdn import File as cdnFile
from app.config import MCIMConfig
from app.utils.loger import log
from app.utils.response_cache import cache
from app.utils.response import CurseforgeBaseResponse
from app.utils.network import ResponseCodeException
from app.utils.network import request as request_async

from app.sync_queue.curseforge import add_curseforge_fileIds_to_queue
from app.sync_queue.modrinth import add_modrinth_project_ids_to_queue
from app.utils.metric import (
    FILE_CDN_FORWARD_TO_ORIGIN_COUNT,
    FILE_CDN_FORWARD_TO_OPEN93HOME_COUNT,
)
from app.config.mcim import FileCDNRedirectMode


mcim_config = MCIMConfig.load()

# expire 3h
file_cdn_router = APIRouter()

FILE_CDN_REDIRECT_MODE = mcim_config.file_cdn_redirect_mode

MAX_AGE = int(60 * 60 * 2.5)

CDN_MAX_AGE = int(60 * 60 * 2.8)

# 这个根本不需要更新，是 sha1 https://files.mcimirror.top/files/mcim/8e7b73b39c0bdae84a4be445027747c9bae935c4
_93ATHOME_MAX_AGE = int(60 * 60 * 24 * 7)

# 缓存文件大小限制
MAX_LENGTH = mcim_config.max_file_size

TIMEOUT = 2.5


def get_http_date(delay: int = CDN_MAX_AGE):
    """
    Get the current timestamp
    """
    timestamp = time.time()
    timestamp += delay

    # Convert the timestamp to an HTTP date
    http_date = formatdate(timestamp, usegmt=True)
    return http_date


def file_cdn_check_secret(secret: str):
    if secret != mcim_config.file_cdn_secret:
        return False
    return True


@file_cdn_router.get("/file_cdn/statistics", include_in_schema=False)
async def file_cdn_statistics(request: Request):
    cdnFile_collection = request.app.state.aio_mongo_engine.get_collection(cdnFile)
    cdnFile_count = await cdnFile_collection.aggregate(
        [{"$collStats": {"count": {}}}]
    ).to_list(length=None)
    return CurseforgeBaseResponse(content={"file_cdn_files": cdnFile_count[0]["count"]})


if mcim_config.file_cdn:
    # modrinth | example: https://cdn.modrinth.com/data/AANobbMI/versions/IZskON6d/sodium-fabric-0.5.8%2Bmc1.20.6.jar
    # WARNING: 直接查 version_id 忽略 project_id
    # WARNING: 必须文件名一致
    @file_cdn_router.get(
        "/data/{project_id}/versions/{version_id}/{file_name}", tags=["modrinth"]
    )
    @cache(
        expire=(
            _93ATHOME_MAX_AGE
            if FILE_CDN_REDIRECT_MODE == FileCDNRedirectMode.ORIGIN
            else MAX_AGE
        )
    )
    async def get_modrinth_file(
        project_id: str, version_id: str, file_name: str, request: Request
    ):
        def return_origin_response():
            url = f"https://cdn.modrinth.com/data/{project_id}/versions/{version_id}/{file_name}"
            FILE_CDN_FORWARD_TO_ORIGIN_COUNT.labels("modrinth").inc()
            return RedirectResponse(
                url=url,
                headers={"Cache-Control": f"public, age={3600*24*1}"},
                status_code=302,
            )

        async def return_open93home_response(sha1: str, request: Request):
            file_cdn_model: Optional[cdnFile] = (
                await request.app.state.aio_mongo_engine.find_one(
                    cdnFile, cdnFile.sha1 == sha1
                )
            )
            if file_cdn_model:
                return RedirectResponse(
                    url=f"{mcim_config.open93home_endpoint}/{file_cdn_model.path}",
                    headers={"Cache-Control": f"public, age={3600*24*7}"},
                    status_code=301,
                )

        file: Optional[mrFile] = await request.app.state.aio_mongo_engine.find_one(
            mrFile,
            query.and_(
                mrFile.project_id == project_id,
                mrFile.version_id == version_id,
                mrFile.filename == file_name,
            ),
        )
        if file:
            if file.size <= MAX_LENGTH:
                sha1 = file.hashes.sha1
                if FILE_CDN_REDIRECT_MODE == FileCDNRedirectMode.OPEN93HOME:
                    open93home_response = await return_open93home_response(
                        sha1, request
                    )
                    if open93home_response:
                        FILE_CDN_FORWARD_TO_OPEN93HOME_COUNT.labels("modrinth").inc()
                        return open93home_response
                    else:
                        log.warning(f"Open93Home not found {sha1}")
                        return return_origin_response()
                else:  # FILE_CDN_REDIRECT_MODE == FileCDNRedirectMode.ORIGIN: # default
                    return return_origin_response()
        else:
            # 文件信息不存在
            await add_modrinth_project_ids_to_queue(project_ids=[project_id])
            log.debug(f"Project {project_id} add to queue.")

        return return_origin_response()

    # curseforge | example: https://edge.forgecdn.net/files/3040/523/jei_1.12.2-4.16.1.301.jar
    @file_cdn_router.get("/files/{fileid1}/{fileid2}/{file_name}", tags=["curseforge"])
    @cache(
        expire=(
            _93ATHOME_MAX_AGE
            if FILE_CDN_REDIRECT_MODE == FileCDNRedirectMode.ORIGIN
            else MAX_AGE
        )
    )
    async def get_curseforge_file(
        fileid1: int, fileid2: int, file_name: str, request: Request
    ):
        def return_origin_response():
            url = f"https://edge.forgecdn.net/files/{fileid1}/{fileid2}/{file_name}"
            FILE_CDN_FORWARD_TO_ORIGIN_COUNT.labels("curseforge").inc()
            return RedirectResponse(
                url=url,
                headers={"Cache-Control": f"public, age={3600*24*7}"},
                status_code=302,
            )

        async def return_open93home_response(sha1: str, request: Request):
            file_cdn_model: Optional[cdnFile] = (
                await request.app.state.aio_mongo_engine.find_one(
                    cdnFile, cdnFile.sha1 == sha1
                )
            )
            if file_cdn_model:
                return RedirectResponse(
                    url=f"{mcim_config.open93home_endpoint}/{file_cdn_model.path}",
                    headers={"Cache-Control": f"public, age={3600*24*7}"},
                    status_code=301,
                )

        fileid = int(f"{fileid1}{fileid2}")
        file: Optional[cfFile] = await request.app.state.aio_mongo_engine.find_one(
            cfFile,
            query.and_(
                cfFile.id == fileid, cfFile.fileName == file_name
            ),
        )
        if file:  # 数据库中有文件
            if file.fileLength <= MAX_LENGTH:
                sha1 = (
                    file.hashes[0].value
                    if file.hashes[0].algo == 1
                    else file.hashes[1].value
                )

                if FILE_CDN_REDIRECT_MODE == FileCDNRedirectMode.OPEN93HOME:
                    open93home_response = await return_open93home_response(
                        sha1, request
                    )
                    if open93home_response:
                        FILE_CDN_FORWARD_TO_OPEN93HOME_COUNT.labels("curseforge").inc()
                        return open93home_response
                    else:
                        log.warning(f"Open93Home not found {sha1}")
                        return return_origin_response()
                else:  # FILE_CDN_REDIRECT_MODE == FileCDNRedirectMode.ORIGIN:
                    return return_origin_response()
            else:
                log.debug(
                    f"File {fileid} is too large, {file.fileLength} > {MAX_LENGTH}"
                )
        else:
            if fileid >= 530000:
                await add_curseforge_fileIds_to_queue(fileIds=[fileid])
                log.debug(f"FileId {fileid} add to queue.")

        return return_origin_response()


@file_cdn_router.get("/file_cdn/list", include_in_schema=False)
async def list_file_cdn(
    request: Request,
    secret: str,
    last_id: Optional[str] = None,
    last_modified: Optional[int] = None,
    page_size: int = Query(
        default=1000,
        le=10000,
    ),
):
    if not file_cdn_check_secret(secret):
        return JSONResponse(
            status_code=403, content="Forbidden", headers={"Cache-Control": "no-cache"}
        )
    files_collection = request.app.state.aio_mongo_engine.get_collection(cdnFile)
    
    # 动态构建 $match 阶段
    match_stage = {}
    if last_modified:
        match_stage["mtime"] = {"$gt": last_modified}
    if last_id:
        match_stage["_id"] = {"$gt": last_id}
    match_stage["disable"] = {"$ne": True}

    # 聚合管道
    pipeline = [{"$match": match_stage}, {"$sort": {"_id": 1}}, {"$limit": page_size}]

    results = await files_collection.aggregate(pipeline).to_list(length=None)
    return CurseforgeBaseResponse(content=results)


async def check_file_hash_and_size(url: str, hash: str, size: int):
    sha1 = hashlib.sha1()
    try:
        resp = await request_async(method="GET", url=url, follow_redirects=True)
        if (
            int(resp.headers["content-length"]) != size
        ):  # check size | exapmple a5fb8e2a37f1772312e2c75af2866132ebf97e4f
            log.warning(
                f'Reported size: {size}, calculated size: {resp.headers["content-length"]}'
            )
            return False
        sha1.update(resp.content)
        log.warning(f"Reported hash: {hash}, calculated hash: {sha1.hexdigest()}")
        return sha1.hexdigest() == hash
    except ResponseCodeException as e:
        return False


@file_cdn_router.get("/file_cdn/report", include_in_schema=False)
async def report(
    request: Request,
    secret: str,
    _hash: str = Query(alias="hash"),
):
    if not file_cdn_check_secret(secret):
        return JSONResponse(
            status_code=403, content="Forbidden", headers={"Cache-Control": "no-cache"}
        )

    file: Optional[cdnFile] = await request.app.state.aio_mongo_engine.find_one(
        cdnFile, cdnFile.sha1 == _hash
    )

    if file:
        check_result = await check_file_hash_and_size(
            url=file.url, hash=_hash, size=file.size
        )
        cdnFile_collection = request.app.state.aio_mongo_engine.get_collection(
            cdnFile
        )
        if check_result:
            await cdnFile_collection.update_one(
                {"_id": file.sha1}, {"$set": {"disable": False}}
            )
            return CurseforgeBaseResponse(
                status_code=500,
                content={
                    "code": 500,
                    "message": "Hash and size match successfully, file is correct",
                },
                headers={"Cache-Control": "no-cache"},
            )
        else:
            await cdnFile_collection.update_one(
                {"_id": file.sha1}, {"$set": {"disable": True}}
            )
            return CurseforgeBaseResponse(
                status_code=200,
                content={
                    "code": 200,
                    "message": "Hash or size not match, file is disabled",
                },
                headers={"Cache-Control": "no-cache"},
            )
    else:
        return CurseforgeBaseResponse(
            status_code=404,
            content={"code": 404, "message": "File not found"},
            headers={"Cache-Control": "no-cache"},
        )
