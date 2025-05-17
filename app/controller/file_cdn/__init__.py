from fastapi import APIRouter, Request, Query
from fastapi.responses import RedirectResponse, Response
from odmantic import query
from typing import Optional
import time
import hashlib
from email.utils import formatdate

from app.models.database.curseforge import File as cfFile
from app.models.database.modrinth import File as mrFile
from app.models.database.file_cdn import File as cdnFile
from app.config import config_manager
from app.utils.loger import log
from app.utils.response_cache import cache
from app.utils.response import BaseResponse
from app.utils.network import ResponseCodeException
from app.utils.network import request as request_async

from app.sync_queue.curseforge import add_curseforge_fileIds_to_queue
from app.sync_queue.modrinth import add_modrinth_project_ids_to_queue
from app.utils.metric import (
    FILE_CDN_FORWARD_TO_ORIGIN_COUNT,
    FILE_CDN_FORWARD_TO_OPEN93HOME_COUNT,
)
from app.config.mcim import FileCDNRedirectMode

# expire 3h
file_cdn_router = APIRouter()

MAX_AGE = int(60 * 60 * 2.5)

CDN_MAX_AGE = int(60 * 60 * 2.8)

# 这个根本不需要更新，是 sha1 https://files.mcimirror.top/files/mcim/8e7b73b39c0bdae84a4be445027747c9bae935c4
_93ATHOME_MAX_AGE = int(60 * 60 * 24 * 7)

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
    if secret != config_manager.mcim_config.file_cdn_secret:
        return False
    return True


@file_cdn_router.get("/file_cdn/statistics", include_in_schema=False)
async def file_cdn_statistics(request: Request):
    cdnFile_collection = request.app.state.aio_mongo_engine.get_collection(cdnFile)
    cdnFile_count = await cdnFile_collection.aggregate(
        [{"$collStats": {"count": {}}}]
    ).to_list(length=None)
    return BaseResponse(content={"file_cdn_files": cdnFile_count[0]["count"]})


