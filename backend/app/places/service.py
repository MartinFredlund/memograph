from uuid import uuid4
from neo4j import Session

from app.places.schemas import PlaceCreate, PlaceUpdate


def create_place(session: Session, data: PlaceCreate) -> dict:
    query = """
        CREATE (p:Place{uid:$uid, created_at: timestamp(), updated_at: timestamp()})
        SET p += $props
        RETURN p
    """
    result = session.run(
        query, uid=str(uuid4()), props=data.model_dump(exclude_none=True)
    )
    record = result.single()
    return dict(record["p"])


def get_place(session: Session, uid: str) -> dict | None:
    result = session.run("MATCH (p:Place {uid: $uid}) RETURN p", uid=uid)
    record = result.single()
    if record is None:
        return None
    return dict(record["p"])


def update_place(session: Session, uid: str, data: PlaceUpdate) -> dict | None:
    result = session.run(
        "MATCH (p:Place {uid:$uid}) SET p += $props, p.updated_at=timestamp() RETURN p",
        uid=uid,
        props=data.model_dump(exclude_none=True),
    )
    record = result.single()
    if record is None:
        return None
    return dict(record["p"])


def list_places(session: Session) -> list[dict]:
    result = session.run("MATCH (p:Place) RETURN p")
    return [dict(record["p"]) for record in result]
