from fastapi.testclient import TestClient

project_id = "AANobbMI"

modId = 238222

def test_curseforge_translate(client: TestClient):
    response = client.get(f"/translate/curseforge?modId={modId}")
    assert response.status_code == 200
    assert response.json()["modId"] == modId

def test_modrinth_translate(client: TestClient):
    response = client.get(f"/translate/modrinth?project_id={project_id}")
    assert response.status_code == 200
    assert response.json()["project_id"] == project_id