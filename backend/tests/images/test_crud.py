from io import BytesIO
from uuid import uuid4

from PIL import Image as PILImage


# --- Rotate ---


async def test_rotate_happy_path(client, seeded_image, editor_user, fake_storage):
    response = await client.post(
        f"/api/images/{seeded_image['uid']}/rotate",
        json={"degrees": 90},
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["uid"] == seeded_image["uid"]

    # The stored bytes must be a valid image whose dimensions swapped.
    # Original was 100x50 → after ROTATE_90 it must be 50x100.
    stored_bytes = fake_storage[seeded_image["object_key"]]
    rotated = PILImage.open(BytesIO(stored_bytes))
    assert rotated.size == (50, 100)

    # size_bytes on the node should match the new payload.
    assert body["size_bytes"] == len(stored_bytes)


async def test_rotate_not_found(client, fake_storage, editor_user):
    response = await client.post(
        f"/api/images/{uuid4()}/rotate",
        json={"degrees": 90},
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 404


async def test_rotate_viewer_forbidden(client, seeded_image, viewer_token):
    response = await client.post(
        f"/api/images/{seeded_image['uid']}/rotate",
        json={"degrees": 90},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 403


async def test_rotate_rejects_invalid_degrees(client, seeded_image, editor_user):
    response = await client.post(
        f"/api/images/{seeded_image['uid']}/rotate",
        json={"degrees": 45},
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 422


async def test_rotate_normalizes_exif_orientation(
    client, seeded_oriented_image, editor_user, fake_storage
):
    """Regression: rotating a photo with an EXIF Orientation tag must not
    leave the tag intact, or EXIF-respecting viewers will double-rotate.

    Also covers the subtler format-loss bug: when ImageOps.exif_transpose
    physically rotates pixels, the returned image's `.format` attribute is
    dropped. Without capturing the original format before that call, the
    save step fails with 'unknown file extension'.
    """
    response = await client.post(
        f"/api/images/{seeded_oriented_image['uid']}/rotate",
        json={"degrees": 90},
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 200
    stored = fake_storage[seeded_oriented_image["object_key"]]
    reloaded = PILImage.open(BytesIO(stored))
    orientation = reloaded.getexif().get(274, 1)
    assert orientation == 1, (
        f"Orientation should be normalized to 1, got {orientation}"
    )


# --- Delete ---


async def test_delete_admin_can_delete_any_image(
    client, seeded_image, admin_user, fake_storage, db_session
):
    response = await client.delete(
        f"/api/images/{seeded_image['uid']}",
        headers={"Authorization": f"Bearer {admin_user['token']}"},
    )

    assert response.status_code == 204
    assert response.content == b""
    assert seeded_image["object_key"] not in fake_storage
    record = db_session.run(
        "MATCH (i:Image {uid: $uid}) RETURN i", uid=seeded_image["uid"]
    ).single()
    assert record is None


async def test_delete_owner_editor_can_delete_own_image(
    client, seeded_image, editor_user, fake_storage, db_session
):
    response = await client.delete(
        f"/api/images/{seeded_image['uid']}",
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 204
    assert seeded_image["object_key"] not in fake_storage
    record = db_session.run(
        "MATCH (i:Image {uid: $uid}) RETURN i", uid=seeded_image["uid"]
    ).single()
    assert record is None


async def test_delete_editor_cannot_delete_others_image(
    client, seeded_image, other_editor_user, fake_storage, db_session
):
    response = await client.delete(
        f"/api/images/{seeded_image['uid']}",
        headers={"Authorization": f"Bearer {other_editor_user['token']}"},
    )

    assert response.status_code == 403
    # Image must still exist in both storage and the graph.
    assert seeded_image["object_key"] in fake_storage
    record = db_session.run(
        "MATCH (i:Image {uid: $uid}) RETURN i", uid=seeded_image["uid"]
    ).single()
    assert record is not None


async def test_delete_viewer_forbidden(client, seeded_image, viewer_token):
    response = await client.delete(
        f"/api/images/{seeded_image['uid']}",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 403


async def test_delete_not_found(client, fake_storage, admin_user):
    response = await client.delete(
        f"/api/images/{uuid4()}",
        headers={"Authorization": f"Bearer {admin_user['token']}"},
    )

    assert response.status_code == 404
