from neo4j import Session


def list_nodes(session: Session) -> list[dict]:
    query = """
        CALL {
            MATCH (p:Person) RETURN p.uid AS uid, 'Person' AS type, p.name AS name
            UNION
            MATCH (e:Event) RETURN e.uid AS uid, 'Event' AS type, e.name AS name
            UNION
            MATCH (pl:Place) RETURN pl.uid as uid, 'Place' AS type, pl.name AS name
        }
        RETURN uid, type, name
        ORDER BY type, name
    """
    result = session.run(query)
    return [{"uid": r["uid"], "type": r["type"], "name": r["name"]} for r in result]


def list_plain_edges(session: Session) -> list[dict]:
    query = """
        CALL {
            MATCH (a)-[r:PARENT_OF]->(b) RETURN elementID(r) AS id, a.uid AS source, b.uid AS target, type(r) AS label
            UNION
            MATCH (a)-[r:PARTNER_OF]->(b) RETURN elementID(r) AS id, a.uid AS source, b.uid AS target, type(r) AS label
            UNION
            MATCH (a)-[r:HELD_AT]->(b) RETURN elementID(r) AS id, a.uid AS source, b.uid AS target, type(r) AS label
            UNION
            MATCH (a)-[r:LIVES_AT]->(b) RETURN elementID(r) AS id, a.uid AS source, b.uid AS target, type(r) AS label
            UNION
            MATCH (a)-[r:BORN_AT]->(b) RETURN elementID(r) AS id, a.uid AS source, b.uid AS target, type(r) AS label
        }
        RETURN id, source, target, label
    """
    result = session.run(query)
    return [
        {
            "id": r["id"],
            "source": r["source"],
            "target": r["target"],
            "label": r["label"],
        }
        for r in result
    ]


def list_social_edges(session: Session) -> list[dict]:
    query = """
        MATCH (a:Person)-[r:SOCIAL]->(b:Person)
        RETURN elementID(r) AS id, a.uid AS source, b.uid AS target, type(r) AS label, r.type AS social_type
    """
    result = session.run(query)
    return [
        {
            "id": r["id"],
            "source": r["source"],
            "target": r["target"],
            "label": r["label"],
            "social_type": r["social_type"],
        }
        for r in result
    ]


def list_attended_edges(session: Session) -> list[dict]:
    query_explicit = """
        MATCH (p:Person)-[r:ATTENDED]->(e:Event)
        RETURN elementID(r) AS id, p.uid AS source, e.uid AS target
    """
    query_derived = """
        MATCH (p:Person)-[:APPEARS_IN]->(i:Image)-[:FROM_EVENT]->(e:Event)
        RETURN DISTINCT p.uid as source, e.uid AS target
    """
    result_explicit = session.run(query_explicit)
    edges = {}
    for r in result_explicit:
        key = (r["source"], r["target"])
        edges[key] = {
            "id": r["id"],
            "source": r["source"],
            "target": r["target"],
            "label": "ATTENDED",
            "explicit": True,
            "derived": False,
        }
    result_derived = session.run(query_derived)
    for r in result_derived:
        key = (r["source"], r["target"])
        if key in edges:
            edges[key]["derived"] = True

        else:
            edges[key] = {
                "id": f"derived-{r['source']}-attended-{r['target']}",
                "source": r["source"],
                "target": r["target"],
                "label": "ATTENDED",
                "explicit": False,
                "derived": True,
            }
    return list(edges.values())
