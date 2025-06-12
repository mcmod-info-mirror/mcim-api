from odmantic import AIOEngine, SyncEngine
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from app.config import MongodbConfig
from app.models.database.curseforge import Mod, File, Fingerprint
from app.models.database.modrinth import Project, Version, File as ModrinthFile
from app.models.database.file_cdn import File as CDNFile
from app.utils.loger import log

_mongodb_config = MongodbConfig.load()

aio_mongo_engine: AIOEngine = None
sync_mongo_engine: SyncEngine = None


def _create_mongodb_uri() -> str:
    """
    Constructs the MongoDB URI based on the configuration.
    :return: The MongoDB URI.
    """
    if _mongodb_config.auth:
        return (
            f"mongodb://{_mongodb_config.user}:{_mongodb_config.password}@"
            f"{_mongodb_config.host}:{_mongodb_config.port}"
        )
    else:
        return f"mongodb://{_mongodb_config.host}:{_mongodb_config.port}"


def init_mongodb_syncengine() -> SyncEngine:
    """
    Initializes the synchronous MongoDB engine.
    :return: The SyncEngine instance.
    """
    global sync_mongo_engine
    sync_mongo_engine = SyncEngine(
        client=MongoClient(
            _create_mongodb_uri()
        ),
        database="mcim_backend",
    )
    return sync_mongo_engine


def init_mongodb_aioengine() -> AIOEngine:
    """
    Initializes the asynchronous MongoDB engine.
    :return: The AIOEngine instance.
    """
    return AIOEngine(
        client=AsyncIOMotorClient(
            _create_mongodb_uri()
        ),
        database="mcim_backend",
    )


async def setup_async_mongodb(engine: AIOEngine) -> None:
    """
    Configures the database with the specified models.
    :param engine: The AIOEngine instance.
    """
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


def get_aio_mongodb_engine() -> AIOEngine:
    """
    Retrieves the AIOEngine instance, initializing it if it doesn't exist.
    :return: The AIOEngine instance.
    """
    global aio_mongo_engine
    if aio_mongo_engine is None:
        aio_mongo_engine = init_mongodb_aioengine()
    return aio_mongo_engine


# Initialize the engines
aio_mongo_engine: AIOEngine = init_mongodb_aioengine()
sync_mongo_engine: SyncEngine = init_mongodb_syncengine()

log.success("MongoDB connection established.")
