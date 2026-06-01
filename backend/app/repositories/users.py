import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: str | uuid.UUID) -> User | None:
        try:
            parsed_id = uuid.UUID(str(user_id))
        except ValueError:
            return None
        return await self.session.get(User, parsed_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_by_identifier(self, identifier: str) -> User | None:
        lowered = identifier.lower()
        result = await self.session.execute(
            select(User).where(or_(User.email == lowered, User.username == identifier))
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[User]:
        result = await self.session.execute(select(User).order_by(User.created_at.desc()))
        return list(result.scalars().all())

    async def list_by_role(self, role: UserRole) -> list[User]:
        result = await self.session.execute(
            select(User).where(User.role == role).order_by(User.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def commit(self) -> None:
        await self.session.commit()

    async def refresh(self, user: User) -> None:
        await self.session.refresh(user)