# modrinth | example: https://cdn.modrinth.com/data/AANobbMI/versions/IZskON6d/sodium-fabric-0.5.8%2Bmc1.20.6.jar
# WARNING: 直接查 version_id 忽略 project_id
# WARNING: 必须文件名一致
@file_cdn_router.get(
    "/data/{project_id}/versions/{version_id}/{file_name}", tags=["modrinth"]
)
@cache(
    expire=(
        _93ATHOME_MAX_AGE
        if config_manager.mcim_config.file_cdn_redirect_mode == FileCDNRedirectMode.ORIGIN
        else MAX_AGE
    )
)
async def get_modrinth_file(
    project_id: str, version_id: str, file_name: str, request: Request
):
    def get_origin_response(project_id: str, version_id: str, file_name: str) -> RedirectResponse:
        url = f"https://cdn.modrinth.com/data/{project_id}/versions/{version_id}/{file_name}"
        FILE_CDN_FORWARD_TO_ORIGIN_COUNT.labels("modrinth").inc()
        return RedirectResponse(
            url=url,
            headers={"Cache-Control": f"public, age={3600 * 24 * 1}"},
            status_code=302,
        )

    def get_open93home_response(
        sha1: str
    ) -> Optional[RedirectResponse]:
        # 重新检查 cdnFile
        # file_cdn_model: Optional[cdnFile] = (
        #     await request.app.state.aio_mongo_engine.find_one(
        #         cdnFile, cdnFile.sha1 == sha1
        #     )
        # )
        # if file_cdn_model:
        #     return RedirectResponse(
        #         url=f"{config_manager.mcim_config.open93home_endpoint}/{file_cdn_model.path}",
        #         headers={"Cache-Control": f"public, age={3600*24*7}"},
        #         status_code=301,
        #     )

        # 信任 file_cdn_cached 则不再检查
        # 在调用该函数之前应该已经检查过 file_cdn_cached 为 True
        return RedirectResponse(
            # url=f"{config_manager.mcim_config.open93home_endpoint}/{file_cdn_model.path}",
            url=f"{config_manager.mcim_config.open93home_endpoint}/{sha1}",  # file_cdn_model.path 实际上是 sha1
            headers={"Cache-Control": f"public, age={3600 * 24 * 7}"},
            status_code=301,
        )

    def get_pysio_response(
        project_id: str, version_id: str, file_name: str
    ) -> RedirectResponse:
        url = f"https://{config_manager.mcim_config.pysio_endpoint}/data/{project_id}/versions/{version_id}/{file_name}"
        return RedirectResponse(
            url=url,
            headers={"Cache-Control": f"public, age={3600 * 24 * 1}"},
            status_code=302,
        )

    if not config_manager.mcim_config.file_cdn:
        return get_origin_response(project_id=project_id, version_id=version_id, file_name=file_name)
    elif config_manager.mcim_config.file_cdn_redirect_mode == FileCDNRedirectMode.PYSIO:
        # Note: Pysio 表示无需筛选，所以直接跳过 file 检索
        pysio_response = get_pysio_response(project_id=project_id, version_id=version_id, file_name=file_name)
        return pysio_response

    file: Optional[mrFile] = await request.app.state.aio_mongo_engine.find_one(
        mrFile,
        query.and_(
            mrFile.project_id == project_id,
            mrFile.version_id == version_id,
            mrFile.filename == file_name,
        ),
    )
    if file:
        if file.size <= config_manager.mcim_config.max_file_size and file.file_cdn_cached:  # 检查 file_cdn_cached
            sha1 = file.hashes.sha1
            if config_manager.mcim_config.file_cdn_redirect_mode == FileCDNRedirectMode.OPEN93HOME:
                open93home_response = get_open93home_response(sha1)
                if open93home_response:
                    FILE_CDN_FORWARD_TO_OPEN93HOME_COUNT.labels("modrinth").inc()
                    return open93home_response
                else:
                    log.warning(f"Open93Home not found {sha1}")
                    return get_origin_response(project_id=project_id, version_id=version_id, file_name=file_name)
            else:  # config_manager.mcim_config.file_cdn_redirect_mode == FileCDNRedirectMode.ORIGIN: # default
                return get_origin_response(project_id=project_id, version_id=version_id, file_name=file_name)
    else:
        # 文件信息不存在
        await add_modrinth_project_ids_to_queue(project_ids=[project_id])
        log.debug(f"Project {project_id} add to queue.")

    return get_origin_response(project_id=project_id, version_id=version_id, file_name=file_name)


