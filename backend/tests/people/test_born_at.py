from uuid import uuid4

from app.people.schemas import PersonCreate
from app.people.service import create_person
from app.places.schemas import PlaceCreate
from app.places.service import create_place


async def test_set_born_at_happy_path(client, db_session, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    person = create_person(db_session, PersonCreate(name="Alice"))
    place = create_place(db_session, PlaceCreate(name="Stockholm"))

    response = await client.put(
        f"/api/people/{person['uid']}/born-at",
        json={"place_uid": place["uid"]},
        headers=headers,
    )

    assert response.status_code == 204

    record = db_session.run(
        """
        MATCH (p:Person {uid: $person_uid})-[:BORN_AT]->(pl:Place)
        RETURN pl.uid AS place_uid
        """,
        person_uid=person["uid"],
    ).single()
    assert record is not None
    assert record["place_uid"] == place["uid"]


async def test_set_born_at_replaces_existing(client, db_session, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    person = create_person(db_session, PersonCreate(name="Bob"))
    place1 = create_place(db_session, PlaceCreate(name="Stockholm"))
    place2 = create_place(db_session, PlaceCreate(name="Gothenburg"))

    await client.put(
        f"/api/people/{person['uid']}/born-at",
        json={"place_uid": place1["uid"]},
        headers=headers,
    )
    await client.put(
        f"/api/people/{person['uid']}/born-at",
        json={"place_uid": place2["uid"]},
        headers=headers,
    )

    records = db_session.run(
        """
        MATCH (p:Person {uid: $person_uid})-[:BORN_AT]->(pl:Place)
        RETURN pl.uid AS place_uid
        """,
        person_uid=person["uid"],
    ).data()
    assert len(records) == 1
    assert records[0]["place_uid"] == place2["uid"]


async def test_set_born_at_person_not_found(client, editor_token):
    place = None
    response = await client.put(
        f"/api/people/{uuid4()}/born-at",
        json={"place_uid": str(uuid4())},
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Person not found"


async def test_set_born_at_place_not_found(client, db_session, editor_token):
    person = create_person(db_session, PersonCreate(name="Carol"))

    response = await client.put(
        f"/api/people/{person['uid']}/born-at",
        json={"place_uid": str(uuid4())},
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Place not found"


async def test_set_born_at_viewer_forbidden(client, db_session, viewer_token):
    person = create_person(db_session, PersonCreate(name="Dave"))
    place = create_place(db_session, PlaceCreate(name="Malmö"))

    response = await client.put(
        f"/api/people/{person['uid']}/born-at",
        json={"place_uid": place["uid"]},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 403


async def test_unset_born_at_happy_path(client, db_session, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    person = create_person(db_session, PersonCreate(name="Eve"))
    place = create_place(db_session, PlaceCreate(name="Uppsala"))

    db_session.run(
        """
        MATCH (p:Person {uid: $person_uid}), (pl:Place {uid: $place_uid})
        CREATE (p)-[:BORN_AT]->(pl)
        """,
        person_uid=person["uid"],
        place_uid=place["uid"],
    )

    response = await client.delete(
        f"/api/people/{person['uid']}/born-at", headers=headers
    )

    assert response.status_code == 204

    record = db_session.run(
        """
        MATCH (p:Person {uid: $person_uid})-[r:BORN_AT]->(:Place)
        RETURN r
        """,
        person_uid=person["uid"],
    ).single()
    assert record is None


async def test_unset_born_at_is_idempotent(client, db_session, editor_token):
    person = create_person(db_session, PersonCreate(name="Frank"))

    response = await client.delete(
        f"/api/people/{person['uid']}/born-at",
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 204


async def test_unset_born_at_person_not_found(client, editor_token):
    response = await client.delete(
        f"/api/people/{uuid4()}/born-at",
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Person not found"


async def test_unset_born_at_viewer_forbidden(client, db_session, viewer_token):
    person = create_person(db_session, PersonCreate(name="Grace"))

    response = await client.delete(
        f"/api/people/{person['uid']}/born-at",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 403
