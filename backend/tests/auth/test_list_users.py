from app.auth.schemas import UserRole
from app.auth.service import create_user, hash_password


async def test_admin_can_list_users(client, db_session, admin_token):
    create_user(db_session, "alice", hash_password("password123"), UserRole.EDITOR)
    create_user(db_session, "bob", hash_password("password123"), UserRole.VIEWER)

    response = await client.get(
        "/api/users/",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    usernames = [u["username"] for u in response.json()]
    assert "alice" in usernames
    assert "bob" in usernames


async def test_editor_cannot_list_users(client, editor_token):
    response = await client.get(
        "/api/users/",
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 403


async def test_list_users_empty(client, admin_token):
    response = await client.get(
        "/api/users/",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert response.json() == []
