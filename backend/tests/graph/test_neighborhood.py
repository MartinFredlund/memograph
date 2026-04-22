from uuid import uuid4

from app.people.schemas import PersonCreate
from app.people.service import create_person


async def test_isolated_person(client, db_session, viewer_token):
    person = create_person(db_session, PersonCreate(name="Alice"))

    response = await client.get(
        f"/api/graph/neighborhood/{person['uid']}",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["nodes"]) == 1
    assert body["nodes"][0]["uid"] == person["uid"]
    assert body["nodes"][0]["type"] == "Person"
    assert body["nodes"][0]["name"] == "Alice"
    assert body["edges"] == []


async def test_person_not_found(client, viewer_token):
    response = await client.get(
        f"/api/graph/neighborhood/{uuid4()}",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 404


async def test_direct_connections_returned(client, db_session, viewer_token):
    alice = create_person(db_session, PersonCreate(name="Alice"))
    bob = create_person(db_session, PersonCreate(name="Bob"))
    db_session.run(
        "MATCH (a:Person {uid: $from}), (b:Person {uid: $to}) "
        "CREATE (a)-[:PARENT_OF]->(b)",
        {"from": alice["uid"], "to": bob["uid"]},
    )

    response = await client.get(
        f"/api/graph/neighborhood/{alice['uid']}",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 200
    body = response.json()
    uids = {n["uid"] for n in body["nodes"]}
    assert uids == {alice["uid"], bob["uid"]}
    assert len(body["edges"]) == 1
    assert body["edges"][0]["source"] == alice["uid"]
    assert body["edges"][0]["target"] == bob["uid"]
    assert body["edges"][0]["label"] == "PARENT_OF"


async def test_edges_between_neighbors_included(client, db_session, viewer_token):
    """Bob and Carol are both parents of Alice and partners of each other.
    Querying Alice's neighborhood should include the Bob-Carol PARTNER_OF edge."""
    alice = create_person(db_session, PersonCreate(name="Alice"))
    bob = create_person(db_session, PersonCreate(name="Bob"))
    carol = create_person(db_session, PersonCreate(name="Carol"))
    db_session.run(
        """
        MATCH (a:Person {uid: $alice}), (b:Person {uid: $bob}), (c:Person {uid: $carol})
        CREATE (b)-[:PARENT_OF]->(a)
        CREATE (c)-[:PARENT_OF]->(a)
        CREATE (b)-[:PARTNER_OF]->(c)
        """,
        {"alice": alice["uid"], "bob": bob["uid"], "carol": carol["uid"]},
    )

    response = await client.get(
        f"/api/graph/neighborhood/{alice['uid']}",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    body = response.json()
    uids = {n["uid"] for n in body["nodes"]}
    assert uids == {alice["uid"], bob["uid"], carol["uid"]}

    labels = {e["label"] for e in body["edges"]}
    assert "PARENT_OF" in labels
    assert "PARTNER_OF" in labels
    assert len(body["edges"]) == 3


async def test_social_edge_includes_social_type(client, db_session, viewer_token):
    alice = create_person(db_session, PersonCreate(name="Alice"))
    bob = create_person(db_session, PersonCreate(name="Bob"))
    db_session.run(
        "MATCH (a:Person {uid: $from}), (b:Person {uid: $to}) "
        "CREATE (a)-[:SOCIAL {type: 'friend'}]->(b)",
        {"from": alice["uid"], "to": bob["uid"]},
    )

    response = await client.get(
        f"/api/graph/neighborhood/{alice['uid']}",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    body = response.json()
    social_edges = [e for e in body["edges"] if e["label"] == "SOCIAL"]
    assert len(social_edges) == 1
    assert social_edges[0]["social_type"] == "friend"


async def test_excludes_non_person_relationships(client, db_session, viewer_token):
    """HELD_AT, BORN_AT etc. should not appear in the neighborhood graph."""
    alice = create_person(db_session, PersonCreate(name="Alice"))
    db_session.run(
        """
        MATCH (a:Person {uid: $uid})
        CREATE (pl:Place {uid: $place_uid, name: 'Stockholm'})
        CREATE (a)-[:BORN_AT]->(pl)
        """,
        {"uid": alice["uid"], "place_uid": str(uuid4())},
    )

    response = await client.get(
        f"/api/graph/neighborhood/{alice['uid']}",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    body = response.json()
    assert len(body["nodes"]) == 1
    assert body["nodes"][0]["type"] == "Person"
    assert body["edges"] == []


async def test_does_not_include_two_hop_neighbors(client, db_session, viewer_token):
    """Depth is 1 — friends of friends should not appear."""
    alice = create_person(db_session, PersonCreate(name="Alice"))
    bob = create_person(db_session, PersonCreate(name="Bob"))
    carol = create_person(db_session, PersonCreate(name="Carol"))
    db_session.run(
        """
        MATCH (a:Person {uid: $alice}), (b:Person {uid: $bob}), (c:Person {uid: $carol})
        CREATE (a)-[:SOCIAL {type: 'friend'}]->(b)
        CREATE (b)-[:SOCIAL {type: 'friend'}]->(c)
        """,
        {"alice": alice["uid"], "bob": bob["uid"], "carol": carol["uid"]},
    )

    response = await client.get(
        f"/api/graph/neighborhood/{alice['uid']}",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    body = response.json()
    uids = {n["uid"] for n in body["nodes"]}
    assert alice["uid"] in uids
    assert bob["uid"] in uids
    assert carol["uid"] not in uids


async def test_unauthenticated_returns_401(client):
    response = await client.get(f"/api/graph/neighborhood/{uuid4()}")

    assert response.status_code == 401
