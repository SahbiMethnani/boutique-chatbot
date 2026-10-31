import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from .. import main  

@pytest.fixture(scope="session")
def client():
    return TestClient(main.app)
