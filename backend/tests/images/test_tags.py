from uuid import uuid4


async def test_add_tag_happy_path(
    client, seeded_image, seeded_person, editor_user, db_session
):
    response = await client.post(
        f"/api/images/{seeded_image['uid']}/tags",
        json={"person_uid": seeded_person["uid"], "tag_x": 42.5, "tag_y": 60.0},
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body == {
        "person_uid": seeded_person["uid"],
        "person_name": seeded_person["name"],
        "tag_x": 42.5,
        "tag_y": 60.0,
    }

    record = db_session.run(
        """
        MATCH (p:Person {uid: $person_uid})-[r:APPEARS_IN]->(i:Image {uid: $image_uid})
        RETURN r.tag_x AS tag_x, r.tag_y AS tag_y
        """,
        person_uid=seeded_person["uid"],
        image_uid=seeded_image["uid"],
    ).single()
    assert record is not None
    assert record["tag_x"] == 42.5
    assert record["tag_y"] == 60.0


async def test_add_tag_is_idempotent(
    client, seeded_image, seeded_person, editor_user, db_session
):
    """Re-tagging the same person on the same image updates coords, does not
    create a duplicate APPEARS_IN edge. MERGE semantics."""
    url = f"/api/images/{seeded_image['uid']}/tags"
    headers = {"Authorization": f"Bearer {editor_user['token']}"}

    first = await client.post(
        url,
        json={"person_uid": seeded_person["uid"], "tag_x": 10.0, "tag_y": 20.0},
        headers=headers,
    )
    assert first.status_code == 201

    second = await client.post(
        url,
        json={"person_uid": seeded_person["uid"], "tag_x": 80.0, "tag_y": 90.0},
        headers=headers,
    )
    assert second.status_code == 201
    assert second.json()["tag_x"] == 80.0
    assert second.json()["tag_y"] == 90.0

    count = db_session.run(
        """
        MATCH (p:Person {uid: $person_uid})-[r:APPEARS_IN]->(i:Image {uid: $image_uid})
        RETURN count(r) AS n
        """,
        person_uid=seeded_person["uid"],
        image_uid=seeded_image["uid"],
    ).single()["n"]
    assert count == 1


async def test_add_tag_image_not_found(client, seeded_person, editor_user):
    response = await client.post(
        f"/api/images/{uuid4()}/tags",
        json={"person_uid": seeded_person["uid"], "tag_x": 10.0, "tag_y": 20.0},
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Image not found"


async def test_add_tag_person_not_found(client, seeded_image, editor_user):
    response = await client.post(
        f"/api/images/{seeded_image['uid']}/tags",
        json={"person_uid": str(uuid4()), "tag_x": 10.0, "tag_y": 20.0},
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Person not found"


async def test_add_tag_viewer_forbidden(
    client, seeded_image, seeded_person, viewer_token
):
    response = await client.post(
        f"/api/images/{seeded_image['uid']}/tags",
        json={"person_uid": seeded_person["uid"], "tag_x": 10.0, "tag_y": 20.0},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 403


async def test_add_tag_rejects_out_of_range_coords(
    client, seeded_image, seeded_person, editor_user
):
    response = await client.post(
        f"/api/images/{seeded_image['uid']}/tags",
        json={"person_uid": seeded_person["uid"], "tag_x": 150.0, "tag_y": 20.0},
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 422


async def test_remove_tag_happy_path(
    client, seeded_image, seeded_person, editor_user, db_session
):
    db_session.run(
        """
        MATCH (p:Person {uid: $person_uid}), (i:Image {uid: $image_uid})
        CREATE (p)-[:APPEARS_IN {tag_x: 10.0, tag_y: 20.0}]->(i)
        """,
        person_uid=seeded_person["uid"],
        image_uid=seeded_image["uid"],
    )

    response = await client.delete(
        f"/api/images/{seeded_image['uid']}/tags/{seeded_person['uid']}",
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 204

    record = db_session.run(
        """
        MATCH (p:Person {uid: $person_uid})-[r:APPEARS_IN]->(i:Image {uid: $image_uid})
        RETURN r
        """,
        person_uid=seeded_person["uid"],
        image_uid=seeded_image["uid"],
    ).single()
    assert record is None


async def test_remove_tag_is_idempotent(
    client, seeded_image, seeded_person, editor_user
):
    """Deleting a non-existent tag returns 204 — matches the MERGE-based add."""
    response = await client.delete(
        f"/api/images/{seeded_image['uid']}/tags/{seeded_person['uid']}",
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 204


async def test_remove_tag_image_not_found(client, seeded_person, editor_user):
    response = await client.delete(
        f"/api/images/{uuid4()}/tags/{seeded_person['uid']}",
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Image not found"


async def test_remove_tag_person_not_found(client, seeded_image, editor_user):
    response = await client.delete(
        f"/api/images/{seeded_image['uid']}/tags/{uuid4()}",
        headers={"Authorization": f"Bearer {editor_user['token']}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Person not found"


async def test_remove_tag_viewer_forbidden(
    client, seeded_image, seeded_person, viewer_token
):
    response = await client.delete(
        f"/api/images/{seeded_image['uid']}/tags/{seeded_person['uid']}",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 403
