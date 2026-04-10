from fastapi import APIRouter, Depends, HTTPException
from neo4j import Session

from app.dependencies import get_current_user, get_db_session, require_editor
from app.places.schemas import PlaceCreate, PlaceResponse, PlaceUpdate
from app.places.service import create_place, get_place, list_places, update_place


router = APIRouter(prefix="/api/places", tags=["places"])


@router.get("/")
def list_all(
    session: Session = Depends(get_db_session), current_user=Depends(get_current_user)
) -> list[PlaceResponse]:
    return [PlaceResponse(**place) for place in list_places(session)]


@router.get("/{uid}")
def get_one(
    uid: str,
    session: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> PlaceResponse:
    place = get_place(session, uid)
    if place is None:
        raise HTTPException(status_code=404, detail="Place not found")
    return PlaceResponse(**place)


@router.post("/", status_code=201)
def create(
    data: PlaceCreate,
    session: Session = Depends(get_db_session),
    current_user=Depends(require_editor),
) -> PlaceResponse:
    place = create_place(session, data)
    return PlaceResponse(**place)


@router.put("/{uid}")
def update(
    uid: str,
    data: PlaceUpdate,
    session: Session = Depends(get_db_session),
    current_user=Depends(require_editor),
) -> PlaceResponse:
    place = update_place(session, uid, data)
    if place is None:
        raise HTTPException(status_code=404, detail="Place not found")
    return PlaceResponse(**place)
