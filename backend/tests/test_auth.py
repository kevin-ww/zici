import pytest


@pytest.mark.asyncio
async def test_register(client):
    r = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
        "display_name": "Test User",
    })
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "test@example.com"
    assert body["display_name"] == "Test User"
    assert "id" in body
    assert "hashed_password" not in body


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": "password123"}
    await client.post("/api/auth/register", json=payload)
    r = await client.post("/api/auth/register", json=payload)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_login(client):
    await client.post("/api/auth/register", json={
        "email": "login@example.com",
        "password": "password123",
    })
    r = await client.post("/api/auth/login", json={
        "email": "login@example.com",
        "password": "password123",
    })
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/auth/register", json={
        "email": "wrongpw@example.com",
        "password": "correctpassword",
    })
    r = await client.post("/api/auth/login", json={
        "email": "wrongpw@example.com",
        "password": "wrongpassword",
    })
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client):
    r = await client.post("/api/auth/login", json={
        "email": "nobody@example.com",
        "password": "password123",
    })
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me(client):
    await client.post("/api/auth/register", json={
        "email": "me@example.com",
        "password": "password123",
        "display_name": "Me User",
    })
    login_r = await client.post("/api/auth/login", json={
        "email": "me@example.com",
        "password": "password123",
    })
    token = login_r.json()["access_token"]

    r = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "me@example.com"
    assert body["display_name"] == "Me User"
    assert "hashed_password" not in body


@pytest.mark.asyncio
async def test_me_no_token(client):
    r = await client.get("/api/auth/me")
    assert r.status_code in (401, 403)  # HTTPBearer returns 401/403 depending on FastAPI version


@pytest.mark.asyncio
async def test_me_invalid_token(client):
    r = await client.get("/api/auth/me", headers={"Authorization": "Bearer invalidtoken"})
    assert r.status_code == 401
