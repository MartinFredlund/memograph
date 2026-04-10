from app.auth.schemas import UserRole
from app.auth.service import create_user, hash_password


async def test_login_happy_path(client, db_session):
    create_user(
        db_session,
        username="alice",
        hashed_password=hash_password("correcthorsebattery"),
        role=UserRole.ADMIN,
    )

    response = await client.post(
        "/api/auth/login",
        data={"username": "alice", "password": "correcthorsebattery"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


async def test_login_wrong_password(client, db_session):
    create_user(
        db_session,
        username="alice",
        hashed_password=hash_password("correcthorsebattery"),
        role=UserRole.ADMIN,
    )

    response = await client.post(
        "/api/auth/login",
        data={"username": "alice", "password": "wrongpassword"},
    )

    assert response.status_code == 401


async def test_login_unknown_user(client):
    response = await client.post(
        "/api/auth/login",
        data={"username": "ghost", "password": "doesntmatter"},
    )

    assert response.status_code == 401
