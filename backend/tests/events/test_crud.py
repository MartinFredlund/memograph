from uuid import uuid4


async def test_create_event_with_dates(client, editor_token):
    response = await client.post(
        "/api/events/",
        json={
            "name": "Christmas 2024",
            "start_date": "2024-12-24",
            "end_date": "2024-12-26",
            "description": "Family gathering",
        },
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Christmas 2024"
    assert body["start_date"] == "2024-12-24"
    assert body["end_date"] == "2024-12-26"


async def test_create_event_minimal(client, editor_token):
    response = await client.post(
        "/api/events/",
        json={"name": "Unnamed"},
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Unnamed"
    assert body["start_date"] is None
    assert body["end_date"] is None


async def test_get_event_not_found(client, editor_token):
    response = await client.get(
        f"/api/events/{uuid4()}",
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 404


async def test_list_events(client, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    await client.post("/api/events/", json={"name": "Event A"}, headers=headers)
    await client.post("/api/events/", json={"name": "Event B"}, headers=headers)

    response = await client.get("/api/events/", headers=headers)

    assert response.status_code == 200
    names = [e["name"] for e in response.json()]
    assert set(names) == {"Event A", "Event B"}


async def test_update_event(client, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    create_resp = await client.post(
        "/api/events/",
        json={"name": "Old Name"},
        headers=headers,
    )
    uid = create_resp.json()["uid"]

    response = await client.put(
        f"/api/events/{uid}",
        json={"name": "New Name", "description": "Updated"},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "New Name"
    assert body["description"] == "Updated"
