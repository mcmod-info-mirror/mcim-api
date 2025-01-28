from fastapi.testclient import TestClient

from app.config import MCIMConfig

mcim_config = MCIMConfig.load()

modrinth_sample = ["/data/AANobbMI/versions/Hd6ChVqe/sodium-fabric-0.6.3%2Bmc1.21.1.jar"] # 7e75f9d2dedfa158be6391052dccdfe91ed0cb29

curseforge_sample = ["/files/6000/80/sodium-fabric-0.6.5%2Bmc1.21.1.jar"] # 68469cfbcb1b7fcdb0d11c8b984a657adfac5684

def test_modrinth_file_cdn(client: TestClient):
    for url in modrinth_sample:
        response = client.get(url)
        assert response.status_code <= 400

def test_curseforge_file_cdn(client: TestClient):
    for url in curseforge_sample:
        response = client.get(url)
        assert response.status_code <= 400

def test_file_cdn_list(client: TestClient):
    response = client.get("/file_cdn/list", params={"secret": mcim_config.file_cdn_secret})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0