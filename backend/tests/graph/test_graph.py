from uuid import uuid4

from app.people.schemas import PersonCreate
from app.people.service import create_person
from app.events.schemas import EventCreate
from app.events.service import create_event
from app.places.schemas import PlaceCreate
from app.places.service import create_place


async def test_empty_graph(client, viewer_token):
    response = await client.get(
        "/api/graph/",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body == {"nodes": [], "edges": []}


async def test_nodes_include_all_entity_types(client, db_session, viewer_token):
    create_person(db_session, PersonCreate(name="Alice"))
    create_event(db_session, EventCreate(name="Christmas 2024"))
    create_place(db_session, PlaceCreate(name="Grandma's House"))

    response = await client.get(
        "/api/graph/",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 200
    nodes = response.json()["nodes"]
    assert len(nodes) == 3

    types = {n["type"] for n in nodes}
    assert types == {"Person", "Event", "Place"}

    names = {n["name"] for n in nodes}
    assert names == {"Alice", "Christmas 2024", "Grandma's House"}

    for node in nodes:
        assert "uid" in node
        assert "type" in node
        assert "name" in node


async def test_nodes_sorted_by_type_then_name(client, db_session, viewer_token):
    create_person(db_session, PersonCreate(name="Zara"))
    create_person(db_session, PersonCreate(name="Alice"))
    create_event(db_session, EventCreate(name="Birthday"))

    response = await client.get(
        "/api/graph/",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    nodes = response.json()["nodes"]
    keys = [(n["type"], n["name"]) for n in nodes]
    assert keys == [("Event", "Birthday"), ("Person", "Alice"), ("Person", "Zara")]


async def test_plain_edges_parent_of(client, db_session, viewer_token):
    parent = create_person(db_session, PersonCreate(name="Parent"))
    child = create_person(db_session, PersonCreate(name="Child"))
    db_session.run(
        "MATCH (a:Person {uid: $from}), (b:Person {uid: $to}) "
        "CREATE (a)-[:PARENT_OF]->(b)",
        {"from": parent["uid"], "to": child["uid"]},
    )

    response = await client.get(
        "/api/graph/",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    edges = response.json()["edges"]
    assert len(edges) == 1
    edge = edges[0]
    assert edge["source"] == parent["uid"]
    assert edge["target"] == child["uid"]
    assert edge["label"] == "PARENT_OF"
    assert "id" in edge


async def test_plain_edges_no_duplicates(client, db_session, viewer_token):
    a = create_person(db_session, PersonCreate(name="A"))
    b = create_person(db_session, PersonCreate(name="B"))
    db_session.run(
        "MATCH (a:Person {uid: $from}), (b:Person {uid: $to}) "
        "CREATE (a)-[:PARTNER_OF]->(b)",
        {"from": a["uid"], "to": b["uid"]},
    )

    response = await client.get(
        "/api/graph/",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    edges = response.json()["edges"]
    partner_edges = [e for e in edges if e["label"] == "PARTNER_OF"]
    assert len(partner_edges) == 1


async def test_social_edge_includes_social_type(client, db_session, viewer_token):
    a = create_person(db_session, PersonCreate(name="A"))
    b = create_person(db_session, PersonCreate(name="B"))
    db_session.run(
        "MATCH (a:Person {uid: $from}), (b:Person {uid: $to}) "
        "CREATE (a)-[:SOCIAL {type: 'colleague'}]->(b)",
        {"from": a["uid"], "to": b["uid"]},
    )

    response = await client.get(
        "/api/graph/",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    edges = response.json()["edges"]
    social_edges = [e for e in edges if e["label"] == "SOCIAL"]
    assert len(social_edges) == 1
    assert social_edges[0]["social_type"] == "colleague"
    assert social_edges[0]["source"] == a["uid"]
    assert social_edges[0]["target"] == b["uid"]


async def test_explicit_attended_edge(client, db_session, viewer_token):
    person = create_person(db_session, PersonCreate(name="Alice"))
    event = create_event(db_session, EventCreate(name="Wedding"))
    db_session.run(
        "MATCH (p:Person {uid: $p_uid}), (e:Event {uid: $e_uid}) "
        "CREATE (p)-[:ATTENDED]->(e)",
        {"p_uid": person["uid"], "e_uid": event["uid"]},
    )

    response = await client.get(
        "/api/graph/",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    edges = response.json()["edges"]
    attended = [e for e in edges if e["label"] == "ATTENDED"]
    assert len(attended) == 1
    assert attended[0]["explicit"] is True
    assert attended[0]["derived"] is False
    assert attended[0]["source"] == person["uid"]
    assert attended[0]["target"] == event["uid"]


async def test_derived_attended_edge(client, db_session, viewer_token):
    person = create_person(db_session, PersonCreate(name="Alice"))
    event = create_event(db_session, EventCreate(name="Wedding"))
    db_session.run(
        """
        MATCH (p:Person {uid: $p_uid}), (e:Event {uid: $e_uid})
        CREATE (i:Image {uid: $i_uid, filename: 'test.jpg', object_key: 'test',
                         content_type: 'image/jpeg', size_bytes: 100,
                         uploaded_at: timestamp()})
        CREATE (p)-[:APPEARS_IN {tag_x: 50.0, tag_y: 50.0}]->(i)
        CREATE (i)-[:FROM_EVENT]->(e)
        """,
        {"p_uid": person["uid"], "e_uid": event["uid"], "i_uid": str(uuid4())},
    )

    response = await client.get(
        "/api/graph/",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    edges = response.json()["edges"]
    attended = [e for e in edges if e["label"] == "ATTENDED"]
    assert len(attended) == 1
    assert attended[0]["explicit"] is False
    assert attended[0]["derived"] is True
    assert attended[0]["id"].startswith("derived-")


async def test_attended_edge_both_explicit_and_derived(
    client, db_session, viewer_token
):
    person = create_person(db_session, PersonCreate(name="Alice"))
    event = create_event(db_session, EventCreate(name="Wedding"))
    db_session.run(
        """
        MATCH (p:Person {uid: $p_uid}), (e:Event {uid: $e_uid})
        CREATE (p)-[:ATTENDED]->(e)
        CREATE (i:Image {uid: $i_uid, filename: 'test.jpg', object_key: 'test',
                         content_type: 'image/jpeg', size_bytes: 100,
                         uploaded_at: timestamp()})
        CREATE (p)-[:APPEARS_IN {tag_x: 50.0, tag_y: 50.0}]->(i)
        CREATE (i)-[:FROM_EVENT]->(e)
        """,
        {"p_uid": person["uid"], "e_uid": event["uid"], "i_uid": str(uuid4())},
    )

    response = await client.get(
        "/api/graph/",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    edges = response.json()["edges"]
    attended = [e for e in edges if e["label"] == "ATTENDED"]
    assert len(attended) == 1
    assert attended[0]["explicit"] is True
    assert attended[0]["derived"] is True
    assert not attended[0]["id"].startswith("derived-")


async def test_cross_ref_edges(client, db_session, viewer_token):
    person = create_person(db_session, PersonCreate(name="Alice"))
    place = create_place(db_session, PlaceCreate(name="Stockholm"))
    event = create_event(db_session, EventCreate(name="Midsummer"))
    db_session.run(
        """
        MATCH (p:Person {uid: $p_uid}), (pl:Place {uid: $pl_uid}), (e:Event {uid: $e_uid})
        CREATE (p)-[:LIVES_AT]->(pl)
        CREATE (p)-[:BORN_AT]->(pl)
        CREATE (e)-[:HELD_AT]->(pl)
        """,
        {"p_uid": person["uid"], "pl_uid": place["uid"], "e_uid": event["uid"]},
    )

    response = await client.get(
        "/api/graph/",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    edges = response.json()["edges"]
    labels = {e["label"] for e in edges}
    assert {"LIVES_AT", "BORN_AT", "HELD_AT"} == labels
    assert len(edges) == 3


async def test_unauthenticated_returns_401(client):
    response = await client.get("/api/graph/")

    assert response.status_code == 401
