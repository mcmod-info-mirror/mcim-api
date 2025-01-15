from typing import List, Optional, Union
from odmantic import query
import json
import time


from app.sync import sync_mongo_engine as mongodb_engine
from app.sync import sync_redis_engine as redis_engine
from app.models.database.curseforge import File, Mod, Pagination, Fingerprint
from app.models.database.file_cdn import File as FileCDN
from app.utils.network import request_sync
from app.config import MCIMConfig
from app.utils.loger import log

mcim_config = MCIMConfig.load()

API = mcim_config.curseforge_api
MAX_LENGTH = mcim_config.max_file_size
MIN_DOWNLOAD_COUNT = 0
HEADERS = {
    "x-api-key": mcim_config.curseforge_api_key,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.54",
}


def submit_models(models: List[Union[File, Mod, Fingerprint]]):
    if len(models) != 0:
        mongodb_engine.save_all(models)
        log.debug(f"Submited: {len(models)}")


def check_alive():
    return request_sync(API, headers=HEADERS).text


def append_model_from_files_res(
    res, latestFiles: dict, need_to_cache: bool = True
) -> List[Union[File, Fingerprint]]:
    models = []
    for file in res["data"]:
        for _hash in file["hashes"]:
            if _hash["algo"] == 1:
                file["sha1"] = _hash["value"]
            elif _hash["algo"] == 2:
                file["md5"] = _hash["value"]
        file_model = File(need_to_cache=need_to_cache, **file)
        models.append(file_model)
        models.append(
            Fingerprint(
                id=file["fileFingerprint"],
                file=file,
                latestFiles=latestFiles,
            )
        )
        # for file_cdn
        if mcim_config.file_cdn:
            if (
                file_model.sha1 is not None
                and file_model.gameId == 432
                and file_model.fileLength <= MAX_LENGTH
                and file_model.downloadCount >= MIN_DOWNLOAD_COUNT
                and file_model.downloadUrl is not None
            ):
                models.append(
                    FileCDN(
                        sha1=file_model.sha1,
                        url=file_model.downloadUrl,
                        path=file_model.sha1,
                        size=file_model.fileLength,
                        mtime=int(time.time()),
                    )
                )
    return models


# verify_expire: False 为待验证，True 为已验证过期
def sync_mod_all_files(
    modId: int,
    latestFiles: List[dict] = None,
    need_to_cache: bool = True,
    verify_expire: Optional[bool] = False,
) -> List[Union[File, Mod]]:
    if not verify_expire:  # 未确认
        # 再次检查是否已经过期，以免反复 update
        mod_model: Optional[Mod] = mongodb_engine.find_one(Mod, Mod.id == modId)
        if mod_model is not None:
            if (
                time.time()
                <= mod_model.sync_at.timestamp()
                + mcim_config.expire_second.curseforge.mod
            ):
                log.debug(f"Mod {modId} is not expired, pass!")
                return None
    models = []
    if not latestFiles:
        data = request_sync(f"{API}/v1/mods/{modId}", headers=HEADERS).json()["data"]
        latestFiles = data["latestFiles"]
        need_to_cache = True if data["classId"] == 6 else False

    params = {"index": 0, "pageSize": 50}
    res = request_sync(
        f"{API}/v1/mods/{modId}/files",
        headers=HEADERS,
        params=params,
    ).json()

    models = append_model_from_files_res(res, latestFiles, need_to_cache=need_to_cache)
    submit_models(models=models)
    log.info(
        f'Finished modid:{modId} i:ps:t {params["index"]}:{params["pageSize"]}:{res["pagination"]["totalCount"]}'
    )

    page = Pagination(**res["pagination"])
    # index A zero based index of the first item to include in the response, the limit is: (index + pageSize <= 10,000).
    while page.index < page.totalCount - 1:
        params = {"index": page.index + page.pageSize, "pageSize": page.pageSize}
        res = request_sync(
            f"{API}/v1/mods/{modId}/files", headers=HEADERS, params=params
        ).json()
        page = Pagination(**res["pagination"])
        models = append_model_from_files_res(
            res, latestFiles, need_to_cache=need_to_cache
        )
        submit_models(models=models)
        log.info(
            f'Finished modid:{modId} i:ps:t {params["index"]}:{params["pageSize"]}:{page.totalCount}'
        )
    log.info(f'Finished modid:{modId} with {res["pagination"]["totalCount"]} files')


def sync_multi_mods_all_files(modIds: List[int]):
    # 去重
    modIds = list(set(modIds))
    mod_models: Optional[List[Mod]] = mongodb_engine.find(
        Mod, query.in_(Mod.id, modIds)
    )
    for mod_model in mod_models:
        if (
            time.time()
            <= mod_model.sync_at.timestamp() + mcim_config.expire_second.curseforge.mod
        ):
            log.debug(f"Mod {mod_model.id} is not expired, pass!")
            modIds.remove(mod_model.id)
    for modId in modIds:
        sync_mod_all_files(modId, verify_expire=True)


def sync_mod(modId: int):
    models: List[Union[File, Mod]] = []
    res = request_sync(f"{API}/v1/mods/{modId}", headers=HEADERS).json()["data"]
    if not res["gameId"] == 432:
        log.debug(f"Mod {modId} is not belong to Minecraft, pass!")
        return
    models.append(Mod(**res))
    mod = mongodb_engine.find_one(Mod, Mod.id == modId)
    if mod is not None:
        if mod.dateReleased == models[0].dateReleased:
            log.debug(f"Mod {modId} is not out-of-date, pass!")
            return
    sync_mod_all_files(
        modId,
        latestFiles=res["latestFiles"],
        need_to_cache=True if res["classId"] == 6 else False,
    )
    submit_models(models)


def sync_mutil_mods(modIds: List[int]):
    modIds = list(set(modIds))
    data = {"modIds": modIds}
    res = request_sync(
        method="POST", url=f"{API}/v1/mods", json=data, headers=HEADERS
    ).json()["data"]
    models: List[Union[File, Mod]] = []
    mods = mongodb_engine.find(Mod, query.in_(Mod.id, modIds))
    mods_dateReleased_index = {mod.id: mod.dateReleased for mod in mods}
    for mod in res:
        if mod["gameId"] != 432:
            log.debug(f"Mod {mod['id']} is not belong to Minecraft, pass!")
        models.append(Mod(**mod))
        if mods_dateReleased_index.get(mod["id"]) is not None:
            if mods_dateReleased_index[mod["id"]] == mod["dateReleased"]:
                log.debug(f"Mod {mod['id']} is not updated, pass!")
                modIds.remove(mod["id"])

    sync_multi_mods_all_files([model.id for model in models])
    submit_models(models)


def sync_mutil_files(fileIds: List[int]):
    res = request_sync(
        method="POST",
        url=f"{API}/v1/mods/files",
        headers=HEADERS,
        json={"fileIds": fileIds},
    ).json()["data"]
    modids = [file["modId"] for file in res if file["gameId"] == 432]
    sync_multi_mods_all_files(modids)


def sync_fingerprints(fingerprints: List[int]):
    res = request_sync(
        method="POST",
        url=f"{API}/v1/fingerprints/432",
        headers=HEADERS,
        json={"fingerprints": fingerprints},
    ).json()
    modids = [
        file["file"]["modId"]
        for file in res["data"]["exactMatches"]
        if file["file"]["gameId"] == 432
    ]
    sync_multi_mods_all_files(modids)


def sync_categories():
    res = request_sync(
        f"{API}/v1/categories", headers=HEADERS, params={"gameId": "432"}
    ).json()["data"]
    redis_engine.hset("curseforge", "categories", json.dumps(res))
