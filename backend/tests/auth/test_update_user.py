from app.auth.schemas import UserRole
from app.auth.service import create_user, hash_password


async def test_admin_can_update_role(client, db_session, admin_token):
    user = create_user(db_session, "alice", hash_password("password123"), UserRole.VIEWER)

    response = await client.put(
        f"/api/users/{user['uid']}",
        json={"role": "editor"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "editor"


async def test_admin_can_update_username(client, db_session, admin_token):
    user = create_user(db_session, "alice", hash_password("password123"), UserRole.EDITOR)

    response = await client.put(
        f"/api/users/{user['uid']}",
        json={"username": "alice_new"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == "alice_new"


async def test_editor_cannot_update_user(client, db_session, editor_token):
    user = create_user(db_session, "alice", hash_password("password123"), UserRole.VIEWER)

    response = await client.put(
        f"/api/users/{user['uid']}",
        json={"role": "editor"},
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 403


async def test_update_nonexistent_user(client, admin_token):
    response = await client.put(
        "/api/users/nonexistent-uid",
        json={"role": "editor"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 404
