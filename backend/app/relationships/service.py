from uuid import uuid4
from neo4j import Session

from app.relationships.schemas import Category, RelationshipCreate, RelationshipUpdate


def create_relationship(session: Session, data: RelationshipCreate) -> dict | None:
    if data.category == Category.PARENT_OF:
        query = """
            MATCH (a:Person {uid: $from_uid}), (b:Person {uid: $to_uid})
            CREATE (a)-[r:PARENT_OF {uid: $uid, since: $since, context: $context}]->(b)
            RETURN r, a.uid as from_uid, b.uid as to_uid
        """
    elif data.category == Category.PARTNER_OF:
        query = """
            MATCH (a:Person {uid: $from_uid}), (b:Person {uid: $to_uid})
            CREATE (a)-[r:PARTNER_OF {uid: $uid, since: $since, context: $context}]->(b)
            RETURN r, a.uid as from_uid, b.uid as to_uid
        """
    elif data.category == Category.SOCIAL:
        query = """
            MATCH (a:Person {uid: $from_uid}), (b:Person {uid: $to_uid})
            CREATE (a)-[r:SOCIAL {uid: $uid, since: $since, context: $context, social_type: $social_type}]->(b)
            RETURN r, a.uid as from_uid, b.uid as to_uid
        """
    else:
        raise ValueError(f"Unknown category: {data.category}")

    result = session.run(
        query,
        from_uid=data.from_uid,
        to_uid=data.to_uid,
        uid=str(uuid4()),
        since=data.since,
        context=data.context,
        social_type=data.social_type,
    )
    record = result.single()
    if record is None:
        return None
    rel = dict(record["r"])
    rel["from_uid"] = record["from_uid"]
    rel["to_uid"] = record["to_uid"]
    rel["category"] = data.category.value
    return rel


def get_relationships_for_person(session: Session, person_uid: str) -> list[dict]:
    query = """
        MATCH (:Person{uid: $uid})-[r]-(:Person)
        RETURN r, startNode(r).uid AS from_uid, endNode(r).uid AS to_uid, type(r) AS category
    """
    result = session.run(query, uid=person_uid)
    relationships = []
    for record in result:
        rel = dict(record["r"])
        rel["from_uid"] = record["from_uid"]
        rel["to_uid"] = record["to_uid"]
        rel["category"] = record["category"]
        relationships.append(rel)
    return relationships


def update_relationship(
    session: Session, uid: str, data: RelationshipUpdate
) -> dict | None:
    query = """
        MATCH (a: Person)-[r {uid: $uid}]-> (b: Person)
        SET r += $props
        RETURN r, a.uid AS from_uid, b.uid AS to_uid, type(r) AS category
    """
    result = session.run(query, uid=uid, props=data.model_dump(exclude_none=True))
    record = result.single()
    if record is None:
        return None
    rel = dict(record["r"])
    rel["from_uid"] = record["from_uid"]
    rel["to_uid"] = record["to_uid"]
    rel["category"] = record["category"]
    return rel


def delete_relationship(session: Session, uid: str) -> bool:
    query = """
        MATCH (a: Person)-[r {uid:$uid}]->(b:Person)
        DELETE r
        RETURN count(r) as deleted
    """
    result = session.run(query, uid=uid)
    record = result.single()
    return record["deleted"] > 0
