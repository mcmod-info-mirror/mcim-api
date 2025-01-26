from fastapi.testclient import TestClient
import json

project_ids = ["Wnxd13zP", "Ua7DFN59"]
version_ids = [
    "dpSzBMP6",
    "IOIGqCVr",
    "xVBjqLw6",
    "8jfhokYb",
    "fTWVa6NX",
    "Km2A7nLe",
]
sha512_sample = [
    "be134c430492bb8933ff60cc59ff6143b25c4b79aa0d4a6e0332d9de7cfe1bacd16a43fe17167e9cc57d4747237f68cf584b99dd78233799239fb6acc0807d61",
    "1c97698babd08c869f76c53e86b4cfca3f369d0fdf0d8237d5d37d03d37cc4de9fc6a831f00c5ce8de6b145e774a31d0adc301e85fb24a4649e9af5c75156a0f",
    "4962062a240a10d1eb3507b28477270d7557a2d3d83ef459f9939a4be32fa8f8fcc92c3eab5125b183f7da11a73cd9f06fb049a8b6cbc276fe3401bbede766de",
]
sha1_sample = [
    "f0cea90219f681c3183e0d37d021cb8902d2d085",
    "627c93adb68e04ffb390ad0e5dbf62d342f27a28",
    "e8b77ed731002c41d0658d5386cfc25f0df12dc4",
    "d3bcef6c363422b38cbd0298af63a27b5e75829d",
]


def test_modrinth_root(client: TestClient):
    response = client.get("/modrinth/")
    assert response.status_code == 200
    assert response.json() == {"message": "Modrinth"}


def test_modrinth_search(client: TestClient):
    response = client.get("/modrinth/v2/search", params={"query": "sodium"})
    assert response.status_code == 200

def test_modrinth_project(client: TestClient):
    for project_id in project_ids:
        response = client.get(f"/modrinth/v2/project/{project_id}")
        assert response.status_code == 200
        assert response.json()["id"] == project_id


def test_modrinth_projects(client: TestClient):
    response = client.get(
        "/modrinth/v2/projects", params={"ids": json.dumps(project_ids)})
    assert response.status_code == 200
    assert len(response.json()) == len(project_ids)


def test_modrinth_project_versions(client: TestClient):
    for project_id in project_ids:
        response = client.get(f"/modrinth/v2/project/{project_id}/version")
        assert response.status_code == 200
        assert len(response.json()) > 0


def test_modrinth_version(client: TestClient):
    for version_id in version_ids:
        response = client.get(f"/modrinth/v2/version/{version_id}")
        assert response.status_code == 200
        assert response.json()["id"] == version_id


def test_modrinth_versions(client: TestClient):
    response = client.get(
        "/modrinth/v2/versions", params={"ids": json.dumps(version_ids)}
    )
    assert response.status_code == 200
    assert len(response.json()) == len(version_ids)


def test_modrinth_version_file_sha1(client: TestClient):
    for sha1_hash in sha1_sample:
        response = client.get(
            f"/modrinth/v2/version_file/{sha1_hash}", params={"algorithm": "sha1"}
        )
        assert response.status_code == 200


def test_modrinth_version_file_sha512(client: TestClient):
    for sha512_hash in sha512_sample:
        response = client.get(
            f"/modrinth/v2/version_file/{sha512_hash}", params={"algorithm": "sha512"}
        )
        assert response.status_code == 200


def test_modrinth_version_file_sha1_update(client: TestClient):
    for sha1_hash in sha1_sample:
        response = client.post(
            f"/modrinth/v2/version_file/{sha1_hash}/update",
            params={"algorithm": "sha1"},
            json={
                "loaders": ["fabric"],
                "game_versions": ["1.20.1"],
            },
        )
        assert response.status_code == 200

def test_modrinth_version_file_sha512_update(client: TestClient):
    for sha512_hash in sha512_sample:
        response = client.post(
            f"/modrinth/v2/version_file/{sha512_hash}/update",
            params={"algorithm": "sha512"},
            json={
                "loaders": ["fabric"],
                "game_versions": ["1.20.1"],
            },
        )
        assert response.status_code == 200

def test_modrinth_version_files_sha1(client: TestClient):
    response = client.post(
        "/modrinth/v2/version_files",
        json={"algorithm": "sha1", "hashes": sha1_sample},
    )
    assert response.status_code == 200
    assert len(response.json().keys()) == len(sha1_sample)

def test_modrinth_version_files_sha512(client: TestClient):
    response = client.post(
        "/modrinth/v2/version_files",
        json={"algorithm": "sha512", "hashes": sha512_sample},
    )
    assert response.status_code == 200
    assert len(response.json().keys()) == len(sha512_sample)

def test_modrinth_version_files_sha1_update(client: TestClient):
    response = client.post(
        "/modrinth/v2/version_files/update",
        json={
            "hashes": sha1_sample,
            "algorithm": "sha1",
            "loaders": ["fabric"],
            "game_versions": ["1.20.1"],
        },
    )
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_modrinth_version_files_sha512_update(client: TestClient):
    response = client.post(
        "/modrinth/v2/version_files/update",
        json={
            "hashes": sha512_sample,
            "algorithm": "sha512",
            "loaders": ["fabric"],
            "game_versions": ["1.20.1"],
        },
    )
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_modrinth_tag_category(client: TestClient):
    response = client.get("/modrinth/v2/tag/category")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_modrinth_tag_loader(client: TestClient):
    response = client.get("/modrinth/v2/tag/loader")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_modrinth_tag_game_version(client: TestClient):
    response = client.get("/modrinth/v2/tag/game_version")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_modrinth_tag_donation_platform(client: TestClient):
    response = client.get("/modrinth/v2/tag/donation_platform")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_modrinth_tag_project_type(client: TestClient):
    response = client.get("/modrinth/v2/tag/project_type")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_modrinth_tag_side_type(client: TestClient):
    response = client.get("/modrinth/v2/tag/side_type")
    assert response.status_code == 200
    assert len(response.json()) > 0