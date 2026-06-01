import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.models.user import User, UserRole
from app.repositories.users import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def create_user(self, actor: User, data: UserCreate) -> User:
        self._require_admin(actor)
        user = User(
            email=data.email.lower(),
            username=data.username,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role=data.role,
            is_active=data.is_active,
        )
        try:
            created = await self.repository.create(user)
            await self.repository.commit()
            await self.repository.refresh(created)
            return created
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User email or username already exists",
            ) from exc

    async def list_users(self, actor: User) -> list[User]:
        if actor.role == UserRole.ADMIN:
            return await self.repository.list_all()
        if actor.role == UserRole.INSTRUCTOR:
            return await self.repository.list_by_role(UserRole.STUDENT)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    async def get_user(self, actor: User, user_id: uuid.UUID) -> User:
        user = await self.repository.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if actor.role == UserRole.ADMIN:
            return user
        if actor.role == UserRole.INSTRUCTOR and user.role == UserRole.STUDENT:
            return user
        if actor.id == user.id:
            return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    async def update_user(self, actor: User, user_id: uuid.UUID, data: UserUpdate) -> User:
        user = await self.repository.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        is_self = actor.id == user.id
        if actor.role != UserRole.ADMIN and not is_self:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

        if actor.role != UserRole.ADMIN and (data.role is not None or data.is_active is not None):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

        if data.email is not None:
            user.email = data.email.lower()
        if data.username is not None:
            user.username = data.username
        if data.full_name is not None:
            user.full_name = data.full_name
        if data.password is not None:
            user.hashed_password = hash_password(data.password)
        if actor.role == UserRole.ADMIN and data.role is not None:
            user.role = data.role
        if actor.role == UserRole.ADMIN and data.is_active is not None:
            user.is_active = data.is_active

        try:
            await self.repository.commit()
            await self.repository.refresh(user)
            return user
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User email or username already exists",
            ) from exc

    async def deactivate_user(self, actor: User, user_id: uuid.UUID) -> User:
        self._require_admin(actor)
        user = await self.repository.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        user.is_active = False
        await self.repository.commit()
        await self.repository.refresh(user)
        return user

    @staticmethod
    def _require_admin(actor: User) -> None:
        if actor.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

