from enum import Enum
from uuid import uuid4
from neo4j import Session

from app.people.schemas import AttendedCreate, PersonCreate, PersonUpdate, BornAtCreate


class BornAtResult(str, Enum):
    OK = "ok"
    PERSON_NOT_FOUND = "person not found"
    PLACE_NOT_FOUND = "place not found"


class AttendedResult(str, Enum):
    OK = "ok"
    PERSON_NOT_FOUND = "person not found"
    EVENT_NOT_FOUND = "event not found"


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


def list_visited_places(session: Session, uid: str) -> list[dict]:
    query = """
        MATCH (:Person {uid: $uid}) - [:APPEARS_IN] -> (:Image) - [:TAKEN_AT] -> (pl:Place)
        return DISTINCT pl as place
   """
    result = session.run(query, uid=uid)
    places = {}
    for r in result:
        place = r["place"]
        places[place["uid"]] = {
            "uid": place["uid"],
            "name": place["name"],
            "address": place["address"],
            "description": place["description"],
        }
    return list(places.values())


def add_tag_born_at(session: Session, uid: str, data: BornAtCreate) -> BornAtResult:
    result_person = session.run("MATCH (p:Person {uid:$uid}) RETURN 1", uid=uid)
    record_person = result_person.single()
    if record_person is None:
        return BornAtResult.PERSON_NOT_FOUND
    result_place = session.run(
        "MATCH (pl:Place {uid:$place_uid}) RETURN 1", place_uid=data.place_uid
    )
    record_place = result_place.single()
    if record_place is None:
        return BornAtResult.PLACE_NOT_FOUND
    query = """
        MATCH (p:Person {uid: $uid})
        OPTIONAL MATCH (p)-[r:BORN_AT]->(:Place)
        DELETE r
        WITH p
        MATCH (pl:Place {uid: $place_uid})
        CREATE (p)-[:BORN_AT]->(pl)
    """
    session.run(
        query,
        uid=uid,
        place_uid=data.place_uid,
    )
    return BornAtResult.OK


def unset_tag_born_at(session: Session, uid: str) -> BornAtResult:
    result_person = session.run("MATCH (p:Person {uid:$uid}) RETURN 1", uid=uid)
    record_person = result_person.single()
    if record_person is None:
        return BornAtResult.PERSON_NOT_FOUND
    session.run(
        "OPTIONAL MATCH (p:Person {uid:$uid})-[r:BORN_AT]->() DELETE r", uid=uid
    )
    return BornAtResult.OK


def add_tag_attended(
    session: Session, uid: str, data: AttendedCreate
) -> AttendedResult:
    result_person = session.run("MATCH (p:Person {uid:$uid}) RETURN 1", uid=uid)
    record_person = result_person.single()
    if record_person is None:
        return AttendedResult.PERSON_NOT_FOUND
    result_event = session.run(
        "MATCH (e:Event {uid:$event_uid}) RETURN 1", event_uid=data.event_uid
    )
    record_event = result_event.single()
    if record_event is None:
        return AttendedResult.EVENT_NOT_FOUND
    session.run(
        "MATCH (p:Person {uid: $uid}), (e:Event {uid: $event_uid}) MERGE (p)-[:ATTENDED]->(e)",
        uid=uid,
        event_uid=data.event_uid,
    )
    return AttendedResult.OK


def remove_tag_attended(session: Session, uid: str, event_uid: str) -> AttendedResult:
    result_person = session.run("MATCH (p:Person {uid:$uid}) RETURN 1", uid=uid)
    record_person = result_person.single()
    if record_person is None:
        return AttendedResult.PERSON_NOT_FOUND
    result_event = session.run(
        "MATCH (e:Event {uid:$event_uid}) RETURN 1", event_uid=event_uid
    )
    record_event = result_event.single()
    if record_event is None:
        return AttendedResult.EVENT_NOT_FOUND
    session.run(
        "MATCH (:Person {uid:$uid}) - [r:ATTENDED] -> (:Event {uid:$event_uid}) DELETE r",
        uid=uid,
        event_uid=event_uid,
    )
    return AttendedResult.OK
