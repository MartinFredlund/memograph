from jose.exceptions import JWTError
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException
from neo4j import Session

from app.auth.schemas import TokenPayload, UserRole
from app.auth.service import decode_access_token
from app.db.neo4j_driver import get_driver

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    try:
        return decode_access_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_db_session() -> Session:
    driver = get_driver()
    with driver.session() as session:
        yield session


def require_editor(
    current_user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    if current_user.role not in {UserRole.ADMIN, UserRole.EDITOR}:
        raise HTTPException(status_code=403, detail="Invalid user role for action")
    return current_user
