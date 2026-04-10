from fastapi import APIRouter, Depends, HTTPException
from neo4j import Session

from app.dependencies import get_current_user, get_db_session, require_editor
from app.events.schemas import EventCreate, EventResponse, EventUpdate
from app.events.service import create_event, get_event, list_events, update_event


router = APIRouter(prefix="/api/events", tags=["event"])


@router.get("/")
def list_all(
    session: Session = Depends(get_db_session), current_user=Depends(get_current_user)
) -> list[EventResponse]:
    return [EventResponse(**event) for event in list_events(session)]


@router.get("/{uid}")
def get_one(
    uid: str,
    session: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> EventResponse:
    event = get_event(session, uid)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return EventResponse(**event)


@router.post("/", status_code=201)
def create(
    data: EventCreate,
    session: Session = Depends(get_db_session),
    current_user=Depends(require_editor),
) -> EventResponse:
    event = create_event(session, data)
    return EventResponse(**event)


@router.put("/{uid}")
def update(
    uid: str,
    data: EventUpdate,
    session: Session = Depends(get_db_session),
    current_user=Depends(require_editor),
) -> EventResponse:
    event = update_event(session, uid, data)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return EventResponse(**event)
