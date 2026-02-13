from fastapi.testclient import TestClient

from src.main import app 

import pytest 

@pytest.fixture
def client():
    return TestClient(app)

