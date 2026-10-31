import pytest
from ..main import app

def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"].strip() == "Backend actif"
    assert "ia" in data
    assert "database" in data
