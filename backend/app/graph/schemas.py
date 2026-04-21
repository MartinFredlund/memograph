from typing import Literal
from pydantic import BaseModel


class GraphNode(BaseModel):
    uid: str
    type: Literal["Person", "Event", "Place"]
    name: str


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str
    social_type: str | None = None
    explicit: bool | None = None
    derived: bool | None = None


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
