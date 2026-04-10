from app.auth.schemas import UserRole
from app.auth.service import create_user, hash_password


async def test_admin_can_register_user(client, admin_token):
    response = await client.post(
        "/api/auth/register",
        json={"username": "bob", "password": "password123", "role": "editor"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "bob"
    assert body["role"] == "editor"
    assert body["is_active"] is True


async def test_editor_cannot_register_user(client, editor_token):
    response = await client.post(
        "/api/auth/register",
        json={"username": "bob", "password": "password123", "role": "viewer"},
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 403


async def test_register_duplicate_username(client, db_session, admin_token):
    create_user(
        db_session,
        username="bob",
        hashed_password=hash_password("password123"),
        role=UserRole.EDITOR,
    )

    response = await client.post(
        "/api/auth/register",
        json={"username": "bob", "password": "password456", "role": "viewer"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 409
