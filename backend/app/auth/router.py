from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.schemas import Token, UserCreate, UserResponse, UserRole
from app.auth.service import (
    create_access_token,
    create_user,
    get_user_by_username,
    hash_password,
    verify_password,
)
from app.db.neo4j_driver import get_driver
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(credentials: OAuth2PasswordRequestForm = Depends()) -> Token:
    driver = get_driver()
    user = get_user_by_username(driver, credentials.username)
    if user and verify_password(credentials.password, user["hashed_password"]):
        token = create_access_token(user["uid"], UserRole(user["role"]))
        return Token(access_token=token)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )


@router.post("/register")
def register(
    user_create: UserCreate, current_user=Depends(get_current_user)
) -> UserResponse:
    driver = get_driver()
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    if get_user_by_username(driver, user_create.username):
        raise HTTPException(status_code=409, detail="Username taken")
    return UserResponse(
        **create_user(
            driver,
            user_create.username,
            hash_password(user_create.password),
            user_create.role,
        )
    )
