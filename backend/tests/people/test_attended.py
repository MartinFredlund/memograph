from uuid import uuid4

from app.events.schemas import EventCreate
from app.events.service import create_event
from app.people.schemas import PersonCreate
from app.people.service import create_person


async def test_add_attended_happy_path(client, db_session, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    person = create_person(db_session, PersonCreate(name="Alice"))
    event = create_event(db_session, EventCreate(name="Christmas 2024"))

    response = await client.post(
        f"/api/people/{person['uid']}/attended",
        json={"event_uid": event["uid"]},
        headers=headers,
    )

    assert response.status_code == 201

    record = db_session.run(
        """
        MATCH (p:Person {uid: $person_uid})-[:ATTENDED]->(e:Event)
        RETURN e.uid AS event_uid
        """,
        person_uid=person["uid"],
    ).single()
    assert record is not None
    assert record["event_uid"] == event["uid"]


async def test_add_attended_multiple_events(client, db_session, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    person = create_person(db_session, PersonCreate(name="Bob"))
    event1 = create_event(db_session, EventCreate(name="Christmas 2024"))
    event2 = create_event(db_session, EventCreate(name="New Year 2025"))

    await client.post(
        f"/api/people/{person['uid']}/attended",
        json={"event_uid": event1["uid"]},
        headers=headers,
    )
    await client.post(
        f"/api/people/{person['uid']}/attended",
        json={"event_uid": event2["uid"]},
        headers=headers,
    )

    records = db_session.run(
        """
        MATCH (p:Person {uid: $person_uid})-[:ATTENDED]->(e:Event)
        RETURN e.uid AS event_uid
        """,
        person_uid=person["uid"],
    ).data()
    assert len(records) == 2
    uids = {r["event_uid"] for r in records}
    assert uids == {event1["uid"], event2["uid"]}


async def test_add_attended_is_idempotent(client, db_session, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    person = create_person(db_session, PersonCreate(name="Carol"))
    event = create_event(db_session, EventCreate(name="Wedding"))

    await client.post(
        f"/api/people/{person['uid']}/attended",
        json={"event_uid": event["uid"]},
        headers=headers,
    )
    await client.post(
        f"/api/people/{person['uid']}/attended",
        json={"event_uid": event["uid"]},
        headers=headers,
    )

    records = db_session.run(
        """
        MATCH (p:Person {uid: $person_uid})-[:ATTENDED]->(e:Event)
        RETURN e.uid AS event_uid
        """,
        person_uid=person["uid"],
    ).data()
    assert len(records) == 1


async def test_add_attended_person_not_found(client, editor_token):
    response = await client.post(
        f"/api/people/{uuid4()}/attended",
        json={"event_uid": str(uuid4())},
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Person not found"


async def test_add_attended_event_not_found(client, db_session, editor_token):
    person = create_person(db_session, PersonCreate(name="Dave"))

    response = await client.post(
        f"/api/people/{person['uid']}/attended",
        json={"event_uid": str(uuid4())},
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"


async def test_add_attended_viewer_forbidden(client, db_session, viewer_token):
    person = create_person(db_session, PersonCreate(name="Eve"))
    event = create_event(db_session, EventCreate(name="Birthday"))

    response = await client.post(
        f"/api/people/{person['uid']}/attended",
        json={"event_uid": event["uid"]},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 403


async def test_remove_attended_happy_path(client, db_session, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    person = create_person(db_session, PersonCreate(name="Frank"))
    event = create_event(db_session, EventCreate(name="Concert"))

    db_session.run(
        """
        MATCH (p:Person {uid: $person_uid}), (e:Event {uid: $event_uid})
        CREATE (p)-[:ATTENDED]->(e)
        """,
        person_uid=person["uid"],
        event_uid=event["uid"],
    )

    response = await client.delete(
        f"/api/people/{person['uid']}/attended/{event['uid']}",
        headers=headers,
    )

    assert response.status_code == 204

    record = db_session.run(
        """
        MATCH (p:Person {uid: $person_uid})-[r:ATTENDED]->(:Event)
        RETURN r
        """,
        person_uid=person["uid"],
    ).single()
    assert record is None


async def test_remove_attended_is_idempotent(client, db_session, editor_token):
    person = create_person(db_session, PersonCreate(name="Grace"))
    event = create_event(db_session, EventCreate(name="Gala"))

    response = await client.delete(
        f"/api/people/{person['uid']}/attended/{event['uid']}",
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 204


async def test_remove_attended_person_not_found(client, editor_token):
    response = await client.delete(
        f"/api/people/{uuid4()}/attended/{uuid4()}",
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Person not found"


async def test_remove_attended_event_not_found(client, db_session, editor_token):
    person = create_person(db_session, PersonCreate(name="Hank"))

    response = await client.delete(
        f"/api/people/{person['uid']}/attended/{uuid4()}",
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"


async def test_remove_attended_viewer_forbidden(client, db_session, viewer_token):
    person = create_person(db_session, PersonCreate(name="Iris"))
    event = create_event(db_session, EventCreate(name="Party"))

    response = await client.delete(
        f"/api/people/{person['uid']}/attended/{event['uid']}",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 403
