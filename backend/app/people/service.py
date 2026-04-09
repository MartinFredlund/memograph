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
