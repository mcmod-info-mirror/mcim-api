from fastapi import APIRouter, Request, Query,Body
from typing import List, Optional


from app.models.database.translate import ModrinthTranslation, CurseForgeTranslation
from app.utils.response_cache import cache
from app.utils.response import (
    TrustableResponse,
    UncachedResponse,
)

translate_router = APIRouter(prefix="/translate", tags=["translate"])


@translate_router.get(
    "/modrinth",
    description="Modrinth 翻译",
    response_model=ModrinthTranslation,
)
@cache(expire=3600 * 24)
async def modrinth_translate(
    request: Request,
    project_id: str = Query(..., description="Modrinth Project id"),
):
    result: Optional[
        ModrinthTranslation
    ] = await request.app.state.aio_mongo_engine.find_one(
        ModrinthTranslation, ModrinthTranslation.project_id == project_id
    )

    if result:
        return TrustableResponse(content=result)
    else:
        return UncachedResponse()
    

@translate_router.post(
    "/modrinth",
    description="Modrinth 翻译(大量的时候)",
    response_model=ModrinthTranslation,
)
# @cache(expire=3600 * 24)
async def modrinth_translates(
    request: Request,
    project_ids: List[str] = Body(..., description="Modrinth Project ids"),
):
    results = []
    for project_id in project_ids:
        translation = await request.app.state.aio_mongo_engine.find_one(
        ModrinthTranslation, ModrinthTranslation.project_id == project_id
    )
        if translation:
            results.append(translation)
    result: Optional[
        ModrinthTranslation
    ] = results

    if result:
        return TrustableResponse(content=result)
    else:
        return UncachedResponse()


@translate_router.get(
    "/curseforge",
    description="CurseForge 翻译",
    response_model=CurseForgeTranslation,
)
@cache(expire=3600 * 24)
async def curseforge_translate(
    request: Request,
    modId: int = Query(..., description="CurseForge Mod id"),
):
    result: Optional[
        CurseForgeTranslation
    ] = await request.app.state.aio_mongo_engine.find_one(
        CurseForgeTranslation, CurseForgeTranslation.modId == modId
    )

    if result:
        return TrustableResponse(content=result)
    else:
        return UncachedResponse()
    
@translate_router.post(
    "/curseforge",
    description="CurseForge 翻译(大量的时候)",
    response_model=CurseForgeTranslation,
)
# @cache(expire=3600 * 24)
async def curseforge_translates(
    request: Request,
    modIds: List[int] = Body(..., description="CurseForge Mod ids"),
):
    results = []
    for modId in modIds:
        translation = await request.app.state.aio_mongo_engine.find_one(
        CurseForgeTranslation, CurseForgeTranslation.modId == modId
    )
        if translation:
            results.append(translation)
    result: Optional[
        CurseForgeTranslation
    ] = results
    if result:
        return TrustableResponse(content=result)
    else:
        return UncachedResponse()