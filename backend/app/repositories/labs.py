import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.lab_instance import LabEvent, LabInstance, LabNode
from app.models.ticket import TicketAttempt


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
        output_limit = get_settings().lab_event_output_limit
        if event.stdout is not None:
            event.stdout = self._limit_output(event.stdout, output_limit)
        if event.stderr is not None:
            event.stderr = self._limit_output(event.stderr, output_limit)
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

    async def list_nodes_by_lab_ids(self, lab_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[LabNode]]:
        if not lab_ids:
            return {}
        result = await self.session.execute(select(LabNode).where(LabNode.lab_instance_id.in_(lab_ids)))
        grouped: dict[uuid.UUID, list[LabNode]] = {}
        for node in result.scalars().all():
            grouped.setdefault(node.lab_instance_id, []).append(node)
        return grouped

    async def list_events(self, lab_id: uuid.UUID) -> list[LabEvent]:
        result = await self.session.execute(
            select(LabEvent).where(LabEvent.lab_instance_id == lab_id).order_by(LabEvent.created_at.desc())
        )
        return list(result.scalars().all())

    async def count_attempts_for_lab(self, lab_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count(TicketAttempt.id)).where(TicketAttempt.lab_instance_id == lab_id)
        )
        return int(result.scalar_one())

    async def delete_lab_with_children(self, lab: LabInstance) -> None:
        await self.session.execute(delete(LabEvent).where(LabEvent.lab_instance_id == lab.id))
        await self.session.execute(delete(LabNode).where(LabNode.lab_instance_id == lab.id))
        await self.session.delete(lab)

    async def commit(self) -> None:
        await self.session.commit()

    async def refresh(self, lab: LabInstance) -> None:
        await self.session.refresh(lab)

    @staticmethod
    def _limit_output(value: str, output_limit: int) -> str:
        if len(value) <= output_limit:
            return value
        return value[:output_limit] + "\n[output truncated]"
