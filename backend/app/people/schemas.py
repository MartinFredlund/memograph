from datetime import date, datetime, timezone
from pydantic import BaseModel, ConfigDict, field_validator
from neo4j.time import Date as Neo4jDate


class PersonCreate(BaseModel):
    name: str
    birth_date: date | None = None
    death_date: date | None = None
    gender: str | None = None
    nickname: str | None = None
    description: str | None = None


class PersonUpdate(BaseModel):
    name: str | None = None
    birth_date: date | None = None
    death_date: date | None = None
    gender: str | None = None
    nickname: str | None = None
    description: str | None = None


class PersonResponse(BaseModel):
    uid: str
    name: str
    birth_date: date | None = None
    death_date: date | None = None
    gender: str | None = None
    nickname: str | None = None
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

    @field_validator("birth_date", "death_date", mode="before")
    @classmethod
    def neo4j_date_to_date(cls, v):
        if isinstance(v, Neo4jDate):
            return v.to_native()
        return v


class EventResponse(BaseModel):
    uid: str
    name: str
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None
    created_at: datetime
    updated_at: datetime
    derived: bool | None = None
    explicit: bool | None = None

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


class PlaceResponse(BaseModel):
    uid: str
    name: str
    address: str | None = None
    description: str | None = None


class BornAtCreate(BaseModel):
    place_uid: str
