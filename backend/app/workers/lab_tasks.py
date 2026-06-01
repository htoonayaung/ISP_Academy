import asyncio
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.containerlab_adapter import ContainerlabAdapter
from app.db.session import async_session_factory
from app.lab_runtime.status_parser import parse_containerlab_nodes
from app.models.lab_instance import LabEvent, LabInstanceStatus
from app.models import lab_template, user  # noqa: F401
from app.repositories.labs import LabRepository
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.lab_tasks.start_lab_task")
def start_lab_task(lab_id: str, actor_id: str | None = None) -> None:
    asyncio.run(_start_lab(uuid.UUID(lab_id), _optional_uuid(actor_id)))


@celery_app.task(name="app.workers.lab_tasks.stop_lab_task")
def stop_lab_task(lab_id: str, actor_id: str | None = None) -> None:
    asyncio.run(_stop_lab(uuid.UUID(lab_id), _optional_uuid(actor_id)))


@celery_app.task(name="app.workers.lab_tasks.destroy_lab_task")
def destroy_lab_task(lab_id: str, actor_id: str | None = None) -> None:
    asyncio.run(_destroy_lab(uuid.UUID(lab_id), _optional_uuid(actor_id)))


@celery_app.task(name="app.workers.lab_tasks.refresh_lab_status_task")
def refresh_lab_status_task(lab_id: str) -> None:
    asyncio.run(_refresh_lab(uuid.UUID(lab_id)))


async def _start_lab(lab_id: uuid.UUID, actor_id: uuid.UUID | None) -> None:
    async with async_session_factory() as session:
        repository = LabRepository(session)
        lab = await repository.get_by_id(lab_id)
        if lab is None:
            return
        adapter = ContainerlabAdapter()
        result = adapter.deploy(lab)
        if result.ok:
            lab.status = LabInstanceStatus.RUNNING.value
            lab.started_at = datetime.now(UTC)
            lab.last_error = None
            await repository.add_event(_event(lab.id, "LAB_STARTED", "Containerlab deploy succeeded", result.stdout, result.stderr, actor_id))
            await repository.commit()
            await _refresh_nodes(session, repository, adapter, lab)
            return
        lab.status = LabInstanceStatus.FAILED.value
        lab.last_error = "Containerlab deploy failed"
        await repository.add_event(_event(lab.id, "LAB_FAILED", lab.last_error, result.stdout, result.stderr, actor_id))
        await repository.commit()


async def _stop_lab(lab_id: uuid.UUID, actor_id: uuid.UUID | None) -> None:
    async with async_session_factory() as session:
        repository = LabRepository(session)
        lab = await repository.get_by_id(lab_id)
        if lab is None:
            return
        adapter = ContainerlabAdapter()
        result = adapter.destroy(lab)
        if result.ok:
            lab.status = LabInstanceStatus.STOPPED.value
            lab.stopped_at = datetime.now(UTC)
            lab.last_error = None
            await repository.add_event(_event(lab.id, "LAB_STOPPED", "Containerlab destroy succeeded", result.stdout, result.stderr, actor_id))
        else:
            lab.status = LabInstanceStatus.FAILED.value
            lab.last_error = "Containerlab destroy failed while stopping lab"
            await repository.add_event(_event(lab.id, "LAB_FAILED", lab.last_error, result.stdout, result.stderr, actor_id))
        await repository.commit()


async def _destroy_lab(lab_id: uuid.UUID, actor_id: uuid.UUID | None) -> None:
    async with async_session_factory() as session:
        repository = LabRepository(session)
        lab = await repository.get_by_id(lab_id)
        if lab is None:
            return
        adapter = ContainerlabAdapter()
        result = adapter.destroy(lab)
        if result.ok:
            lab.status = LabInstanceStatus.DESTROYED.value
            lab.destroyed_at = datetime.now(UTC)
            lab.last_error = None
            await repository.replace_nodes(lab.id, [])
            await repository.add_event(_event(lab.id, "LAB_DESTROYED", "Containerlab resources destroyed", result.stdout, result.stderr, actor_id))
        else:
            lab.status = LabInstanceStatus.FAILED.value
            lab.last_error = "Containerlab destroy failed"
            await repository.add_event(_event(lab.id, "LAB_FAILED", lab.last_error, result.stdout, result.stderr, actor_id))
        await repository.commit()


async def _refresh_lab(lab_id: uuid.UUID) -> None:
    async with async_session_factory() as session:
        repository = LabRepository(session)
        lab = await repository.get_by_id(lab_id)
        if lab is None:
            return
        await _refresh_nodes(session, repository, ContainerlabAdapter(), lab)


async def _refresh_nodes(session: AsyncSession, repository: LabRepository, adapter: ContainerlabAdapter, lab) -> None:
    result, payload = adapter.inspect(lab)
    if result.ok and payload is not None:
        nodes = parse_containerlab_nodes(lab.id, payload)
        await repository.replace_nodes(lab.id, nodes)
        await repository.add_event(_event(lab.id, "LAB_INSPECTED", "Containerlab inspect succeeded", result.stdout, result.stderr, None))
        await session.commit()


def _event(
    lab_id: uuid.UUID,
    event_type: str,
    message: str,
    stdout: str | None,
    stderr: str | None,
    actor_id: uuid.UUID | None,
) -> LabEvent:
    return LabEvent(
        lab_instance_id=lab_id,
        event_type=event_type,
        message=message,
        stdout=stdout,
        stderr=stderr,
        created_by=actor_id,
    )


def _optional_uuid(value: str | None) -> uuid.UUID | None:
    if not value:
        return None
    return uuid.UUID(value)