# curseforge | example: https://edge.forgecdn.net/files/3040/523/jei_1.12.2-4.16.1.301.jar
@file_cdn_router.get("/files/{fileid1}/{fileid2}/{file_name}", tags=["curseforge"])
@cache(
    expire=(
        _93ATHOME_MAX_AGE
        if config_manager.mcim_config.file_cdn_redirect_mode == FileCDNRedirectMode.ORIGIN
        else MAX_AGE
    )
)
async def get_curseforge_file(
    fileid1: int, fileid2: int, file_name: str, request: Request
) -> RedirectResponse:
    def get_origin_response(fileId1: int, fileId2: int, file_name: str) -> RedirectResponse:
        url = f"https://edge.forgecdn.net/files/{fileId1}/{fileId2}/{file_name}"
        FILE_CDN_FORWARD_TO_ORIGIN_COUNT.labels("curseforge").inc()
        return RedirectResponse(
            url=url,
            headers={"Cache-Control": f"public, age={3600 * 24 * 7}"},
            status_code=302,
        )

    def get_open93home_response(
        sha1: str
    ) -> RedirectResponse:
        # 信任 file_cdn_cached 则不再检查
        # 在调用该函数之前应该已经检查过 file_cdn_cached 为 True
        return RedirectResponse(
            # url=f"{config_manager.mcim_config.open93home_endpoint}/{file_cdn_model.path}",
            url=f"{config_manager.mcim_config.open93home_endpoint}/{sha1}",  # file_cdn_model.path 实际上是 sha1
            headers={"Cache-Control": f"public, age={3600 * 24 * 7}"},
            status_code=301,
        )

    def get_pysio_response(
        fileId1: int, fileId2: int, file_name: str
    ) -> RedirectResponse:
        # TODO:暂时不做进一步筛选
        return RedirectResponse(
            url=f"{config_manager.mcim_config.pysio_endpoint}/files/{fileId1}/{fileId2}/{file_name}",
            headers={"Cache-Control": f"public, age={3600 * 24 * 7}"},
            status_code=301,
        )

    if not config_manager.mcim_config.file_cdn:
        origin_response: RedirectResponse = get_origin_response(fileId1=fileid1, fileId2=fileid2, file_name=file_name)
        return origin_response
    elif config_manager.mcim_config.file_cdn_redirect_mode == FileCDNRedirectMode.PYSIO:
        # Note: Pysio 表示无需筛选，所以直接跳过 file 检索
        pysio_response = get_pysio_response(fileId1=fileid1, fileId2=fileid2, file_name=file_name)
        return pysio_response

    fileid = int(f"{fileid1}{fileid2}")

    file: Optional[cfFile] = await request.app.state.aio_mongo_engine.find_one(
        cfFile,
        query.and_(cfFile.id == fileid, cfFile.fileName == file_name),
    )

    if file:  # 数据库中有文件
        if file.fileLength <= config_manager.mcim_config.max_file_size and file.file_cdn_cached:
            sha1 = (
                file.hashes[0].value
                if file.hashes[0].algo == 1
                else file.hashes[1].value
            )

            if config_manager.mcim_config.file_cdn_redirect_mode == FileCDNRedirectMode.OPEN93HOME:
                open93home_response = get_open93home_response(sha1, request)
                if open93home_response:
                    FILE_CDN_FORWARD_TO_OPEN93HOME_COUNT.labels("curseforge").inc()
                    return open93home_response
                else:
                    log.warning(f"Open93Home not found {sha1}")
                    return get_origin_response(fileId1=fileid1, fileId2=fileid2, file_name=file_name)
            else:  # config_manager.mcim_config.file_cdn_redirect_mode == FileCDNRedirectMode.ORIGIN:
                return get_origin_response(fileId1=fileid1, fileId2=fileid2, file_name=file_name)

        else:
            log.trace(f"File {fileid} is too large, {file.fileLength} > {config_manager.mcim_config.max_file_size}")
    else:
        if fileid >= 530000:
            await add_curseforge_fileIds_to_queue(fileIds=[fileid])
            log.debug(f"FileId {fileid} add to queue.")

    return get_origin_response(fileId1=fileid1, fileId2=fileid2, file_name=file_name)


# @file_cdn_router.get("/file_cdn/list", include_in_schema=False)
# async def list_file_cdn(
#     request: Request,
#     secret: str,
#     last_id: Optional[str] = None,
#     last_modified: Optional[int] = None,
#     page_size: int = Query(
#         default=1000,
#         le=10000,
#     ),
# ):
#     if not config_manager.mcim_config.file_cdn or not config_manager.mcim_config.file_cdn_redirect_mode == FileCDNRedirectMode.OPEN93HOME or not file_cdn_check_secret(secret):
#         return Response(
#             status_code=403, content="Forbidden", headers={"Cache-Control": "no-cache"}
#         )

#     files_collection = request.app.state.aio_mongo_engine.get_collection(cdnFile)

#     # 动态构建 $match 阶段
#     match_stage = {}
#     if last_modified:
#         match_stage["mtime"] = {"$gt": last_modified}
#     if last_id:
#         match_stage["_id"] = {"$gt": last_id}
#     match_stage["disable"] = {"$ne": True}

#     # 聚合管道
#     pipeline = [{"$match": match_stage}, {"$sort": {"_id": 1}}, {"$limit": page_size}]

