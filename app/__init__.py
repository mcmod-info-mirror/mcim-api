from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.exception_handlers import (
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
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
from app.utils.response import BaseResponse
from app.utils.middleware import (
    TimingMiddleware,
    CountTrustableMiddleware,
    UncachePOSTMiddleware,
)
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
    # description="这是一个为 Mod 信息加速的 API<br />你不应该直接浏览器中测试接口，有 UA 限制",
    description="这是一个为 Mod 信息加速的 API",
    lifespan=lifespan,
)

if mcim_config.prometheus:
    init_prometheus_metrics(APP)


APP.include_router(controller_router)

# Gzip 中间件
APP.add_middleware(GZipMiddleware, minimum_size=1000)

# 计时中间件
APP.add_middleware(TimingMiddleware)

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


@APP.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Log the 422 error details, 分行输出避免 Request body 截断
    log.debug(f"Invalid request on {request.url} Detail: {exc}")
    log.debug(f"Invalid request on {request.url} Request body: {exc.body}")
    return await request_validation_exception_handler(request, exc)


@APP.get("/favicon.ico")
@cache(never_expire=True)
async def favicon():
    return RedirectResponse(url=mcim_config.favicon_url)


WELCOME_MESSAGE = {
    "status": "success",
    "message": "mcimirror",
    "information": {
        "Status": "https://status.mcimirror.top",
        "Docs": [
            "https://mod.mcimirror.top/docs",
        ],
        "Github": "https://github.com/mcmod-info-mirror",
        "contact": {"Email": "z0z0r4@outlook.com", "QQ": "3531890582"},
    },
}


@APP.get(
    "/",
    responses={
        200: {
            "description": "MCIM API",
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
    return BaseResponse(content=WELCOME_MESSAGE)
