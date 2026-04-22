from enum import Enum
from uuid import uuid4
from neo4j import Session

from app.events.schemas import EventCreate, EventUpdate, HeldAtCreate


class HeldAtResult(str, Enum):
    OK = "ok"
    EVENT_NOT_FOUND = "event not found"
    PLACE_NOT_FOUND = "place not found"


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


def add_tag_held_at(session: Session, uid: str, data: HeldAtCreate) -> HeldAtResult:
    result_event = session.run("MATCH (:Event {uid: $uid}) RETURN 1", uid=uid)
    record_event = result_event.single()
    if record_event is None:
        return HeldAtResult.EVENT_NOT_FOUND
    result_place = session.run(
        "MATCH (:Place {uid: $place_uid}) RETURN 1", place_uid=data.place_uid
    )
    record_place = result_place.single()
    if record_place is None:
        return HeldAtResult.PLACE_NOT_FOUND
    query = """
        MATCH (e:Event {uid: $uid})
        OPTIONAL MATCH (e)-[r:HELD_AT]->(:Place)
        DELETE r
        with e
        MATCH (pl:Place {uid: $place_uid})
        CREATE (e)-[:HELD_AT]->(pl)
    """
    session.run(
        query,
        uid=uid,
        place_uid=data.place_uid,
    )
    return HeldAtResult.OK


def remove_tag_held_at(session: Session, uid: str) -> HeldAtResult:
    result_event = session.run("MATCH (:Event {uid: $uid}) RETURN 1", uid=uid)
    record_event = result_event.single()
    if record_event is None:
        return HeldAtResult.EVENT_NOT_FOUND

    session.run(
        "MATCH (:Event {uid: $uid})-[r:HELD_AT]->(:Place) DELETE r",
        uid=uid,
    )
    return HeldAtResult.OK
