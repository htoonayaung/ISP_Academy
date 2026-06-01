from fastapi import HTTPException, status

from app.core.config import get_settings
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.repositories.users import UserRepository
from app.schemas.auth import TokenResponse


class AuthService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def authenticate(self, identifier: str, password: str) -> User:
        generic_error = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

        user = await self.repository.get_by_identifier(identifier)
        if user is None:
            raise generic_error

        if not user.is_active:
            raise generic_error

        if not verify_password(password, user.hashed_password):
            raise generic_error

        return user

    async def login(self, identifier: str, password: str) -> TokenResponse:
        user = await self.authenticate(identifier, password)
        settings = get_settings()
        token = create_access_token(str(user.id))
        return TokenResponse(
            access_token=token,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )

