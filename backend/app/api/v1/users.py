import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.permissions import get_current_user
from app.models.user import User
from app.repositories.users import UserRepository
from app.schemas.user import UserCreate, UserPasswordReset, UserRead, UserUpdate
from app.services.user_service import UserService

router = APIRouter(tags=["users"])


def get_user_service(session: AsyncSession = Depends(get_db_session)) -> UserService:
    return UserService(UserRepository(session))


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> User:
    return await service.create_user(current_user, payload)


@router.get("", response_model=list[UserRead])
async def list_users(
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> list[User]:
    return await service.list_users(current_user)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> User:
    return await service.get_user(current_user, user_id)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> User:
    return await service.update_user(current_user, user_id, payload)


@router.delete("/{user_id}", response_model=UserRead)
async def deactivate_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> User:
    return await service.deactivate_user(current_user, user_id)


@router.post("/{user_id}/reset-password", response_model=UserRead)
async def reset_user_password(
    user_id: uuid.UUID,
    payload: UserPasswordReset,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> User:
    return await service.reset_password(current_user, user_id, payload)
