from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field, field_validator


class PlaceCreate(BaseModel):
    name: str
    address: str | None = None
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    description: str | None = None


class PlaceUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    description: str | None = None


class PlaceResponse(BaseModel):
    uid: str
    name: str
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def ms_to_datetime(cls, v):
        if isinstance(v, int):
            return datetime.fromtimestamp(v / 1000, tz=timezone.utc)
        return v
