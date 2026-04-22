from fastapi import APIRouter, Depends, HTTPException
from neo4j import Session

from app.dependencies import get_current_user, get_db_session, require_editor
from app.people.schemas import (
    EventResponse,
    PersonCreate,
    PersonResponse,
    PersonUpdate,
    PlaceResponse,
)
from app.people.service import (
    create_person,
    get_person,
    list_attended_events,
    list_persons,
    list_visited_places,
    update_person,
)

router = APIRouter(prefix="/api/people", tags=["people"])


@router.get("/")
def list_all(
    session: Session = Depends(get_db_session), current_user=Depends(get_current_user)
) -> list[PersonResponse]:
    return [PersonResponse(**person) for person in list_persons(session)]


@router.get("/{uid}")
def get_one(
    uid: str,
    session: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> PersonResponse:
    person = get_person(session, uid)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")
    return PersonResponse(**person)


@router.post("/", status_code=201)
def create(
    data: PersonCreate,
    session: Session = Depends(get_db_session),
    current_user=Depends(require_editor),
) -> PersonResponse:
    person = create_person(session, data)
    return PersonResponse(**person)


@router.put("/{uid}")
def update(
    uid: str,
    data: PersonUpdate,
    session: Session = Depends(get_db_session),
    current_user=Depends(require_editor),
) -> PersonResponse:
    person = update_person(session, uid, data)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")
    return PersonResponse(**person)


@router.get("/{uid}/events", status_code=200)
def list_events(
    uid: str,
    session: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[EventResponse]:
    return [EventResponse(**e) for e in list_attended_events(session, uid)]


@router.get("/{uid}/places", status_code=200)
def list_places(
    uid: str,
    session: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[PlaceResponse]:
    return [PlaceResponse(**p) for p in list_visited_places(session, uid)]
