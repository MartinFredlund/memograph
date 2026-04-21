from fastapi import APIRouter, Depends
from neo4j import Session

from app.auth.schemas import TokenPayload
from app.dependencies import get_current_user, get_db_session
from app.graph.schemas import GraphEdge, GraphNode, GraphResponse
from app.graph.service import (
    list_attended_edges,
    list_nodes,
    list_plain_edges,
    list_social_edges,
)

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/", status_code=200)
def get_graph(
    session: Session = Depends(get_db_session),
    current_user: TokenPayload = Depends(get_current_user),
) -> GraphResponse:
    edges = []
    edges.extend([GraphEdge(**e) for e in list_plain_edges(session)])
    edges.extend([GraphEdge(**e) for e in list_social_edges(session)])
    edges.extend([GraphEdge(**e) for e in list_attended_edges(session)])
    return GraphResponse(
        nodes=[GraphNode(**n) for n in list_nodes(session)],
        edges=edges,
    )
