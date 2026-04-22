from datetime import date, datetime, timezone
from pydantic import BaseModel, ConfigDict, field_validator
from neo4j.time import Date as Neo4jDate


class EventCreate(BaseModel):
    name: str
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None


class EventUpdate(BaseModel):
    name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None


class EventResponse(BaseModel):
    uid: str
    name: str
    start_date: date | None = None
    end_date: date | None = None
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

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def neo4j_date_to_date(cls, v):
        if isinstance(v, Neo4jDate):
            return v.to_native()  # converts to datetime.date
        return v


class HeldAtCreate(BaseModel):
    place_uid: str
