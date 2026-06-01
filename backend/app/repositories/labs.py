import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lab_instance import LabEvent, LabInstance, LabNode


class LabRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, lab_id: str | uuid.UUID) -> LabInstance | None:
        try:
            parsed_id = uuid.UUID(str(lab_id))
        except ValueError:
            return None
        return await self.session.get(LabInstance, parsed_id)

    async def list_all(self) -> list[LabInstance]:
        result = await self.session.execute(select(LabInstance).order_by(LabInstance.created_at.desc()))
        return list(result.scalars().all())

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[LabInstance]:
        result = await self.session.execute(
            select(LabInstance)
            .where(LabInstance.owner_id == owner_id)
            .order_by(LabInstance.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, lab: LabInstance) -> LabInstance:
        self.session.add(lab)
        await self.session.flush()
        await self.session.refresh(lab)
        return lab

    async def add_event(self, event: LabEvent) -> LabEvent:
        self.session.add(event)
        await self.session.flush()
        await self.session.refresh(event)
        return event

    async def replace_nodes(self, lab_id: uuid.UUID, nodes: list[LabNode]) -> None:
        await self.session.execute(delete(LabNode).where(LabNode.lab_instance_id == lab_id))
        self.session.add_all(nodes)
        await self.session.flush()

    async def list_nodes(self, lab_id: uuid.UUID) -> list[LabNode]:
        result = await self.session.execute(
            select(LabNode).where(LabNode.lab_instance_id == lab_id).order_by(LabNode.name.asc())
        )
        return list(result.scalars().all())

    async def list_events(self, lab_id: uuid.UUID) -> list[LabEvent]:
        result = await self.session.execute(
            select(LabEvent).where(LabEvent.lab_instance_id == lab_id).order_by(LabEvent.created_at.desc())
        )
        return list(result.scalars().all())

    async def commit(self) -> None:
        await self.session.commit()

    async def refresh(self, lab: LabInstance) -> None:
        await self.session.refresh(lab)
