import pytest
from httpx import AsyncClient

from app.main import create_app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_latest_basic_payload():
    app = create_app()
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        resp = await client.get("/data/latest")
    assert resp.status_code == 200
    payload = resp.json()
    for key in [
        "timestamp",
        "data_mode",
        "a_shares",
        "a_share_heatmap",
        "a_share_short_term",
        "fx",
        "commodities",
        "rates",
        "crypto",
        "summary",
        "heatmap",
    ]:
        assert key in payload
    assert payload["data_mode"] in {"mock", "wind", "open"}
    if payload["data_mode"] == "mock":
        assert payload["a_shares"]
        assert payload["heatmap"]
        assert payload["a_share_short_term"].get("hot_boards")
