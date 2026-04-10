async def test_create_place_with_coordinates(client, editor_token):
    response = await client.post(
        "/api/places/",
        json={
            "name": "Grandma's house",
            "address": "123 Main St",
            "latitude": 59.3293,
            "longitude": 18.0686,
        },
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Grandma's house"
    assert body["latitude"] == 59.3293
    assert body["longitude"] == 18.0686


async def test_create_place_invalid_latitude(client, editor_token):
    response = await client.post(
        "/api/places/",
        json={"name": "Nowhere", "latitude": 200.0},
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 422


async def test_create_place_invalid_longitude(client, editor_token):
    response = await client.post(
        "/api/places/",
        json={"name": "Nowhere", "longitude": 500.0},
        headers={"Authorization": f"Bearer {editor_token}"},
    )

    assert response.status_code == 422


async def test_list_places(client, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    await client.post("/api/places/", json={"name": "Place A"}, headers=headers)
    await client.post("/api/places/", json={"name": "Place B"}, headers=headers)

    response = await client.get("/api/places/", headers=headers)

    assert response.status_code == 200
    names = [p["name"] for p in response.json()]
    assert set(names) == {"Place A", "Place B"}


async def test_update_place(client, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    create_resp = await client.post(
        "/api/places/",
        json={"name": "Old Place"},
        headers=headers,
    )
    uid = create_resp.json()["uid"]

    response = await client.put(
        f"/api/places/{uid}",
        json={"name": "New Place"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["name"] == "New Place"
