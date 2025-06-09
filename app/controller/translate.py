from fastapi import APIRouter, Request, Query, Path, Body
from typing import List, Optional, Annotated
from pydantic import BaseModel, Field
from odmantic import query


from app.models.database.translate import ModrinthTranslation, CurseForgeTranslation
from app.utils.response_cache import cache
from app.utils.response import (
    TrustableResponse,
    UncachedResponse,
)

translate_router = APIRouter(prefix="/translate", tags=["translate"])


class CurseForgeBatchRequest(BaseModel):
    modIds: Annotated[List[int], Field(min_length=1, max_length=1000)]


class ModrinthBatchRequest(BaseModel):
    project_ids: Annotated[List[str], Field(min_length=1, max_length=1000)]


@translate_router.get(
    "/modrinth/{project_id}",
    description="Modrinth 翻译",
    response_model=ModrinthTranslation,
)
@cache(expire=3600 * 24)
async def modrinth_translate_path(
    request: Request,
    project_id: str = Path(..., description="Modrinth Project id"),
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
    description="批量 Modrinth 翻译",
    response_model=List[ModrinthTranslation],
)
async def modrinth_translate_batch(
    request: Request,
    project_ids: ModrinthBatchRequest = Body(..., description="Modrinth Project ids"),
):
    results: List[ModrinthTranslation] = await request.app.state.aio_mongo_engine.find(
        ModrinthTranslation,
        query.in_(ModrinthTranslation.project_id, project_ids.project_ids),
    )

    if results:
        return TrustableResponse(content=results)
    else:
        return UncachedResponse()


@translate_router.get(
    "/curseforge/{modId}",
    description="CurseForge 翻译",
    response_model=CurseForgeTranslation,
)
@cache(expire=3600 * 24)
async def curseforge_translate_path(
    request: Request,
    modId: int = Path(..., description="CurseForge Mod id"),
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
    description="批量 CurseForge 翻译",
    response_model=List[CurseForgeTranslation],
)
async def curseforge_translate_batch(
    request: Request,
    modIds: CurseForgeBatchRequest = Body(..., description="CurseForge Mod ids"),
):
    results: List[
        CurseForgeTranslation
    ] = await request.app.state.aio_mongo_engine.find(
        CurseForgeTranslation, query.in_(CurseForgeTranslation.modId, modIds.modIds)
    )

    if results:
        return TrustableResponse(content=results)
    else:
        return UncachedResponse()


@translate_router.get(
    "/modrinth",
    description="Modrinth 翻译",
    response_model=ModrinthTranslation,
    deprecated=True,
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


@translate_router.get(
    "/curseforge",
    description="CurseForge 翻译",
    response_model=CurseForgeTranslation,
    deprecated=True,
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
