from pydantic import BaseModel

from app.config.base import BaseConfig
from app.config.constants import MONGODB_CONFIG_PATH

class MongodbConfigModel(BaseModel):
    host: str = "mongodb"
    port: int = 27017
    auth: bool = True
    user: str = "username"
    password: str = "password"
    database: str = "database"


# class MongodbConfig:
#     @staticmethod
#     def save(
#         model: MongodbConfigModel = MongodbConfigModel(), target=MONGODB_CONFIG_PATH
#     ):
#         with open(target, "w") as fd:
#             json.dump(model.model_dump(), fd, indent=4)

#     @staticmethod
#     def load(target=MONGODB_CONFIG_PATH) -> MongodbConfigModel:
#         if not os.path.exists(target):
#             MongodbConfig.save(target=target)
#             return MongodbConfigModel()
#         with open(target, "r") as fd:
#             data = json.load(fd)
#         return MongodbConfigModel(**data)


class MongodbConfig(BaseConfig[MongodbConfigModel]):
    MODEL_CLASS = MongodbConfigModel
    DEFAULT_CONFIG_PATH = MONGODB_CONFIG_PATH