from uuid import uuid4


async def test_set_place_happy_path(
    client, seeded_image, seeded_place, editor_user, db_session
):
    response = await client.put(
        f"/api/images/{seeded_image['uid']}/place",
        json={"place_uid": seeded_place["uid"]},
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 204

    record = db_session.run(
        """
        MATCH (i:Image {uid: $image_uid})-[:TAKEN_AT]->(p:Place)
        RETURN p.uid AS place_uid
        """,
        image_uid=seeded_image["uid"],
    ).single()
    assert record is not None
    assert record["place_uid"] == seeded_place["uid"]


async def test_set_place_replaces_existing(
    client,
    seeded_image,
    seeded_place,
    other_seeded_place,
    editor_user,
    db_session,
):
    """The 'exactly one TAKEN_AT per image' invariant: PUTting a new place
    must delete the previous one, not accumulate."""
    url = f"/api/images/{seeded_image['uid']}/place"
    headers = {"Authorization": f"Bearer {editor_user['token']}"}

    first = await client.put(
        url, json={"place_uid": seeded_place["uid"]}, headers=headers
    )
    assert first.status_code == 204

    second = await client.put(
        url, json={"place_uid": other_seeded_place["uid"]}, headers=headers
    )
    assert second.status_code == 204

    records = db_session.run(
        """
        MATCH (i:Image {uid: $image_uid})-[:TAKEN_AT]->(p:Place)
        RETURN p.uid AS place_uid
        """,
        image_uid=seeded_image["uid"],
    ).data()
    assert len(records) == 1
    assert records[0]["place_uid"] == other_seeded_place["uid"]


async def test_set_place_image_not_found(client, seeded_place, editor_user):
    response = await client.put(
        f"/api/images/{uuid4()}/place",
        json={"place_uid": seeded_place["uid"]},
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Image not found"


async def test_set_place_place_not_found(client, seeded_image, editor_user):
    response = await client.put(
        f"/api/images/{seeded_image['uid']}/place",
        json={"place_uid": str(uuid4())},
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Place not found"


async def test_set_place_viewer_forbidden(
    client, seeded_image, seeded_place, viewer_token
):
    response = await client.put(
        f"/api/images/{seeded_image['uid']}/place",
        json={"place_uid": seeded_place["uid"]},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 403


async def test_unset_place_happy_path(
    client, seeded_image, seeded_place, editor_user, db_session
):
    db_session.run(
        """
        MATCH (i:Image {uid: $image_uid}), (p:Place {uid: $place_uid})
        CREATE (i)-[:TAKEN_AT]->(p)
        """,
        image_uid=seeded_image["uid"],
        place_uid=seeded_place["uid"],
    )

    response = await client.delete(
        f"/api/images/{seeded_image['uid']}/place",
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 204

    record = db_session.run(
        """
        MATCH (i:Image {uid: $image_uid})-[r:TAKEN_AT]->(:Place)
        RETURN r
        """,
        image_uid=seeded_image["uid"],
    ).single()
    assert record is None


async def test_unset_place_is_idempotent(client, seeded_image, editor_user):
    """DELETE on an image with no place linked returns 204 — matches
    standard idempotent-delete semantics."""
    response = await client.delete(
        f"/api/images/{seeded_image['uid']}/place",
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 204


async def test_unset_place_image_not_found(client, editor_user):
    response = await client.delete(
        f"/api/images/{uuid4()}/place",
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Image not found"


async def test_unset_place_viewer_forbidden(client, seeded_image, viewer_token):
    response = await client.delete(
        f"/api/images/{seeded_image['uid']}/place",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 403


async def test_set_event_happy_path(
    client, seeded_image, seeded_event, editor_user, db_session
):
    response = await client.put(
        f"/api/images/{seeded_image['uid']}/event",
        json={"event_uid": seeded_event["uid"]},
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 204

    record = db_session.run(
        """
        MATCH (i:Image {uid: $image_uid})-[:FROM_EVENT]->(e:Event)
        RETURN e.uid AS event_uid
        """,
        image_uid=seeded_image["uid"],
    ).single()
    assert record is not None
    assert record["event_uid"] == seeded_event["uid"]


async def test_set_event_replaces_existing(
    client,
    seeded_image,
    seeded_event,
    other_seeded_event,
    editor_user,
    db_session,
):
    """The 'exactly one FROM_EVENT per image' invariant."""
    url = f"/api/images/{seeded_image['uid']}/event"
    headers = {"Authorization": f"Bearer {editor_user['token']}"}

    first = await client.put(
        url, json={"event_uid": seeded_event["uid"]}, headers=headers
    )
    assert first.status_code == 204

    second = await client.put(
        url, json={"event_uid": other_seeded_event["uid"]}, headers=headers
    )
    assert second.status_code == 204

    records = db_session.run(
        """
        MATCH (i:Image {uid: $image_uid})-[:FROM_EVENT]->(e:Event)
        RETURN e.uid AS event_uid
        """,
        image_uid=seeded_image["uid"],
    ).data()
    assert len(records) == 1
    assert records[0]["event_uid"] == other_seeded_event["uid"]


async def test_set_event_image_not_found(client, seeded_event, editor_user):
    response = await client.put(
        f"/api/images/{uuid4()}/event",
        json={"event_uid": seeded_event["uid"]},
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Image not found"


async def test_set_event_event_not_found(client, seeded_image, editor_user):
    response = await client.put(
        f"/api/images/{seeded_image['uid']}/event",
        json={"event_uid": str(uuid4())},
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"


async def test_set_event_viewer_forbidden(
    client, seeded_image, seeded_event, viewer_token
):
    response = await client.put(
        f"/api/images/{seeded_image['uid']}/event",
        json={"event_uid": seeded_event["uid"]},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 403


async def test_unset_event_happy_path(
    client, seeded_image, seeded_event, editor_user, db_session
):
    db_session.run(
        """
        MATCH (i:Image {uid: $image_uid}), (e:Event {uid: $event_uid})
        CREATE (i)-[:FROM_EVENT]->(e)
        """,
        image_uid=seeded_image["uid"],
        event_uid=seeded_event["uid"],
    )

    response = await client.delete(
        f"/api/images/{seeded_image['uid']}/event",
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 204

    record = db_session.run(
        """
        MATCH (i:Image {uid: $image_uid})-[r:FROM_EVENT]->(:Event)
        RETURN r
        """,
        image_uid=seeded_image["uid"],
    ).single()
    assert record is None


async def test_unset_event_is_idempotent(client, seeded_image, editor_user):
    response = await client.delete(
        f"/api/images/{seeded_image['uid']}/event",
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 204


async def test_unset_event_image_not_found(client, editor_user):
    response = await client.delete(
        f"/api/images/{uuid4()}/event",
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Image not found"


async def test_unset_event_viewer_forbidden(client, seeded_image, viewer_token):
    response = await client.delete(
        f"/api/images/{seeded_image['uid']}/event",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 403
