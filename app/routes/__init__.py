from fastapi import APIRouter, Depends
from typing import Optional
from odmantic import AIOEngine

from app.routes.modrinth import modrinth_router
from app.routes.curseforge import curseforge_router
from app.routes.file_cdn import file_cdn_router
from app.routes.translate import translate_router
from app.config import MCIMConfig
from app.database.mongodb import get_aio_mongodb_engine
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

root_router = APIRouter()
root_router.include_router(curseforge_router)
root_router.include_router(modrinth_router)
root_router.include_router(file_cdn_router)
root_router.include_router(translate_router)


@root_router.get(
    "/statistics", description="MCIM 缓存统计信息，每小时更新", include_in_schema=True
)
@cache(expire=3600)
async def mcim_statistics(
    modrinth: Optional[bool] = True,
    curseforge: Optional[bool] = True,
    file_cdn: Optional[bool] = True,
    aio_mongo_engine: AIOEngine = Depends(get_aio_mongodb_engine)
):
    """
    全部统计信息
    """

    result = {}

    if curseforge:
        curseforge_mod_collection = aio_mongo_engine.get_collection(
            CurseForgeMod
        )
        curseforge_file_collection = aio_mongo_engine.get_collection(
            CurseForgeFile
        )
        curseforge_fingerprint_collection = (
            aio_mongo_engine.get_collection(CurseForgeFingerprint)
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
        modrinth_project_collection = aio_mongo_engine.get_collection(
            ModrinthProject
        )
        modrinth_version_collection = aio_mongo_engine.get_collection(
            ModrinthVersion
        )
        modrinth_file_collection = aio_mongo_engine.get_collection(
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
        file_cdn_file_collection = aio_mongo_engine.get_collection(
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
        headers={"Cache-Control": "max-age=3600"},
    )
