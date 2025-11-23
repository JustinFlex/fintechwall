from fastapi.testclient import TestClient

from app.main import create_app


def test_get_and_update_config():
    client = TestClient(create_app())

    resp = client.get("/config")
    assert resp.status_code == 200
    assert resp.json()["data_mode"] in {"wind", "open", "mock"}

    update = client.post("/config", json={"data_mode": "open"})
    assert update.status_code == 200
    assert update.json()["data_mode"] == "open"

    bad = client.post("/config", json={"data_mode": "invalid"})
    assert bad.status_code == 400
