import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lab_template import LabTemplate
from app.models.lab_instance import LabInstance
from app.models.ticket import Ticket


class LabTemplateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, template_id: str | uuid.UUID) -> LabTemplate | None:
        try:
            parsed_id = uuid.UUID(str(template_id))
        except ValueError:
            return None
        return await self.session.get(LabTemplate, parsed_id)

    async def get_by_slug(self, slug: str) -> LabTemplate | None:
        result = await self.session.execute(select(LabTemplate).where(LabTemplate.slug == slug))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[LabTemplate]:
        result = await self.session.execute(select(LabTemplate).order_by(LabTemplate.created_at.desc()))
        return list(result.scalars().all())

    async def list_active(self) -> list[LabTemplate]:
        result = await self.session.execute(
            select(LabTemplate)
            .where(LabTemplate.is_active.is_(True))
            .order_by(LabTemplate.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_visible_to_instructor(self, instructor_id: uuid.UUID) -> list[LabTemplate]:
        result = await self.session.execute(
            select(LabTemplate)
            .where(or_(LabTemplate.created_by == instructor_id, LabTemplate.is_active.is_(True)))
            .order_by(LabTemplate.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, template: LabTemplate) -> LabTemplate:
        self.session.add(template)
        await self.session.flush()
        await self.session.refresh(template)
        return template

    async def commit(self) -> None:
        await self.session.commit()

    async def refresh(self, template: LabTemplate) -> None:
        await self.session.refresh(template)

    async def has_references(self, template_id: uuid.UUID) -> bool:
        checks = [
            select(func.count(Ticket.id)).where(Ticket.lab_template_id == template_id),
            select(func.count(LabInstance.id)).where(LabInstance.template_id == template_id),
        ]
        for query in checks:
            result = await self.session.execute(query)
            if int(result.scalar_one()) > 0:
                return True
        return False

    async def delete(self, template: LabTemplate) -> None:
        await self.session.delete(template)
