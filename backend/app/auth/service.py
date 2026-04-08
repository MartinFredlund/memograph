from datetime import datetime, timedelta, timezone
from jose import jwt
from neo4j import Driver
from uuid import uuid4
import bcrypt

from app import config
from app.auth.schemas import TokenPayload, UserRole


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


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


def get_user_by_username(driver: Driver, username: str) -> dict | None:
    with driver.session() as session:
        result = session.run(
            "MATCH (u:User {username: $username}) RETURN u", username=username
        )
        record = result.single()
        if record is None:
            return None
        return dict(record["u"])


def create_user(
    driver: Driver, username: str, hashed_password: str, role: UserRole
) -> dict:
    with driver.session() as session:
        query = """
            CREATE (u:User{
                uid: $uid,
                username: $username,
                hashed_password: $hashed_password,
                role: $role,
                is_active: true,
                created_at: timestamp(),
                updated_at: timestamp()
            })
            RETURN u
        """
        result = session.run(
            query,
            uid=str(uuid4()),
            username=username,
            hashed_password=hashed_password,
            role=role.value,
        )
        record = result.single()
        return dict(record["u"])
