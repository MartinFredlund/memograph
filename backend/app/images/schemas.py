from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ImageRotate(BaseModel):
    degrees: Literal[90, 180, 270]


class ImageResponse(BaseModel):
    uid: str
    filename: str
    object_key: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("uploaded_at", mode="before")
    @classmethod
    def ms_to_datetime(cls, v):
        if isinstance(v, int):
            return datetime.fromtimestamp(v / 1000, tz=timezone.utc)
        return v


class PersonTagCreate(BaseModel):
    person_uid: str
    tag_x: float = Field(ge=0, le=100)
    tag_y: float = Field(ge=0, le=100)


class PersonTagResponse(BaseModel):
    person_uid: str
    person_name: str
    tag_x: float
    tag_y: float


class PersonTagSummary(BaseModel):
    person_uid: str
    person_name: str


class EventSummary(BaseModel):
    event_uid: str
    event_name: str


class PlaceSummary(BaseModel):
    place_uid: str
    place_name: str


class PlaceLink(BaseModel):
    place_uid: str


class EventLink(BaseModel):
    event_uid: str


class ImageListParams(BaseModel):
    person_uid: str | None = None
    event_uid: str | None = None
    place_uid: str | None = None
    cursor: str | None = None
    page_size: int = Field(default=50, ge=1, le=200)


class ImageListItem(ImageResponse):
    tags: list[PersonTagSummary] = []
    event: EventSummary | None = None
    place: PlaceSummary | None = None


class PaginatedImages(BaseModel):
    items: list[ImageListItem]
    next_cursor: str | None = None


class ImageCountParams(BaseModel):
    person_uid: str | None = None
    event_uid: str | None = None
    place_uid: str | None = None


class ImageCountResponse(BaseModel):
    count: int
