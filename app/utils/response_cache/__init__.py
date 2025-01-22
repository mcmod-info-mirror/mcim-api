import orjson
from functools import wraps
from typing import Optional
from fastapi.responses import Response
from redis.asyncio import Redis
from app.utils.response_cache.key_builder import default_key_builder, KeyBuilder
from app.utils.response_cache.resp_builder import ResponseBuilder
from app.utils.loger import log
from app.config.redis import RedisdbConfig
from app.utils.metric import REDIS_CACHE_HIT_GAUGE

redis_config = RedisdbConfig.load()


class Cache:
    backend: Redis
    enabled: bool = False
    namespace: str = "fastapi_cache"
    key_builder: KeyBuilder = default_key_builder

    @classmethod
    def init(
        cls,
        backend: Optional[Redis] = None,
        enabled: Optional[bool] = False,
        namespace: Optional[str] = "fastapi_cache",
        key_builder: KeyBuilder = default_key_builder,
    ) -> None:
        cls.backend = (
            Redis(
                host=redis_config.host,
                port=redis_config.port,
                db=redis_config.database.info_cache,
                password=redis_config.password,
            )
            if backend is None
            else backend
        )
        cls.enabled = enabled
        cls.namespace = namespace
        cls.key_builder = key_builder


def cache(expire: Optional[int] = 60, never_expire: Optional[bool] = False):
    if not isinstance(expire, int):
        raise ValueError("expire must be an integer")

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if kwargs.get("force") is True or not Cache.enabled:
                return await func(*args, **kwargs)
            key = default_key_builder(
                func, namespace=Cache.namespace, args=args, kwargs=kwargs
            )
            value = await Cache.backend.get(key)

            if value is not None:
                value = orjson.loads(value)
                # log.debug(f"Cached response: [{key}]")
                log.trace(f"Cached response: [{key}]")
                REDIS_CACHE_HIT_GAUGE.labels(f'{func.__module__}:{func.__name__}').inc()
                return ResponseBuilder.decode(value)

            result = await func(*args, **kwargs)
            REDIS_CACHE_HIT_GAUGE.labels(f'{func.__module__}:{func.__name__}').dec()
            if isinstance(result, Response):
                if result.status_code >= 400:
                    return result
                elif "Cache-Control" in result.headers:
                    if "no-cache" in result.headers["Cache-Control"]:
                        return result

                to_set = ResponseBuilder.encode(result)
            else:
                return result
            value = orjson.dumps(to_set)

            if never_expire:
                await Cache.backend.set(key, value)
            else:
                await Cache.backend.set(key, value, ex=expire)
            log.debug(f"Set cache: [{key}]")

            return result

        return wrapper

    return decorator
