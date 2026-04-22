from uuid import uuid4

from app.people.schemas import PersonCreate
from app.people.service import create_person
from app.places.schemas import PlaceCreate
from app.places.service import create_place


async def test_visited_place_from_photo(client, db_session, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    person = create_person(db_session, PersonCreate(name="Alice"))
    place = create_place(db_session, PlaceCreate(name="Beach House"))

    db_session.run(
        """
        MATCH (p:Person {uid: $person_uid}), (pl:Place {uid: $place_uid})
        CREATE (i:Image {uid: $image_uid, filename: 'beach.jpg',
                object_key: 'beach-key', content_type: 'image/jpeg',
                size_bytes: 1024, uploaded_at: timestamp()})
        CREATE (p)-[:APPEARS_IN]->(i)
        CREATE (i)-[:TAKEN_AT]->(pl)
        """,
        person_uid=person["uid"],
        place_uid=place["uid"],
        image_uid=str(uuid4()),
    )

    response = await client.get(
        f"/api/people/{person['uid']}/places", headers=headers
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["uid"] == place["uid"]
    assert body[0]["name"] == "Beach House"


async def test_multiple_photos_same_place_deduplicates(client, db_session, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    person = create_person(db_session, PersonCreate(name="Bob"))
    place = create_place(db_session, PlaceCreate(name="Office"))

    db_session.run(
        """
        MATCH (p:Person {uid: $person_uid}), (pl:Place {uid: $place_uid})
        CREATE (i1:Image {uid: $img1, filename: 'a.jpg',
                object_key: 'a-key', content_type: 'image/jpeg',
                size_bytes: 1024, uploaded_at: timestamp()})
        CREATE (i2:Image {uid: $img2, filename: 'b.jpg',
                object_key: 'b-key', content_type: 'image/jpeg',
                size_bytes: 1024, uploaded_at: timestamp()})
        CREATE (p)-[:APPEARS_IN]->(i1)
        CREATE (p)-[:APPEARS_IN]->(i2)
        CREATE (i1)-[:TAKEN_AT]->(pl)
        CREATE (i2)-[:TAKEN_AT]->(pl)
        """,
        person_uid=person["uid"],
        place_uid=place["uid"],
        img1=str(uuid4()),
        img2=str(uuid4()),
    )

    response = await client.get(
        f"/api/people/{person['uid']}/places", headers=headers
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_no_places_returns_empty_list(client, db_session, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    person = create_person(db_session, PersonCreate(name="Carol"))

    response = await client.get(
        f"/api/people/{person['uid']}/places", headers=headers
    )

    assert response.status_code == 200
    assert response.json() == []


async def test_nonexistent_person_returns_empty_list(client, editor_token):
    response = await client.get(
        f"/api/people/{uuid4()}/places",
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 200
    assert response.json() == []
