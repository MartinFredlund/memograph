from fastapi import APIRouter, Depends
from neo4j import Session

from app.auth.schemas import TokenPayload
from app.dependencies import get_current_user, get_db_session
from app.search.schemas import SearchItem
from app.search.service import search

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/")
def search_all(
    q: str,
    session: Session = Depends(get_db_session),
    current_user: TokenPayload = Depends(get_current_user),
) -> list[SearchItem]:
    return [SearchItem(**item) for item in search(session, q)]
