from typing import List, Union, Optional
from pydantic import BaseModel

from app.config.base import BaseConfig
from app.config.constants import REDIS_CONFIG_PATH

class RedisDatabaseModel(BaseModel):
    tasks_queue: int = 0  # dramatiq tasks
    info_cache: int = 1  # response_cache and static info
    rate_limit: int = 3  # rate limit
    sync_queue: int = 4  # sync queue

class RedisConfigModel(BaseModel):
    host: str = "redis"
    port: int = 6379
    user: Optional[str] = None
    password: Optional[str] = None
    database: RedisDatabaseModel = RedisDatabaseModel()

# class RedisdbConfig:
#     @staticmethod
#     def save(
#         model: RedisdbConfigModel = RedisdbConfigModel(), target=REDIS_CONFIG_PATH
#     ):
#         with open(target, "w") as fd:
#             json.dump(model.model_dump(), fd, indent=4)

#     @staticmethod
#     def load(target=REDIS_CONFIG_PATH) -> RedisdbConfigModel:
#         if not os.path.exists(target):
#             RedisdbConfig.save(target=target)
#             return RedisdbConfigModel()
#         with open(target, "r") as fd:
#             data = json.load(fd)
#         return RedisdbConfigModel(**data)


class RedisConfig(BaseConfig[RedisConfigModel]):
    MODEL_CLASS = RedisConfigModel
    DEFAULT_CONFIG_PATH = REDIS_CONFIG_PATH