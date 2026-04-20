import time

from app.images import service as image_service
from app.images.schemas import ImageListParams


def test_list_images_happy_path(
    db_session,
    fake_storage,
    editor_user,
    seeded_person,
    seeded_place,
    seeded_event,
):
    """End-to-end service-layer check: the Cypher has never been run against
    a real database before this test. Three images are created and one is
    decorated with all three association types (tag, event, place). We then
    assert:

      - DESC sort order (newest uploaded first)
      - full aggregation shape on the decorated image
      - empty-list / None on the untagged images (the null-gotcha paths)
      - next_cursor is None when results fit inside page_size
    """
    # 2ms sleeps guarantee distinct uploaded_at values so the sort is
    # deterministic. Neo4j's timestamp() has ms resolution; without the gap,
    # two images created back-to-back would share a timestamp and order
    # would depend on the uid tiebreaker, which we don't control here.
    img_a = image_service.create_image(
        db_session, editor_user["uid"], "a.jpg", b"a", "image/jpeg"
    )
    time.sleep(0.002)
    img_b = image_service.create_image(
        db_session, editor_user["uid"], "b.jpg", b"b", "image/jpeg"
    )
    time.sleep(0.002)
    img_c = image_service.create_image(
        db_session, editor_user["uid"], "c.jpg", b"c", "image/jpeg"
    )

    image_service.add_tag(
        db_session, img_b["uid"], seeded_person["uid"], tag_x=50.0, tag_y=50.0
    )
    image_service.set_event(db_session, img_b["uid"], seeded_event["uid"])
    image_service.set_place(db_session, img_b["uid"], seeded_place["uid"])

    result = image_service.list_images(db_session, ImageListParams())

    assert [item.uid for item in result.items] == [
        img_c["uid"],
        img_b["uid"],
        img_a["uid"],
    ]
    assert result.next_cursor is None

    # Decorated image: every aggregation path populated.
    decorated = result.items[1]
    assert len(decorated.tags) == 1
    assert decorated.tags[0].person_uid == seeded_person["uid"]
    assert decorated.tags[0].person_name == seeded_person["name"]
    assert decorated.event is not None
    assert decorated.event.event_uid == seeded_event["uid"]
    assert decorated.event.event_name == seeded_event["name"]
    assert decorated.place is not None
    assert decorated.place.place_uid == seeded_place["uid"]
    assert decorated.place.place_name == seeded_place["name"]

    # Untagged image: this is where a broken null-in-collect or a missing
    # CASE would surface as a [{uid: null}] ghost entry or a {uid: null}
    # pseudo-map. Must be empty list and None.
    untagged = result.items[0]
    assert untagged.tags == []
    assert untagged.event is None
    assert untagged.place is None


# --- HTTP-level tests via the router ---
#
# The service-layer test above proves the Cypher and Python wrapper are
# correct. These tests prove the router wiring: auth, query-param binding,
# HTTP error translation, and that the response survives JSON serialization.


