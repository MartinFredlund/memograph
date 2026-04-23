from uuid import uuid4


async def test_update_caption_only(client, seeded_image, editor_user):
    response = await client.put(
        f"/api/images/{seeded_image['uid']}",
        json={"caption": "Beach day"},
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["caption"] == "Beach day"
    assert body["taken_date"] is None


async def test_update_taken_date_only(client, seeded_image, editor_user):
    response = await client.put(
        f"/api/images/{seeded_image['uid']}",
        json={"taken_date": "2024-12-25"},
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["taken_date"] == "2024-12-25"
    assert body["caption"] is None


async def test_update_both_fields(client, seeded_image, editor_user):
    response = await client.put(
        f"/api/images/{seeded_image['uid']}",
        json={"caption": "Christmas morning", "taken_date": "2024-12-25"},
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["caption"] == "Christmas morning"
    assert body["taken_date"] == "2024-12-25"


async def test_update_does_not_overwrite_unset_fields(client, seeded_image, editor_user):
    await client.put(
        f"/api/images/{seeded_image['uid']}",
        json={"caption": "First caption"},
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    response = await client.put(
        f"/api/images/{seeded_image['uid']}",
        json={"taken_date": "2024-06-15"},
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["caption"] == "First caption"
    assert body["taken_date"] == "2024-06-15"


async def test_update_can_clear_field_to_null(client, seeded_image, editor_user):
    await client.put(
        f"/api/images/{seeded_image['uid']}",
        json={"caption": "Will be removed"},
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    response = await client.put(
        f"/api/images/{seeded_image['uid']}",
        json={"caption": None},
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 200
    assert response.json()["caption"] is None


async def test_update_empty_body(client, seeded_image, editor_user):
    response = await client.put(
        f"/api/images/{seeded_image['uid']}",
        json={},
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 200
    assert response.json()["uid"] == seeded_image["uid"]


async def test_update_not_found(client, editor_user, fake_storage):
    response = await client.put(
        f"/api/images/{uuid4()}",
        json={"caption": "Ghost image"},
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 404


async def test_update_viewer_forbidden(client, seeded_image, viewer_token):
    response = await client.put(
        f"/api/images/{seeded_image['uid']}",
        json={"caption": "Nope"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 403
