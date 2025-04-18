from fastapi.testclient import TestClient


modIds = [946010, 594678]

fileIds = [3913840, 5976953]

fingerprints = [2070800629, 1904165976]

error_fingerprints = [114514]

test_fingerprints = fingerprints + error_fingerprints


fileId = 3913840
modId = 594678
download_url = (
    "https://edge.forgecdn.net/files/3913/840/hats-and-cosmetics-1.2.2-1.19.1.jar"
)

classId = 6
gameId = 432


def test_curseforge_root(client: TestClient):
    response = client.get("/curseforge/")
    assert response.status_code == 200
    assert response.json() == {"message": "CurseForge"}


def test_curseforge_mods_search(client: TestClient):
    response = client.get(
        "/curseforge/v1/mods/search", params={"searchFilter": "fabric-api"}
    )
    assert response.status_code == 200


def test_curseforge_mod(client: TestClient):
    for modId in modIds:
        response = client.get(f"/curseforge/v1/mods/{modId}")
        assert response.status_code == 200
        assert response.json()["data"]["id"] == modId


def test_curseforge_mods(client: TestClient):
    response = client.post("/curseforge/v1/mods", json={"modIds": modIds})
    assert response.status_code == 200
    assert len(response.json()["data"]) == len(modIds)


def test_curseforge_mod_files(client: TestClient):
    for modId in modIds:
        response = client.get(f"/curseforge/v1/mods/{modId}/files")
        assert response.status_code == 200
        assert len(response.json()["data"]) > 0


def test_curseforge_file(client: TestClient):
    response = client.get(f"/curseforge/v1/mods/{modId}/files/{fileId}")
    assert response.status_code == 200
    assert response.json()["data"]["id"] == fileId
    assert response.json()["data"]["modId"] == modId


def test_curseforge_file_download_url(client: TestClient):
    response = client.get(f"/curseforge/v1/mods/{modId}/files/{fileId}/download-url")
    assert response.status_code == 200
    assert isinstance(response.json()["data"], str)


def test_curseforge_files(client: TestClient):
    response = client.post("/curseforge/v1/mods/files", json={"fileIds": fileIds})
    assert response.status_code == 200
    assert len(response.json()["data"]) == len(fileIds)


def test_curseforge_fingerprints(client: TestClient):
    response = client.post(
        "/curseforge/v1/fingerprints", json={"fingerprints": test_fingerprints}
    )
    assert response.status_code == 200
    assert sorted(response.json()["data"]["exactFingerprints"]) == sorted(fingerprints)
    assert sorted(response.json()["data"]["unmatchedFingerprints"]) == sorted(
        error_fingerprints
    )
    assert len(response.json()["data"]["exactMatches"]) == len(fingerprints)


def test_curseforge_fingerprints_432(client: TestClient):
    response = client.post(
        "/curseforge/v1/fingerprints/432", json={"fingerprints": test_fingerprints}
    )
    assert response.status_code == 200
    assert sorted(response.json()["data"]["exactFingerprints"]) == sorted(fingerprints)
    assert sorted(response.json()["data"]["unmatchedFingerprints"]) == sorted(
        error_fingerprints
    )
    assert len(response.json()["data"]["exactMatches"]) == len(fingerprints)


def test_curseforge_categories(client: TestClient):
    # only gameId 432
    response = client.get("/curseforge/v1/categories", params={"gameId": gameId})
    assert response.status_code == 200
    assert len(response.json()["data"]) > 0
    # with classId 6
    response = client.get(
        "/curseforge/v1/categories", params={"gameId": gameId, "classId": classId}
    )
    assert response.status_code == 200
    assert len(response.json()["data"]) > 0
    assert all([category["classId"] == classId for category in response.json()["data"]])
    # classOnly
    response = client.get(
        "/curseforge/v1/categories", params={"gameId": gameId, "classOnly": True}
    )
    assert response.status_code == 200
    assert len(response.json()["data"]) > 0
    assert all([category["isClass"] == True for category in response.json()["data"]])
