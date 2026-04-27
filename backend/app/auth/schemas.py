from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

# --- Enums ---


class UserRole(str, Enum):
    """String Enum for user roles to ensure automatic validation and prevent typos."""

    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


# --- Token Schemas ---


class Token(BaseModel):
    """What the API returns after a successful login."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """The data encoded inside the JWT."""

    sub: str  # The user's uid
    role: UserRole
    exp: int


# --- User Schemas ---


class UserCreate(BaseModel):
    """What an admin sends to register a new user."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Must be at least 3 characters long.",
    )
    password: str = Field(
        ..., min_length=8, description="Strong password required, minimum 8 characters."
    )
    role: UserRole


class UserResponse(BaseModel):
    """What comes back when you read user data (never includes password)."""

    uid: str
    username: str
    role: UserRole
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UpdateUser(BaseModel):
    username: str | None = Field(
        None,
        min_length=3,
        max_length=50,
        description="Must be at least 3 characters long.",
    )
    password: str | None = Field(
        None,
        min_length=8,
        description="Strong password required, minimum 8 characters.",
    )
    role: UserRole | None = None
