from uuid import uuid4


async def test_create_person(client, editor_token):
    response = await client.post(
        "/api/people/",
        json={"name": "Alice Smith", "birth_date": "1990-01-15"},
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Alice Smith"
    assert body["birth_date"] == "1990-01-15"
    assert "uid" in body


async def test_get_person(client, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    create_resp = await client.post(
        "/api/people/", json={"name": "Alice Smith"}, headers=headers
    )
    uid = create_resp.json()["uid"]

    response = await client.get(f"/api/people/{uid}", headers=headers)

    assert response.status_code == 200
    assert response.json()["name"] == "Alice Smith"


async def test_get_person_not_found(client, editor_token):
    response = await client.get(
        f"/api/people/{uuid4()}",
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 404


async def test_list_people(client, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    await client.post("/api/people/", json={"name": "Alice"}, headers=headers)
    await client.post("/api/people/", json={"name": "Bob"}, headers=headers)

    response = await client.get("/api/people/", headers=headers)

    assert response.status_code == 200
    names = [p["name"] for p in response.json()]
    assert set(names) == {"Alice", "Bob"}


async def test_update_person_partial(client, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    create_resp = await client.post(
        "/api/people/",
        json={"name": "Alice", "nickname": "Ali"},
        headers=headers,
    )
    uid = create_resp.json()["uid"]

    response = await client.put(
        f"/api/people/{uid}",
        json={"nickname": "Allie"},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Alice"  # untouched
    assert body["nickname"] == "Allie"  # updated


async def test_viewer_cannot_create_person(client, viewer_token):
    response = await client.post(
        "/api/people/",
        json={"name": "Alice"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 403
