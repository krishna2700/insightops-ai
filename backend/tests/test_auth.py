from httpx import AsyncClient


async def test_register_creates_account_and_returns_token(client: AsyncClient):
    res = await client.post(
        "/api/auth/register",
        json={"email": "new@example.com", "password": "password123"},
    )
    assert res.status_code == 201
    assert "access_token" in res.json()


async def test_register_rejects_duplicate_email(client: AsyncClient):
    payload = {"email": "dupe@example.com", "password": "password123"}
    await client.post("/api/auth/register", json=payload)
    res = await client.post("/api/auth/register", json=payload)
    assert res.status_code == 400


async def test_login_rejects_wrong_password(client: AsyncClient):
    await client.post(
        "/api/auth/register", json={"email": "wrongpw@example.com", "password": "password123"}
    )
    res = await client.post(
        "/api/auth/login", json={"email": "wrongpw@example.com", "password": "nope12345"}
    )
    assert res.status_code == 401


async def test_me_requires_authentication(client: AsyncClient):
    res = await client.get("/api/auth/me")
    assert res.status_code == 401


async def test_me_returns_current_user(client: AsyncClient, auth_headers: dict[str, str]):
    res = await client.get("/api/auth/me", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["email"] == "test@example.com"
