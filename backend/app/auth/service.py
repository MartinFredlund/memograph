from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt

from app import config
from app.auth.schemas import TokenPayload, UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(uid: str, role: UserRole) -> str:
    settings = config.get_settings()
    payload = {
        "sub": uid,
        "role": role.value,
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=settings.JWT_EXPIRY_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> TokenPayload:
    settings = config.get_settings()
    payload = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )
    return TokenPayload(**payload)
