from fastapi.testclient import TestClient

project_ids = ["AANobbMI", "P7dR8mSH"]

modIds = [238222, 1004027]


def test_curseforge_translate(client: TestClient):
    response = client.get(f"/translate/curseforge?modId={modIds[0]}")
    assert response.status_code == 200
    assert response.json()["modId"] == modIds[0]


def test_modrinth_translate(client: TestClient):
    response = client.get(f"/translate/modrinth?project_id={project_ids[0]}")
    assert response.status_code == 200
    assert response.json()["project_id"] == project_ids[0]


def test_modrinth_translate_batch(client: TestClient):
    response = client.post("/translate/modrinth", json={"project_ids": project_ids})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert all(item["project_id"] in project_ids for item in response.json())


def test_curseforge_translate_path(client: TestClient):
    response = client.post("/translate/curseforge", json={"modIds": modIds})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert all(item["modId"] in modIds for item in response.json())
