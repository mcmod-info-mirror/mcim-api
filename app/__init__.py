from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from starlette.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from app.controller import controller_router
from app.utils.loger import log
from app.config.config_manager import config_manager
from app.config.constants import (
    MICM_CONFIG_PATH,
    MONGODB_CONFIG_PATH,
    REDIS_CONFIG_PATH,
)
from app.database.mongodb import setup_async_mongodb, init_mongodb_aioengine
from app.database._redis import (
    init_redis_aioengine,
    close_aio_redis_engine,
    init_sync_queue_redis_engine,
    close_sync_queue_redis_engine,
)
from app.utils.response_cache import _cache_instance, cache
from app.utils.response import BaseResponse
from app.utils.middleware import (
    TimingMiddleware,
    CountTrustableMiddleware,
    UncachePOSTMiddleware,
)
from app.utils.metric import init_prometheus_metrics

mcim_config = config_manager.mcim_config

# 全局状态变量，用于跟踪应用实例
app_instance = None


# 配置变更回调函数
async def on_mcim_config_change():
    """MCIM 配置变更时的处理函数"""
    global mcim_config
    log.info("MCIM 配置已更改，正在更新应用状态...")
    # 重新加载配置
    mcim_config = config_manager.mcim_config

    # 更新缓存设置
    if app_instance and hasattr(app_instance.state, "fastapi_cache"):
        if mcim_config.redis_cache:
            if not app_instance.state.fastapi_cache.is_enabled():
                log.info("启用 Redis 缓存...")
                app_instance.state.fastapi_cache.enable()
        else:
            if app_instance.state.fastapi_cache.is_enabled():
                log.info("禁用 Redis 缓存...")
                app_instance.state.fastapi_cache.disable()

    # 无法更新 Prometheus 设置
    # ERROR: Cannot add middleware after an application has started
    # if mcim_config.prometheus and not hasattr(app_instance.state, "prometheus"):
    #     log.info("初始化 Prometheus 指标...")
    #     init_prometheus_metrics(app_instance)

    log.info("MCIM 配置更新完成")


async def on_mongodb_config_change():
    """MongoDB 配置变更时的处理函数"""
    log.info("MongoDB 配置已更改，正在重新初始化连接...")

    # 只有当应用已经初始化时才进行重新连接
    if app_instance and hasattr(app_instance.state, "aio_mongo_engine"):
        try:
            # 获取新的 MongoDB 连接
            new_mongo_engine = init_mongodb_aioengine()

            # 重新初始化连接
            await setup_async_mongodb(new_mongo_engine)

            # 替换旧连接
            # old_engine = app_instance.state.aio_mongo_engine
            app_instance.state.aio_mongo_engine = new_mongo_engine

            log.info("MongoDB 连接已成功重新初始化")
        except Exception as e:
            log.error(f"MongoDB 连接重新初始化失败: {str(e)}")
    else:
        log.info("应用尚未初始化，跳过 MongoDB 重新连接")


async def on_redis_config_change():
    """Redis 配置变更时的处理函数"""
    log.info("Redis 配置已更改，正在重新初始化连接...")

    # 只有当应用已经初始化时才进行重新连接
    if app_instance and hasattr(app_instance.state, "aio_redis_engine"):
        try:
            # 关闭旧连接
            await close_aio_redis_engine()

            # 获取新的 Redis 连接
            app_instance.state.aio_redis_engine = init_redis_aioengine()

            # 如果启用了缓存，重新初始化缓存
            app_instance.state.fastapi_cache.init(enabled=mcim_config.redis_cache)

            log.info("Redis 连接已成功重新初始化")
        except Exception as e:
            log.error(f"Redis 连接重新初始化失败: {str(e)}")
    else:
        log.info("应用尚未初始化，跳过 Redis 重新连接")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global app_instance

    # 保存应用实例引用，以便在配置变更回调中访问
    app_instance = app

    # 注册配置变更回调
    config_manager.register_change_callback(MICM_CONFIG_PATH, on_mcim_config_change)
    config_manager.register_change_callback(
        MONGODB_CONFIG_PATH, on_mongodb_config_change
    )
    config_manager.register_change_callback(REDIS_CONFIG_PATH, on_redis_config_change)

    # 初始化连接
    app.state.aio_redis_engine = init_redis_aioengine()
    init_sync_queue_redis_engine()
    await app.state.aio_redis_engine.flushall()
    app.state.aio_mongo_engine = init_mongodb_aioengine()
    await setup_async_mongodb(app.state.aio_mongo_engine)

    # 初始化 redis 缓存
    app_instance.state.fastapi_cache = _cache_instance
    app_instance.state.fastapi_cache.init(
        enabled=mcim_config.redis_cache,
        backend=app.state.aio_redis_engine,
        namespace="fastapi_cache",
    )

    # 初始化 Prometheus 指标（如果启用）
    if mcim_config.prometheus:
        init_prometheus_metrics(app)

    yield

    # 应用关闭，取消注册回调，关闭连接
    config_manager.unregister_change_callback(MICM_CONFIG_PATH, on_mcim_config_change)
    config_manager.unregister_change_callback(
        MONGODB_CONFIG_PATH, on_mongodb_config_change
    )
    config_manager.unregister_change_callback(REDIS_CONFIG_PATH, on_redis_config_change)

    await close_aio_redis_engine()
    await close_sync_queue_redis_engine()

    # 清除全局引用
    app_instance = None

    log.info("应用已关闭，所有服务已停止")


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
