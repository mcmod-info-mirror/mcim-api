from odmantic import AIOEngine, SyncEngine
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from app.config import config_manager
from app.models.database.curseforge import Mod, File, Fingerprint  # , ModFilesSyncInfo
from app.models.database.modrinth import Project, Version, File as ModrinthFile
from app.models.database.file_cdn import File as CDNFile
from app.utils.loger import log

_mongodb_config = config_manager.mongodb_config

aio_mongo_engine: AIOEngine = None
sync_mongo_engine: SyncEngine = None


def init_mongodb_syncengine() -> SyncEngine:
    """
    Raw Motor client handler, use it when beanie cannot work
    :return:
    """
    global sync_mongo_engine
    sync_mongo_engine = SyncEngine(
        client=MongoClient(
            f"mongodb://{_mongodb_config.user}:{_mongodb_config.password}@{_mongodb_config.host}:{_mongodb_config.port}"
            if _mongodb_config.auth
            else f"mongodb://{_mongodb_config.host}:{_mongodb_config.port}"
        ),
        database="mcim_backend",
    )
    return sync_mongo_engine


def init_mongodb_aioengine() -> AIOEngine:
    """
    Raw Motor client handler, use it when beanie cannot work
    :return:
    """
    return AIOEngine(
        client=AsyncIOMotorClient(
            f"mongodb://{_mongodb_config.user}:{_mongodb_config.password}@{_mongodb_config.host}:{_mongodb_config.port}"
            if _mongodb_config.auth
            else f"mongodb://{_mongodb_config.host}:{_mongodb_config.port}"
        ),
        database="mcim_backend",
    )


async def setup_async_mongodb(engine: AIOEngine) -> None:
    """
    Start beanie when process started.
    :return:
    """
    # try:
    await engine.configure_database(
        [
            # CurseForge
            Mod,
            File,
            Fingerprint,
            # Modrinth
            Project,
            Version,
            ModrinthFile,
            # File CDN
            CDNFile,
        ]
    )


aio_mongo_engine: AIOEngine = init_mongodb_aioengine()
sync_mongo_engine: SyncEngine = init_mongodb_syncengine()

log.success("MongoDB connection established.")