#     results = await files_collection.aggregate(pipeline).to_list(length=None)
#     return BaseResponse(content=results)


# async def check_file_hash_and_size(url: str, hash: str, size: int):
#     sha1 = hashlib.sha1()
#     try:
#         resp = await request_async(method="GET", url=url, follow_redirects=True)
#         if (
#             int(resp.headers["content-length"]) != size
#         ):  # check size | exapmple a5fb8e2a37f1772312e2c75af2866132ebf97e4f
#             log.warning(
#                 f"Reported size: {size}, calculated size: {resp.headers['content-length']}"
#             )
#             return False
#         sha1.update(resp.content)
#         log.warning(f"Reported hash: {hash}, calculated hash: {sha1.hexdigest()}")
#         return sha1.hexdigest() == hash
#     except ResponseCodeException:
#         return False


# @file_cdn_router.get("/file_cdn/report", include_in_schema=False)
# async def report(
#     request: Request,
#     secret: str,
#     _hash: str = Query(alias="hash"),
# ):
#     if not config_manager.mcim_config.file_cdn or not config_manager.mcim_config.file_cdn_redirect_mode == FileCDNRedirectMode.OPEN93HOME or not file_cdn_check_secret(secret):
#         return Response(
#             status_code=403, content="Forbidden", headers={"Cache-Control": "no-cache"}
#         )
# async def check_file_hash_and_size(url: str, hash: str, size: int):
#     sha1 = hashlib.sha1()
#     try:
#         resp = await request_async(method="GET", url=url, follow_redirects=True)
#         if (
#             int(resp.headers["content-length"]) != size
#         ):  # check size | exapmple a5fb8e2a37f1772312e2c75af2866132ebf97e4f
#             log.warning(
#                 f"Reported size: {size}, calculated size: {resp.headers['content-length']}"
#             )
#             return False
#         sha1.update(resp.content)
#         log.warning(f"Reported hash: {hash}, calculated hash: {sha1.hexdigest()}")
#         return sha1.hexdigest() == hash
#     except ResponseCodeException:
#         return False


# @file_cdn_router.get("/file_cdn/report", include_in_schema=False)
# async def report(
#     request: Request,
#     secret: str,
#     _hash: str = Query(alias="hash"),
# ):
#     if not config_manager.mcim_config.file_cdn or not config_manager.mcim_config.file_cdn_redirect_mode == FileCDNRedirectMode.OPEN93HOME or not file_cdn_check_secret(secret):
#         return Response(
#             status_code=403, content="Forbidden", headers={"Cache-Control": "no-cache"}
#         )

#     file: Optional[cdnFile] = await request.app.state.aio_mongo_engine.find_one(
#         cdnFile, cdnFile.sha1 == _hash
#     )

#     if file:
#         check_result = await check_file_hash_and_size(
#             url=file.url, hash=_hash, size=file.size
#         )
#         cdnFile_collection = request.app.state.aio_mongo_engine.get_collection(cdnFile)
#         if check_result:
#             await cdnFile_collection.update_one(
#                 {"_id": file.sha1}, {"$set": {"disable": False}}
#             )
#             return BaseResponse(
#                 status_code=500,
#                 content={
#                     "code": 500,
#                     "message": "Hash and size match successfully, file is correct",
#                 },
#                 headers={"Cache-Control": "no-cache"},
#             )
#         else:
#             await cdnFile_collection.update_one(
#                 {"_id": file.sha1}, {"$set": {"disable": True}}
#             )
#             return BaseResponse(
#                 status_code=200,
#                 content={
#                     "code": 200,
#                     "message": "Hash or size not match, file is disabled",
#                 },
#                 headers={"Cache-Control": "no-cache"},
#             )
#     else:
#         return BaseResponse(
#             status_code=404,
#             content={"code": 404, "message": "File not found"},
#             headers={"Cache-Control": "no-cache"},
#         )