async def test_list_endpoint_happy_path(
    client, db_session, fake_storage, editor_user, seeded_person
):
    """Round-trip through HTTP: the JSON must contain tags/event/place
    fields and nulls must come through as JSON null (not missing keys)."""
    img = image_service.create_image(
        db_session, editor_user["uid"], "test.jpg", b"bytes", "image/jpeg"
    )
    image_service.add_tag(
        db_session, img["uid"], seeded_person["uid"], tag_x=50.0, tag_y=50.0
    )

    response = await client.get(
        "/api/images/",
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["uid"] == img["uid"]
    assert len(item["tags"]) == 1
    assert item["tags"][0]["person_uid"] == seeded_person["uid"]
    assert item["event"] is None
    assert item["place"] is None
    assert body["next_cursor"] is None


async def test_list_endpoint_requires_auth(client):
    """No Authorization header → 401 from OAuth2PasswordBearer."""
    response = await client.get("/api/images/")
    assert response.status_code == 401


async def test_list_endpoint_viewer_allowed(
    client, db_session, fake_storage, editor_user, viewer_token
):
    """RBAC: a viewer-role token must be accepted — the list endpoint is
    read-only and all authenticated roles can access it."""
    image_service.create_image(
        db_session, editor_user["uid"], "test.jpg", b"bytes", "image/jpeg"
    )

    response = await client.get(
        "/api/images/",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 200


async def test_list_endpoint_bad_cursor_returns_400(client, editor_token):
    """Malformed cursor → decode_cursor raises ValueError → router
    translates to 400. This is the contract the cursor unit tests pin."""
    response = await client.get(
        "/api/images/?cursor=!!!not-a-cursor!!!",
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert response.status_code == 400


async def test_list_endpoint_invalid_page_size_returns_422(client, editor_token):
    """Pydantic's Field(ge=1, le=200) on page_size must fire at the
    validation layer, before the handler runs. FastAPI returns 422."""
    response = await client.get(
        "/api/images/?page_size=0",
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert response.status_code == 422

    response = await client.get(
        "/api/images/?page_size=500",
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert response.status_code == 422


async def test_list_endpoint_empty_result(client, editor_token):
    """No images in DB → empty list, null cursor. Verifies the endpoint
    doesn't explode on the zero-row path."""
    response = await client.get(
        "/api/images/",
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["next_cursor"] is None


async def test_list_endpoint_filter_by_person(
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
        f"/api/images/?person_uid={seeded_person['uid']}",
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 200
    uids = [item["uid"] for item in response.json()["items"]]
    assert uids == [img_tagged["uid"]]


async def test_list_endpoint_filter_by_event(
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
        f"/api/images/?event_uid={seeded_event['uid']}",
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 200
    uids = [item["uid"] for item in response.json()["items"]]
    assert uids == [img_linked["uid"]]


async def test_list_endpoint_filter_by_place(
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
        f"/api/images/?place_uid={seeded_place['uid']}",
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 200
    uids = [item["uid"] for item in response.json()["items"]]
    assert uids == [img_linked["uid"]]


async def test_list_endpoint_combined_filters_are_anded(
    client, db_session, fake_storage, editor_user, seeded_person, seeded_event
):
    """Three images, each with a different subset of (person, event). Only
    the one with *both* should come back when filtering by both."""
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
        f"/api/images/?person_uid={seeded_person['uid']}"
        f"&event_uid={seeded_event['uid']}",
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 200
    uids = [item["uid"] for item in response.json()["items"]]
    assert uids == [img_both["uid"]]


async def test_list_endpoint_cursor_pagination(
    client, db_session, fake_storage, editor_user
):
    """Three images with distinct timestamps, page_size=2. Page 1 returns
    2 items with a next_cursor; page 2 returns the remaining 1 with no
    cursor. Together they cover all three with no overlap or skip — this
    is the whole point of cursor pagination."""
    img_a = image_service.create_image(
        db_session, editor_user["uid"], "a.jpg", b"a", "image/jpeg"
    )
    time.sleep(0.002)
    img_b = image_service.create_image(
        db_session, editor_user["uid"], "b.jpg", b"b", "image/jpeg"
    )
    time.sleep(0.002)
    img_c = image_service.create_image(
        db_session, editor_user["uid"], "c.jpg", b"c", "image/jpeg"
    )

    headers = {"Authorization": f"Bearer {editor_user['token']}"}

    response = await client.get("/api/images/?page_size=2", headers=headers)
    assert response.status_code == 200
    page1 = response.json()
    assert [item["uid"] for item in page1["items"]] == [img_c["uid"], img_b["uid"]]
    assert page1["next_cursor"] is not None

    response = await client.get(
        f"/api/images/?page_size=2&cursor={page1['next_cursor']}",
        headers=headers,
    )
    assert response.status_code == 200
    page2 = response.json()
    assert [item["uid"] for item in page2["items"]] == [img_a["uid"]]
    assert page2["next_cursor"] is None
