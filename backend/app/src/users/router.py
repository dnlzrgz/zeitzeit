from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.deps import CurrentUser, SessionDep
from app.models import (
    UpdatePassword,
    UserCreate,
    UserPublic,
    UserRegister,
    UserUpdate,
    UserUpdateMe,
)
from app.src.users import services

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/signup", response_model=UserPublic)
def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """
    Create a new user without the need to be logged in.
    """
    user = services.get_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The user with this email already exists in the system",
        )
    user_create = UserCreate.model_validate(user_in)
    user = services.create(session=session, user_create=user_create)
    return user


@router.get("/me", response_model=UserPublic)
def get_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return current_user


@router.patch("/me", response_model=UserPublic)
def update_me(
    session: SessionDep,
    current_user: CurrentUser,
    user_in: UserUpdateMe,
) -> Any:
    """
    Update the current user.
    """
    if user_in.email and user_in.email != current_user.email:
        existing = services.get_by_email(session=session, email=str(user_in.email))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already in use",
            )

    return services.update(session=session, db_user=current_user, user_in=user_in)


@router.patch("/me/password", status_code=204)
def update_password(
    session: SessionDep,
    current_user: CurrentUser,
    body: UpdatePassword,
) -> None:
    """
    Change the current user's password.
    """
    from app.security import verify_password

    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must differ from current",
        )

    user_in = UserUpdate(password=body.new_password)
    services.update(session=session, db_user=current_user, user_in=user_in)
