from uuid import uuid4
from neo4j import Session

from app.events.schemas import EventCreate, EventUpdate


def create_event(session: Session, data: EventCreate) -> dict:
    query = """
        CREATE (e:Event {uid:$uid, created_at: timestamp(), updated_at: timestamp()})
        SET e += $props
        RETURN e
    """
    result = session.run(
        query,
        uid=str(uuid4()),
        props=data.model_dump(exclude_none=True),
    )
    record = result.single()
    return dict(record["e"])


def get_event(session: Session, uid: str) -> dict | None:
    result = session.run("MATCH (e:Event {uid:$uid}) RETURN e", uid=uid)
    record = result.single()
    if record is None:
        return None
    return dict(record["e"])


def update_event(session: Session, uid: str, data: EventUpdate) -> dict | None:
    result = session.run(
        "MATCH (e:Event {uid: $uid}) SET e += $props, e.updated_at = timestamp() RETURN e",
        uid=uid,
        props=data.model_dump(exclude_none=True),
    )
    record = result.single()
    if record is None:
        return None
    return dict(record["e"])


def list_events(session: Session) -> list[dict]:
    result = session.run("MATCH (e:Event) RETURN e")
    return [dict(record["e"]) for record in result]
