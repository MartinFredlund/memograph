from app.events.schemas import EventCreate
from app.events.service import create_event
from app.people.schemas import PersonCreate
from app.people.service import create_person
from app.places.schemas import PlaceCreate
from app.places.service import create_place


async def test_search_person_by_name(client, db_session, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    create_person(db_session, PersonCreate(name="Alice Johnson"))

    response = await client.get("/api/search/?q=Alice", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 1
    assert body[0]["name"] == "Alice Johnson"
    assert body[0]["type"] == "person"
    assert "score" in body[0]


async def test_search_across_types(client, db_session, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    create_person(db_session, PersonCreate(name="Summer Smith"))
    create_event(db_session, EventCreate(name="Summer Festival"))
    create_place(db_session, PlaceCreate(name="Summer Beach"))

    response = await client.get("/api/search/?q=Summer", headers=headers)

    assert response.status_code == 200
    body = response.json()
    types = {item["type"] for item in body}
    assert types == {"person", "event", "place"}


async def test_search_partial_match(client, db_session, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    create_person(db_session, PersonCreate(name="Christopher"))

    response = await client.get("/api/search/?q=Chris", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 1
    assert body[0]["name"] == "Christopher"


async def test_search_empty_query(client, editor_token):
    response = await client.get(
        "/api/search/?q=", headers={"Authorization": f"Bearer {editor_token}"}
    )

    assert response.status_code == 200
    assert response.json() == []


async def test_search_no_matches(client, db_session, editor_token):
    create_person(db_session, PersonCreate(name="Alice"))

    response = await client.get(
        "/api/search/?q=Zzzznotfound",
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 200
    assert response.json() == []


async def test_search_unauthenticated(client):
    response = await client.get("/api/search/?q=test")

    assert response.status_code == 401
