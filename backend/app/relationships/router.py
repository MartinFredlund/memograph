from fastapi import APIRouter, Depends, HTTPException
from neo4j import Session

from app.dependencies import get_current_user, get_db_session, require_editor
from app.relationships.schemas import (
    RelationshipCreate,
    RelationshipResponse,
    RelationshipUpdate,
)
from app.relationships.service import (
    create_relationship,
    delete_relationship,
    get_relationships_for_person,
    update_relationship,
)

router = APIRouter(tags=["relationships"])


@router.post("/api/relationships", status_code=201)
def create(
    data: RelationshipCreate,
    session: Session = Depends(get_db_session),
    current_user=Depends(require_editor),
) -> RelationshipResponse:
    relationship = create_relationship(session, data)
    if relationship is None:
        raise HTTPException(status_code=404, detail="One or both people not found")
    return RelationshipResponse(**relationship)


@router.get("/api/people/{person_uid}/relationships")
def list_for_person(
    person_uid: str,
    session: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[RelationshipResponse]:
    return [
        RelationshipResponse(**relationship)
        for relationship in get_relationships_for_person(session, person_uid)
    ]


@router.put("/api/relationships/{uid}")
def update(
    data: RelationshipUpdate,
    uid: str,
    session: Session = Depends(get_db_session),
    current_user=Depends(require_editor),
) -> RelationshipResponse:
    relationship = update_relationship(session, uid, data)
    if relationship is None:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return RelationshipResponse(**relationship)


@router.delete("/api/relationships/{uid}", status_code=204)
def delete(
    uid: str,
    session: Session = Depends(get_db_session),
    current_user=Depends(require_editor),
):
    if not delete_relationship(session, uid):
        raise HTTPException(status_code=404, detail="Could not delete relationship")
