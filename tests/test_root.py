from fastapi.testclient import TestClient

def test_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_statistics(client: TestClient):
    response = client.get("/statistics")
    assert response.status_code == 200