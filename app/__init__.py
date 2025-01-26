import os
import shutil
from fastapi import FastAPI
from fastapi.responses import RedirectResponse, ORJSONResponse, Response
from starlette.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from app.controller import controller_router
from app.utils.loger import log
from app.config import MCIMConfig
from app.database.mongodb import setup_async_mongodb, init_mongodb_aioengine
from app.database._redis import (
    init_redis_aioengine,
    close_aio_redis_engine,
    init_sync_queue_redis_engine,
    close_sync_queue_redis_engine,
)
from app.utils.response_cache import Cache
from app.utils.response_cache import cache
from app.utils.response import CurseforgeBaseResponse
from app.utils.middleware import ForceSyncMiddleware, TimingMiddleware, EtagMiddleware, CountTrustableMiddleware, UncachePOSTMiddleware
from app.utils.metric import init_prometheus_metrics

mcim_config = MCIMConfig.load()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.aio_redis_engine = init_redis_aioengine()
    init_sync_queue_redis_engine()
    await app.state.aio_redis_engine.flushall()
    app.state.aio_mongo_engine = init_mongodb_aioengine()
    await setup_async_mongodb(app.state.aio_mongo_engine)

    if mcim_config.redis_cache:
        app.state.fastapi_cache = Cache.init(enabled=True)

    yield

    await close_aio_redis_engine()
    await close_sync_queue_redis_engine()


APP = FastAPI(
    title="MCIM",
    description="这是一个为 Mod 信息加速的 API<br />你不应该直接浏览器中测试接口，有 UA 限制",
    lifespan=lifespan,
)

if mcim_config.prometheus:
    init_prometheus_metrics(APP)


APP.include_router(controller_router)

# Gzip 中间件
APP.add_middleware(GZipMiddleware, minimum_size=1000)

# 计时中间件
APP.add_middleware(TimingMiddleware)

# 强制同步中间件 force=True
# APP.add_middleware(ForceSyncMiddleware)

# # Etag 中间件
# APP.add_middleware(EtagMiddleware)

# 统计 Trustable 请求
APP.add_middleware(CountTrustableMiddleware)

# 不缓存 POST 请求
APP.add_middleware(UncachePOSTMiddleware)

# 跨域中间件
APP.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@APP.get("/favicon.ico")
@cache(never_expire=True)
async def favicon():
    return RedirectResponse(url=mcim_config.favicon_url, status_code=301)


WELCOME_MESSAGE = {
    "status": "success",
    "message": "mcimirror",
    "information": {
        "Status": "https://status.mcimirror.top",
        "Docs": [
            "https://mod.mcimirror.top/docs",
        ],
        "Github": "https://github.com/mcmod-info-mirror/mcim",
        "contact": {"Email": "z0z0r4@outlook.com", "QQ": "3531890582"},
    },
}


@APP.get(
    "/",
    responses={
        200: {
            "description": "MCIM API status",
            "content": {
                "APPlication/json": {
                    "example": WELCOME_MESSAGE,
                }
            },
        }
    },
    description="MCIM API",
)
@cache(never_expire=True)
async def root():
    return CurseforgeBaseResponse(content=WELCOME_MESSAGE)
