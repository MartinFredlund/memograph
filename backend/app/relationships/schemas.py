from datetime import date
from enum import Enum
from pydantic import BaseModel, model_validator


class Category(str, Enum):
    PARENT_OF = "PARENT_OF"
    PARTNER_OF = "PARTNER_OF"
    SOCIAL = "SOCIAL"


class RelationshipCreate(BaseModel):
    from_uid: str
    to_uid: str
    category: Category
    since: date | None = None
    context: str | None = None
    social_type: str | None = None

    @model_validator(mode="after")
    def check_social_type(self):
        if self.category == Category.SOCIAL and not self.social_type:
            raise ValueError("social_type is required for SOCIAL relationships")
        return self


class RelationshipUpdate(BaseModel):
    since: date | None = None
    context: str | None = None


class RelationshipResponse(BaseModel):
    uid: str
    from_uid: str
    to_uid: str
    category: Category
    since: date | None = None
    context: str | None = None
    social_type: str | None = None
