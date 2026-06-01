import asyncio

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import async_session_factory
from app.models.user import User, UserRole
from app.repositories.users import UserRepository


async def seed_admin() -> None:
    settings = get_settings()
    async with async_session_factory() as session:
        repository = UserRepository(session)
        existing = await repository.get_by_identifier(settings.initial_admin_email)
        if existing is not None:
            print("Initial admin already exists")
            return

        admin = User(
            email=settings.initial_admin_email.lower(),
            username=settings.initial_admin_username,
            hashed_password=hash_password(settings.initial_admin_password),
            full_name=settings.initial_admin_full_name,
            role=UserRole.ADMIN,
            is_active=True,
        )
        await repository.create(admin)
        await repository.commit()
        print(f"Initial admin created: {settings.initial_admin_email}")


if __name__ == "__main__":
    asyncio.run(seed_admin())

