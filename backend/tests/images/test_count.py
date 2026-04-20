from app.images import service as image_service

# HTTP-level tests for GET /api/images/count.
#
# Smaller surface area than the list endpoint: no cursor, no pagination,
# no aggregation — just a filtered count. That means the test matrix is
# cut down too (no 400-bad-cursor, no 422-bad-page-size, no multi-page).


async def test_count_endpoint_happy_path(
    client, db_session, fake_storage, editor_user
):
    """Three images, no filters → count == 3."""
    for name in ("a.jpg", "b.jpg", "c.jpg"):
        image_service.create_image(
            db_session, editor_user["uid"], name, b"bytes", "image/jpeg"
        )

    response = await client.get(
        "/api/images/count",
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 200
    assert response.json() == {"count": 3}


async def test_count_endpoint_empty(client, editor_token):
    """Zero images → count == 0. COUNT always returns one row with 0,
    never zero rows, so the handler must not confuse that with 'not found'."""
    response = await client.get(
        "/api/images/count",
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"count": 0}


async def test_count_endpoint_requires_auth(client):
    response = await client.get("/api/images/count")
    assert response.status_code == 401


async def test_count_endpoint_viewer_allowed(
    client, db_session, fake_storage, editor_user, viewer_token
):
    """RBAC: the count endpoint is read-only and must accept all roles."""
    image_service.create_image(
        db_session, editor_user["uid"], "a.jpg", b"a", "image/jpeg"
    )

    response = await client.get(
        "/api/images/count",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"count": 1}


async def test_count_endpoint_filter_by_person(
    client, db_session, fake_storage, editor_user, seeded_person
):
    img_tagged = image_service.create_image(
        db_session, editor_user["uid"], "a.jpg", b"a", "image/jpeg"
    )
    image_service.create_image(
        db_session, editor_user["uid"], "b.jpg", b"b", "image/jpeg"
    )
    image_service.add_tag(
        db_session, img_tagged["uid"], seeded_person["uid"], tag_x=50.0, tag_y=50.0
    )

    response = await client.get(
        f"/api/images/count?person_uid={seeded_person['uid']}",
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )
    assert response.status_code == 200
    assert response.json() == {"count": 1}


async def test_count_endpoint_filter_by_event(
    client, db_session, fake_storage, editor_user, seeded_event
):
    img_linked = image_service.create_image(
        db_session, editor_user["uid"], "a.jpg", b"a", "image/jpeg"
    )
    image_service.create_image(
        db_session, editor_user["uid"], "b.jpg", b"b", "image/jpeg"
    )
    image_service.set_event(db_session, img_linked["uid"], seeded_event["uid"])

    response = await client.get(
        f"/api/images/count?event_uid={seeded_event['uid']}",
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )
    assert response.status_code == 200
    assert response.json() == {"count": 1}


async def test_count_endpoint_filter_by_place(
    client, db_session, fake_storage, editor_user, seeded_place
):
    img_linked = image_service.create_image(
        db_session, editor_user["uid"], "a.jpg", b"a", "image/jpeg"
    )
    image_service.create_image(
        db_session, editor_user["uid"], "b.jpg", b"b", "image/jpeg"
    )
    image_service.set_place(db_session, img_linked["uid"], seeded_place["uid"])

    response = await client.get(
        f"/api/images/count?place_uid={seeded_place['uid']}",
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )
    assert response.status_code == 200
    assert response.json() == {"count": 1}


async def test_count_endpoint_combined_filters_are_anded(
    client, db_session, fake_storage, editor_user, seeded_person, seeded_event
):
    """Three images with different subsets of (person, event). Filtering
    by both uids must match only the image with both — proves AND, not OR."""
    img_both = image_service.create_image(
        db_session, editor_user["uid"], "a.jpg", b"a", "image/jpeg"
    )
    img_person_only = image_service.create_image(
        db_session, editor_user["uid"], "b.jpg", b"b", "image/jpeg"
    )
    img_event_only = image_service.create_image(
        db_session, editor_user["uid"], "c.jpg", b"c", "image/jpeg"
    )
    image_service.add_tag(
        db_session, img_both["uid"], seeded_person["uid"], tag_x=50.0, tag_y=50.0
    )
    image_service.set_event(db_session, img_both["uid"], seeded_event["uid"])
    image_service.add_tag(
        db_session,
        img_person_only["uid"],
        seeded_person["uid"],
        tag_x=50.0,
        tag_y=50.0,
    )
    image_service.set_event(db_session, img_event_only["uid"], seeded_event["uid"])

    response = await client.get(
        f"/api/images/count?person_uid={seeded_person['uid']}"
        f"&event_uid={seeded_event['uid']}",
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )
    assert response.status_code == 200
    assert response.json() == {"count": 1}
