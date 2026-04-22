from typing import Literal
from pydantic import BaseModel


class SearchItem(BaseModel):
    uid: str
    name: str
    type: Literal["person", "event", "place"]
    score: float
