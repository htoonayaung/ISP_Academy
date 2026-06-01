import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import AILabBuilderPreview


class AILabBuilderPreviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, preview: AILabBuilderPreview) -> AILabBuilderPreview:
        self.session.add(preview)
        await self.session.flush()
        await self.session.refresh(preview)
        return preview

    async def get_by_id(self, preview_id: uuid.UUID) -> AILabBuilderPreview | None:
        return await self.session.get(AILabBuilderPreview, preview_id)

    async def list_all(self) -> list[AILabBuilderPreview]:
        result = await self.session.execute(
            select(AILabBuilderPreview).order_by(AILabBuilderPreview.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_requester(self, user_id: uuid.UUID) -> list[AILabBuilderPreview]:
        result = await self.session.execute(
            select(AILabBuilderPreview)
            .where(AILabBuilderPreview.requested_by == user_id)
            .order_by(AILabBuilderPreview.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, preview: AILabBuilderPreview) -> None:
        await self.session.delete(preview)

    async def commit(self) -> None:
        await self.session.commit()

    async def refresh(self, preview: AILabBuilderPreview) -> None:
        await self.session.refresh(preview)
