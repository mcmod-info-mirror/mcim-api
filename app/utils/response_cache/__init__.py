import orjson
from functools import wraps
from typing import Optional, Callable, Any, Union
from fastapi.responses import Response
from redis.asyncio import Redis
from app.utils.response_cache.key_builder import default_key_builder, KeyBuilder
from app.utils.response_cache.resp_builder import ResponseBuilder
from app.utils.loger import log
from app.config import config_manager

redis_config = config_manager.redis_config


class _Cache:
    def __init__(self):
        self.backend = None
        self.enabled = False
        self.namespace = "fastapi_cache"
        self.key_builder = default_key_builder
    
    def init(
        self,
        backend: Optional[Redis] = None,
        enabled: bool = False,
        namespace: str = "fastapi_cache",
        key_builder: KeyBuilder = default_key_builder,
    ) -> None:
        self.backend = (
            Redis(
                host=redis_config.host,
                port=redis_config.port,
                db=redis_config.database.info_cache,
                password=redis_config.password,
            )
            if backend is None
            else backend
        )
        self.enabled = enabled
        self.namespace = namespace
        self.key_builder = key_builder

    def is_enabled(self) -> bool:
        return self.enabled

    def enable(self) -> None:
        self.enabled = True
    
    def disable(self) -> None:
        self.enabled = False

_cache_instance = _Cache()

# 导出缓存装饰器函数
def cache(
    expire: int = 60, 
    never_expire: bool = False
) -> Callable:
    """
    函数结果缓存装饰器
    
    Args:
        expire: 缓存过期时间(秒)
        never_expire: 设置为True时永不过期
    """
    if not isinstance(expire, int):
        raise ValueError("expire must be an integer")
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if kwargs.get("force") is True or not _cache_instance.enabled:
                return await func(*args, **kwargs)
                
            key = _cache_instance.key_builder(
                func, namespace=_cache_instance.namespace, args=args, kwargs=kwargs
            )
            value = await _cache_instance.backend.get(key)

            if value is not None:
                value = orjson.loads(value)
                log.trace(f"Cached response: [{key}]")
                return ResponseBuilder.decode(value)

            result = await func(*args, **kwargs)
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
                await _cache_instance.backend.set(key, value)
            else:
                await _cache_instance.backend.set(key, value, ex=expire)
                
            log.trace(f"Set cache: [{key}]")
            return result

        return wrapper

    return decorator