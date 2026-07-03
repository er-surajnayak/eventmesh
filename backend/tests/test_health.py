"""Smoke tests for the health endpoint and auth gating."""

from httpx import AsyncClient


async def test_health_ok(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert "version" in body


async def test_health_live(client: AsyncClient) -> None:
    resp = await client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json()["status"] == "alive"


async def test_health_ready(client: AsyncClient) -> None:
    # 200 when the DB is reachable, 503 otherwise — both are valid, well-formed.
    resp = await client.get("/health/ready")
    assert resp.status_code in (200, 503)
    body = resp.json()
    assert body["status"] in ("ready", "not_ready")
    assert body["database"] in ("up", "down")


async def test_me_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthorized"
