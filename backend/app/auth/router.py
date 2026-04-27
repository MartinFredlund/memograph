from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from neo4j import Session

from app.auth.schemas import Token, UpdateUser, UserCreate, UserResponse, UserRole
from app.auth.service import (
    create_access_token,
    create_user,
    get_all_users,
    get_user_by_username,
    hash_password,
    update_user,
    verify_password,
)
from app.dependencies import get_current_user, get_db_session

router = APIRouter(prefix="/api/auth", tags=["auth"])
user_router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/login")
def login(
    credentials: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_db_session),
) -> Token:
    user = get_user_by_username(session, credentials.username)
    if user and verify_password(credentials.password, user["hashed_password"]):
        token = create_access_token(user["uid"], user["username"], UserRole(user["role"]))
        return Token(access_token=token)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )


@router.post("/register")
def register(
    user_create: UserCreate,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> UserResponse:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    if get_user_by_username(session, user_create.username):
        raise HTTPException(status_code=409, detail="Username taken")
    return UserResponse(
        **create_user(
            session,
            user_create.username,
            hash_password(user_create.password),
            user_create.role,
        )
    )


@user_router.put("/{uid}")
def update(
    uid: str,
    data: UpdateUser,
    session: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> UserResponse:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    result = update_user(session, uid, data)
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**result)


@user_router.get("/")
def all_users(
    session: Session = Depends(get_db_session), current_user=Depends(get_current_user)
) -> list[UserResponse]:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return get_all_users(session)
