from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoints():
    client = TestClient(create_app())

    live = client.get("/health/live")
    assert live.status_code == 200
    assert live.json()["status"] == "ok"

    ready = client.get("/health/ready")
    assert ready.status_code == 200
    payload = ready.json()
    assert payload["status"] == "ok"
    assert payload["data_mode"] in {"wind", "open"}
    assert payload["cache_enabled"] is False
