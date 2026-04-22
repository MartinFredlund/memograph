from uuid import uuid4

from app.events.schemas import EventCreate
from app.events.service import create_event
from app.people.schemas import PersonCreate
from app.people.service import create_person


async def test_explicit_event(client, db_session, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    person = create_person(db_session, PersonCreate(name="Alice"))
    event = create_event(db_session, EventCreate(name="Christmas 2024"))

    db_session.run(
        """
        MATCH (p:Person {uid: $person_uid}), (e:Event {uid: $event_uid})
        CREATE (p)-[:ATTENDED]->(e)
        """,
        person_uid=person["uid"],
        event_uid=event["uid"],
    )

    response = await client.get(
        f"/api/people/{person['uid']}/events", headers=headers
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["uid"] == event["uid"]
    assert body[0]["name"] == "Christmas 2024"
    assert body[0]["explicit"] is True
    assert body[0]["derived"] is False


async def test_derived_event(client, db_session, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    person = create_person(db_session, PersonCreate(name="Bob"))
    event = create_event(db_session, EventCreate(name="Birthday Party"))

    db_session.run(
        """
        MATCH (p:Person {uid: $person_uid})
        CREATE (i:Image {uid: $image_uid, filename: 'test.jpg',
                object_key: 'test-key', content_type: 'image/jpeg',
                size_bytes: 1024, uploaded_at: timestamp()})
        CREATE (p)-[:APPEARS_IN]->(i)
        WITH i
        MATCH (e:Event {uid: $event_uid})
        CREATE (i)-[:FROM_EVENT]->(e)
        """,
        person_uid=person["uid"],
        image_uid=str(uuid4()),
        event_uid=event["uid"],
    )

    response = await client.get(
        f"/api/people/{person['uid']}/events", headers=headers
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["uid"] == event["uid"]
    assert body[0]["explicit"] is False
    assert body[0]["derived"] is True


async def test_both_explicit_and_derived(client, db_session, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    person = create_person(db_session, PersonCreate(name="Carol"))
    event = create_event(db_session, EventCreate(name="Wedding"))

    db_session.run(
        """
        MATCH (p:Person {uid: $person_uid}), (e:Event {uid: $event_uid})
        CREATE (p)-[:ATTENDED]->(e)
        CREATE (i:Image {uid: $image_uid, filename: 'wedding.jpg',
                object_key: 'wedding-key', content_type: 'image/jpeg',
                size_bytes: 2048, uploaded_at: timestamp()})
        CREATE (p)-[:APPEARS_IN]->(i)
        CREATE (i)-[:FROM_EVENT]->(e)
        """,
        person_uid=person["uid"],
        event_uid=event["uid"],
        image_uid=str(uuid4()),
    )

    response = await client.get(
        f"/api/people/{person['uid']}/events", headers=headers
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["uid"] == event["uid"]
    assert body[0]["explicit"] is True
    assert body[0]["derived"] is True


async def test_no_events_returns_empty_list(client, db_session, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    person = create_person(db_session, PersonCreate(name="Dave"))

    response = await client.get(
        f"/api/people/{person['uid']}/events", headers=headers
    )

    assert response.status_code == 200
    assert response.json() == []


async def test_nonexistent_person_returns_empty_list(client, editor_token):
    response = await client.get(
        f"/api/people/{uuid4()}/events",
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 200
    assert response.json() == []
