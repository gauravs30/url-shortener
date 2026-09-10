async def test_create_random_link(client):
    r = await client.post("/api/links", json={"url": "https://example.com"})
    assert r.status_code == 201
    body = r.json()
    assert body["target_url"] == "https://example.com"
    assert body["short_url"].endswith("/" + body["code"])
    assert body["expires_at"] is None


async def test_create_custom_alias(client):
    r = await client.post("/api/links", json={"url": "https://example.com", "alias": "my-link"})
    assert r.status_code == 201
    assert r.json()["code"] == "my-link"


async def test_duplicate_alias_conflicts(client):
    payload = {"url": "https://example.com", "alias": "dup"}
    assert (await client.post("/api/links", json=payload)).status_code == 201
    r = await client.post("/api/links", json=payload)
    assert r.status_code == 409


async def test_reserved_alias_rejected(client):
    r = await client.post("/api/links", json={"url": "https://example.com", "alias": "api"})
    assert r.status_code == 422


async def test_bad_url_rejected(client):
    r = await client.post("/api/links", json={"url": "ftp://example.com"})
    assert r.status_code == 422


async def test_ttl_days_sets_expiry(client):
    r = await client.post("/api/links", json={"url": "https://example.com", "ttl_days": 7})
    assert r.status_code == 201
    assert r.json()["expires_at"] is not None


async def test_ttl_and_expires_at_are_mutually_exclusive(client):
    r = await client.post(
        "/api/links",
        json={"url": "https://example.com", "ttl_days": 1, "expires_at": "2030-01-01T00:00:00Z"},
    )
    assert r.status_code == 422


async def test_metadata_and_missing(client):
    await client.post("/api/links", json={"url": "https://example.com", "alias": "meta"})
    assert (await client.get("/api/links/meta")).status_code == 200
    assert (await client.get("/api/links/nope")).status_code == 404


async def test_rate_limit_kicks_in(client):
    codes = [
        (await client.post("/api/links", json={"url": "https://example.com"})).status_code
        for _ in range(25)
    ]
    assert 429 in codes
