from uuid import uuid4

from app.events.schemas import EventCreate
from app.events.service import create_event
from app.places.schemas import PlaceCreate
from app.places.service import create_place


async def test_set_held_at_happy_path(client, db_session, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    event = create_event(db_session, EventCreate(name="Christmas 2024"))
    place = create_place(db_session, PlaceCreate(name="Stockholm"))

    response = await client.put(
        f"/api/events/{event['uid']}/place",
        json={"place_uid": place["uid"]},
        headers=headers,
    )

    assert response.status_code == 204

    record = db_session.run(
        """
        MATCH (e:Event {uid: $event_uid})-[:HELD_AT]->(pl:Place)
        RETURN pl.uid AS place_uid
        """,
        event_uid=event["uid"],
    ).single()
    assert record is not None
    assert record["place_uid"] == place["uid"]


async def test_set_held_at_replaces_existing(client, db_session, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    event = create_event(db_session, EventCreate(name="Wedding"))
    place1 = create_place(db_session, PlaceCreate(name="Church"))
    place2 = create_place(db_session, PlaceCreate(name="City Hall"))

    await client.put(
        f"/api/events/{event['uid']}/place",
        json={"place_uid": place1["uid"]},
        headers=headers,
    )
    await client.put(
        f"/api/events/{event['uid']}/place",
        json={"place_uid": place2["uid"]},
        headers=headers,
    )

    records = db_session.run(
        """
        MATCH (e:Event {uid: $event_uid})-[:HELD_AT]->(pl:Place)
        RETURN pl.uid AS place_uid
        """,
        event_uid=event["uid"],
    ).data()
    assert len(records) == 1
    assert records[0]["place_uid"] == place2["uid"]


async def test_set_held_at_event_not_found(client, editor_token):
    response = await client.put(
        f"/api/events/{uuid4()}/place",
        json={"place_uid": str(uuid4())},
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"


async def test_set_held_at_place_not_found(client, db_session, editor_token):
    event = create_event(db_session, EventCreate(name="Birthday"))

    response = await client.put(
        f"/api/events/{event['uid']}/place",
        json={"place_uid": str(uuid4())},
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Place not found"


async def test_set_held_at_viewer_forbidden(client, db_session, viewer_token):
    event = create_event(db_session, EventCreate(name="Concert"))
    place = create_place(db_session, PlaceCreate(name="Arena"))

    response = await client.put(
        f"/api/events/{event['uid']}/place",
        json={"place_uid": place["uid"]},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 403


async def test_unset_held_at_happy_path(client, db_session, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    event = create_event(db_session, EventCreate(name="Festival"))
    place = create_place(db_session, PlaceCreate(name="Park"))

    db_session.run(
        """
        MATCH (e:Event {uid: $event_uid}), (pl:Place {uid: $place_uid})
        CREATE (e)-[:HELD_AT]->(pl)
        """,
        event_uid=event["uid"],
        place_uid=place["uid"],
    )

    response = await client.delete(
        f"/api/events/{event['uid']}/place", headers=headers
    )

    assert response.status_code == 204

    record = db_session.run(
        """
        MATCH (e:Event {uid: $event_uid})-[r:HELD_AT]->(:Place)
        RETURN r
        """,
        event_uid=event["uid"],
    ).single()
    assert record is None


async def test_unset_held_at_is_idempotent(client, db_session, editor_token):
    event = create_event(db_session, EventCreate(name="Gala"))

    response = await client.delete(
        f"/api/events/{event['uid']}/place",
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 204


async def test_unset_held_at_event_not_found(client, editor_token):
    response = await client.delete(
        f"/api/events/{uuid4()}/place",
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"


async def test_unset_held_at_viewer_forbidden(client, db_session, viewer_token):
    event = create_event(db_session, EventCreate(name="Party"))

    response = await client.delete(
        f"/api/events/{event['uid']}/place",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 403
