from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, field_validator


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
