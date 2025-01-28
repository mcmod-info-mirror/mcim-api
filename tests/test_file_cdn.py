from fastapi.testclient import TestClient

from app.config import MCIMConfig

mcim_config = MCIMConfig.load()

cached_modrinth_sample = [
    "/data/Ua7DFN59/versions/xET3UZBe/YungsApi-1.19.2-Forge-3.8.2.jar",
    "/data/Ua7DFN59/versions/k1OTLc33/YungsApi-1.20-Fabric-4.0.4.jar",
]

uncached_modrinth_sample = [
    "/data/MdwFAVRL/versions/DQC4nTXQ/Cobblemon-forge-1.1.1%2B1.19.2.jar",
    "/data/fM515JnW/versions/n7Rl5o6Y/AmbientSounds_FABRIC_v6.0.1_mc1.20.1.jar",
]

cached_curseforge_sample = [
    "/files/6000/80/sodium-fabric-0.6.5%2Bmc1.21.1.jar",
    "/files/5217/345/Vanilla-Expanded-1.20.1-forge.jar",
]

uncached_curseforge_sample = [
    "/files/4706/778/cinderextras53g.jar",
    "/files/5529/108/tacz-1.18.2-1.0.2-release.ja",
]


def test_modrinth_file_cdn(client: TestClient):
    # 也许应该进一步验证返回的 URL 是源站还是 Open93Home
    for url in cached_modrinth_sample:
        response = client.get(url, follow_redirects=False)
        assert 300 <= response.status_code <= 400
        assert response.headers.get("Location") is not None

    for url in uncached_modrinth_sample:
        response = client.get(url, follow_redirects=False)
        assert 300 <= response.status_code <= 400
        assert response.headers.get("Location") is not None


def test_curseforge_file_cdn(client: TestClient):
    for url in cached_curseforge_sample:
        response = client.get(url)
        assert 300 <= response.status_code <= 400
        assert response.headers.get("Location") is not None

    for url in uncached_curseforge_sample:
        response = client.get(url)
        assert 300 <= response.status_code <= 400
        assert response.headers.get("Location") is not None


def test_file_cdn_list(client: TestClient):
    response = client.get(
        "/file_cdn/list", params={"secret": mcim_config.file_cdn_secret}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0
