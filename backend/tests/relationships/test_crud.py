async def _create_person(client, token: str, name: str) -> str:
    resp = await client.post(
        "/api/people/",
        json={"name": name},
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp.json()["uid"]


async def test_create_parent_of(client, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    parent_uid = await _create_person(client, editor_token, "Parent")
    child_uid = await _create_person(client, editor_token, "Child")

    response = await client.post(
        "/api/relationships",
        json={
            "from_uid": parent_uid,
            "to_uid": child_uid,
            "category": "PARENT_OF",
        },
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["category"] == "PARENT_OF"
    assert body["from_uid"] == parent_uid
    assert body["to_uid"] == child_uid


async def test_create_partner_of(client, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    a_uid = await _create_person(client, editor_token, "A")
    b_uid = await _create_person(client, editor_token, "B")

    response = await client.post(
        "/api/relationships",
        json={
            "from_uid": a_uid,
            "to_uid": b_uid,
            "category": "PARTNER_OF",
            "since": "2020-06-15",
        },
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["since"] == "2020-06-15"


async def test_create_social_with_type(client, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    a_uid = await _create_person(client, editor_token, "A")
    b_uid = await _create_person(client, editor_token, "B")

    response = await client.post(
        "/api/relationships",
        json={
            "from_uid": a_uid,
            "to_uid": b_uid,
            "category": "SOCIAL",
            "social_type": "colleague",
        },
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["social_type"] == "colleague"


async def test_create_social_without_type_fails(client, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    a_uid = await _create_person(client, editor_token, "A")
    b_uid = await _create_person(client, editor_token, "B")

    response = await client.post(
        "/api/relationships",
        json={
            "from_uid": a_uid,
            "to_uid": b_uid,
            "category": "SOCIAL",
        },
        headers=headers,
    )

    assert response.status_code == 422


async def test_list_relationships_for_person(client, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    parent = await _create_person(client, editor_token, "Parent")
    child = await _create_person(client, editor_token, "Child")

    await client.post(
        "/api/relationships",
        json={"from_uid": parent, "to_uid": child, "category": "PARENT_OF"},
        headers=headers,
    )

    response = await client.get(
        f"/api/people/{parent}/relationships",
        headers=headers,
    )

    assert response.status_code == 200
    rels = response.json()
    assert len(rels) == 1
    assert rels[0]["category"] == "PARENT_OF"


async def test_update_relationship(client, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    a = await _create_person(client, editor_token, "A")
    b = await _create_person(client, editor_token, "B")

    create_resp = await client.post(
        "/api/relationships",
        json={"from_uid": a, "to_uid": b, "category": "PARTNER_OF"},
        headers=headers,
    )
    rel_uid = create_resp.json()["uid"]

    response = await client.put(
        f"/api/relationships/{rel_uid}",
        json={"since": "2015-04-01"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["since"] == "2015-04-01"


async def test_delete_relationship(client, editor_token):
    headers = {"Authorization": f"Bearer {editor_token}"}
    a = await _create_person(client, editor_token, "A")
    b = await _create_person(client, editor_token, "B")

    create_resp = await client.post(
        "/api/relationships",
        json={"from_uid": a, "to_uid": b, "category": "PARTNER_OF"},
        headers=headers,
    )
    rel_uid = create_resp.json()["uid"]

    response = await client.delete(
        f"/api/relationships/{rel_uid}",
        headers=headers,
    )

    assert response.status_code == 204
