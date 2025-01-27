# import dramatiq
# from dramatiq.brokers.redis import RedisBroker
# from dramatiq.rate_limits.backends import RedisBackend
# from dramatiq.rate_limits import BucketRateLimiter, WindowRateLimiter
# from redis import Redis

# from app.database.mongodb import init_mongodb_syncengine, sync_mongo_engine
# from app.database._redis import (
#     init_sync_redis_engine,
#     close_sync_redis_engine,
#     sync_redis_engine,
# )
# from app.config import RedisdbConfig

# from app.utils.loger import log

# _redis_config = RedisdbConfig.load()


# init_sync_redis_engine()
# init_mongodb_syncengine()

# sync_redis_engine = sync_redis_engine
# sync_mongo_engine = sync_mongo_engine

# rate_limit_backend = RedisBackend(
#     client=Redis(
#         host=_redis_config.host,
#         port=_redis_config.port,
#         password=_redis_config.password,
#         db=_redis_config.database.rate_limit,
#     ),
# )

# redis_broker = RedisBroker(
#     host=_redis_config.host,
#     port=_redis_config.port,
#     password=_redis_config.password,
#     db=_redis_config.database.tasks_queue,
# )


# MODRINTH_LIMITER = WindowRateLimiter(
#     rate_limit_backend, "modrinth-sync-task-distributed-mutex", limit=100, window=60
# )
# CURSEFORGE_LIMITER = WindowRateLimiter(
#     rate_limit_backend, "curseforge-sync-task-distributed-mutex", limit=100, window=60
# )

# dramatiq.set_broker(redis_broker)

# log.success("Dramatiq broker set up successfully.")

# from app.sync.modrinth import *
# from app.sync.curseforge import *

# close_sync_redis_engine()