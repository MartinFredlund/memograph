from app.images import service as image_service


def test_get_image_details_happy_path(
    db_session,
    fake_storage,
    editor_user,
    seeded_person,
    seeded_place,
    seeded_event,
):
    """Service-layer: image with all associations returns full detail
    including tag coordinates (the key difference from the list endpoint)."""
    img = image_service.create_image(
        db_session, editor_user["uid"], "test.jpg", b"bytes", "image/jpeg"
    )
    image_service.add_tag(
        db_session, img["uid"], seeded_person["uid"], tag_x=25.5, tag_y=75.0
    )
    image_service.set_event(db_session, img["uid"], seeded_event["uid"])
    image_service.set_place(db_session, img["uid"], seeded_place["uid"])

    result = image_service.get_image_details(db_session, img["uid"])

    assert result is not None
    assert result.uid == img["uid"]
    assert result.filename == "test.jpg"

    assert len(result.tags) == 1
    tag = result.tags[0]
    assert tag.person_uid == seeded_person["uid"]
    assert tag.person_name == seeded_person["name"]
    assert tag.tag_x == 25.5
    assert tag.tag_y == 75.0

    assert result.event is not None
    assert result.event.event_uid == seeded_event["uid"]
    assert result.event.event_name == seeded_event["name"]

    assert result.place is not None
    assert result.place.place_uid == seeded_place["uid"]
    assert result.place.place_name == seeded_place["name"]


def test_get_image_details_no_associations(
    db_session, fake_storage, editor_user
):
    """An image with no tags, event, or place returns empty tags and nulls."""
    img = image_service.create_image(
        db_session, editor_user["uid"], "bare.jpg", b"bytes", "image/jpeg"
    )

    result = image_service.get_image_details(db_session, img["uid"])

    assert result is not None
    assert result.tags == []
    assert result.event is None
    assert result.place is None


def test_get_image_details_not_found(db_session):
    """Non-existent uid returns None."""
    result = image_service.get_image_details(db_session, "no-such-uid")
    assert result is None


# --- HTTP-level tests ---


async def test_detail_endpoint_happy_path(
    client, db_session, fake_storage, editor_user, seeded_person
):
    """Round-trip through HTTP: tag coordinates must appear in the JSON."""
    img = image_service.create_image(
        db_session, editor_user["uid"], "test.jpg", b"bytes", "image/jpeg"
    )
    image_service.add_tag(
        db_session, img["uid"], seeded_person["uid"], tag_x=10.0, tag_y=90.0
    )

    response = await client.get(
        f"/api/images/{img['uid']}",
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["uid"] == img["uid"]
    assert len(body["tags"]) == 1
    assert body["tags"][0]["tag_x"] == 10.0
    assert body["tags"][0]["tag_y"] == 90.0
    assert body["event"] is None
    assert body["place"] is None


async def test_detail_endpoint_not_found(client, editor_user):
    """Non-existent uid → 404."""
    response = await client.get(
        "/api/images/no-such-uid",
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )
    assert response.status_code == 404


async def test_detail_endpoint_requires_auth(client):
    """No Authorization header → 401."""
    response = await client.get("/api/images/some-uid")
    assert response.status_code == 401


async def test_detail_endpoint_viewer_allowed(
    client, db_session, fake_storage, editor_user, viewer_token
):
    """RBAC: viewer can read image details (read-only endpoint)."""
    img = image_service.create_image(
        db_session, editor_user["uid"], "test.jpg", b"bytes", "image/jpeg"
    )

    response = await client.get(
        f"/api/images/{img['uid']}",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 200
