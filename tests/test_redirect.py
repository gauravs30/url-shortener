from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.models import Click, Link


async def _make_link(client, **extra):
    r = await client.post("/api/links", json={"url": "https://example.com", **extra})
    assert r.status_code == 201
    return r.json()["code"]


async def test_known_code_redirects_307(client):
    code = await _make_link(client, alias="goto")
    r = await client.get(f"/{code}", follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == "https://example.com"


async def test_unknown_code_404(client):
    r = await client.get("/missing", follow_redirects=False)
    assert r.status_code == 404


async def test_expired_code_410(client):
    past = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    code = await _make_link(client, alias="old", expires_at=past)
    r = await client.get(f"/{code}", follow_redirects=False)
    assert r.status_code == 410


async def test_click_is_recorded(client, session):
    code = await _make_link(client, alias="count")
    await client.get(f"/{code}", follow_redirects=False)
    await client.get(f"/{code}", follow_redirects=False)

    link = await session.scalar(select(Link).where(Link.code == code))
    assert link.click_count == 2
    clicks = list(await session.scalars(select(Click).where(Click.link_id == link.id)))
    assert len(clicks) == 2
    assert clicks[0].ip_hash is not None  # hashed, never the raw IP


async def test_stats_endpoint(client):
    code = await _make_link(client, alias="stats1")
    await client.get(f"/{code}", follow_redirects=False)
    r = await client.get(f"/api/links/{code}/stats")
    assert r.status_code == 200
    body = r.json()
    assert body["total_clicks"] == 1
    assert body["clicks_by_day"][0]["count"] == 1
    assert len(body["recent_clicks"]) == 1
