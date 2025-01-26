
import pytest
from fastapi.testclient import TestClient

from app import APP

@pytest.fixture(scope="session", autouse=True)
def client():
    # return TestClient(APP)
    # You should use TestClient as a context manager, to ensure that the lifespan is called.
    # https://www.starlette.io/lifespan/#running-lifespan-in-tests
    with TestClient(app=APP) as client:
        yield client