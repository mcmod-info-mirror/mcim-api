from fastapi import APIRouter, Request
from typing import Optional
from app.controller.modrinth import modrinth_router
from app.controller.curseforge import curseforge_router
from app.controller.file_cdn import file_cdn_router
from app.config import MCIMConfig
from app.utils.loger import log
from app.models.database.modrinth import (
    Project as ModrinthProject,
    Version as ModrinthVersion,
    File as ModrinthFile,
)
from app.models.database.curseforge import (
    Mod as CurseForgeMod,
    File as CurseForgeFile,
    Fingerprint as CurseForgeFingerprint,
)
from app.models.database.file_cdn import File as FileCDNFile
from app.utils.response import BaseResponse
from app.utils.response_cache import cache

mcim_config = MCIMConfig.load()

controller_router = APIRouter()
controller_router.include_router(curseforge_router)
controller_router.include_router(modrinth_router)
controller_router.include_router(file_cdn_router)


@controller_router.get(
    "/statistics", description="MCIM 缓存统计信息，每小时更新", include_in_schema=True
)
@cache(expire=3600)
async def mcim_statistics(
    request: Request,
    modrinth: Optional[bool] = True,
    curseforge: Optional[bool] = True,
    file_cdn: Optional[bool] = True,
):
    """
    全部统计信息
    """

    result = {}

    if curseforge:
        curseforge_mod_collection = request.app.state.aio_mongo_engine.get_collection(
            CurseForgeMod
        )
        curseforge_file_collection = request.app.state.aio_mongo_engine.get_collection(
            CurseForgeFile
        )
        curseforge_fingerprint_collection = (
            request.app.state.aio_mongo_engine.get_collection(CurseForgeFingerprint)
        )

        curseforge_mod_count = await curseforge_mod_collection.aggregate(
            [{"$collStats": {"count": {}}}]
        ).to_list(length=None)
        curseforge_file_count = await curseforge_file_collection.aggregate(
            [{"$collStats": {"count": {}}}]
        ).to_list(length=None)
        curseforge_fingerprint_count = (
            await curseforge_fingerprint_collection.aggregate(
                [{"$collStats": {"count": {}}}]
            ).to_list(length=None)
        )

        result["curseforge"] = {
            "mod": curseforge_mod_count[0]["count"],
            "file": curseforge_file_count[0]["count"],
            "fingerprint": curseforge_fingerprint_count[0]["count"],
        }

    if modrinth:
        modrinth_project_collection = request.app.state.aio_mongo_engine.get_collection(
            ModrinthProject
        )
        modrinth_version_collection = request.app.state.aio_mongo_engine.get_collection(
            ModrinthVersion
        )
        modrinth_file_collection = request.app.state.aio_mongo_engine.get_collection(
            ModrinthFile
        )

        modrinth_project_count = await modrinth_project_collection.aggregate(
            [{"$collStats": {"count": {}}}]
        ).to_list(length=None)
        modrinth_version_count = await modrinth_version_collection.aggregate(
            [{"$collStats": {"count": {}}}]
        ).to_list(length=None)
        modrinth_file_count = await modrinth_file_collection.aggregate(
            [{"$collStats": {"count": {}}}]
        ).to_list(length=None)

        result["modrinth"] = {
            "project": modrinth_project_count[0]["count"],
            "version": modrinth_version_count[0]["count"],
            "file": modrinth_file_count[0]["count"],
        }

    if file_cdn and mcim_config.file_cdn:
        file_cdn_file_collection = request.app.state.aio_mongo_engine.get_collection(
            FileCDNFile
        )

        file_cdn_file_count = await file_cdn_file_collection.aggregate(
            [{"$collStats": {"count": {}}}]
        ).to_list(length=None)

        result["file_cdn"] = {
            "file": file_cdn_file_count[0]["count"],
        }
    
    return BaseResponse(
        content=result,
        headers={"Cache-Control": f"max-age=3600"},
    )
