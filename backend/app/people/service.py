from uuid import uuid4
from neo4j import Session

from app.people.schemas import PersonCreate, PersonUpdate


def create_person(session: Session, data: PersonCreate) -> dict:
    query = """
        CREATE (p:Person{uid: $uid, created_at: timestamp(), updated_at: timestamp()})
        SET p += $props
        RETURN p
    """
    result = session.run(
        query,
        uid=str(uuid4()),
        props=data.model_dump(exclude_none=True),
    )
    record = result.single()
    return dict(record["p"])


def get_person(session: Session, uid: str) -> dict | None:
    result = session.run("MATCH (p:Person {uid: $uid}) RETURN p", uid=uid)
    record = result.single()
    if record is None:
        return None
    return dict(record["p"])


def update_person(session: Session, uid: str, data: PersonUpdate) -> dict | None:
    result = session.run(
        "MATCH (p:Person {uid: $uid}) SET p += $props, p.updated_at = timestamp() RETURN p",
        uid=uid,
        props=data.model_dump(exclude_none=True),
    )
    record = result.single()
    if record is None:
        return None
    return dict(record["p"])


def list_persons(session: Session) -> list[dict]:
    result = session.run("MATCH (p:Person) RETURN p")
    return [dict(record["p"]) for record in result]


def list_attended_events(session: Session, uid: str) -> list[dict]:
    query_explicit = """
        MATCH (:Person {uid: $uid})-[:ATTENDED]->(e:Event)
        RETURN e AS event
    """
    query_derived = """
        MATCH (p:Person {uid: $uid})-[:APPEARS_IN]->(i:Image)-[:FROM_EVENT]->(e:Event)
        RETURN DISTINCT e AS event
    """
    result_explicit = session.run(query_explicit, uid=uid)

    events = {}
    for r in result_explicit:
        event = r["event"]
        key = event["uid"]
        events[key] = {
            "uid": event["uid"],
            "name": event["name"],
            "start_date": event["start_date"],
            "end_date": event["end_date"],
            "description": event["description"],
            "created_at": event["created_at"],
            "updated_at": event["updated_at"],
            "explicit": True,
            "derived": False,
        }
    result_derived = session.run(query_derived, uid=uid)
    for r in result_derived:
        event = r["event"]
        key = event["uid"]
        if key in events:
            events[key]["derived"] = True

        else:
            events[key] = {
                "uid": event["uid"],
                "name": event["name"],
                "start_date": event["start_date"],
                "end_date": event["end_date"],
                "description": event["description"],
                "created_at": event["created_at"],
                "updated_at": event["updated_at"],
                "explicit": False,
                "derived": True,
            }
    return list(events.values())
