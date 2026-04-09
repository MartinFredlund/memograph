from datetime import date, datetime, timezone
from pydantic import BaseModel, ConfigDict, field_validator


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
