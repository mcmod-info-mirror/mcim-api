
import pytest
from fastapi.testclient import TestClient

from app import APP

@pytest.fixture(scope="session", autouse=True)
def client():
    return TestClient(APP)