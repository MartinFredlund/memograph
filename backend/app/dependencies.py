from jose.exceptions import JWTError
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException
from neo4j import Session

from app.auth.schemas import TokenPayload
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
