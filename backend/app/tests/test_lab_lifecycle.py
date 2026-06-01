import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
import uuid

from app.models.lab_instance import LabInstance
from app.models.lab_template import LabTemplate


class DummyTask:
    calls: list[tuple[str, str]]

    def __init__(self) -> None:
        self.calls = []

    def delay(self, lab_id: str, actor_id: str) -> None:
        self.calls.append((lab_id, actor_id))


@pytest.mark.asyncio
async def test_start_queues_task_and_sets_starting(
    client: AsyncClient,
    auth_header,
    student_token: str,
    active_template: LabTemplate,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = DummyTask()
    monkeypatch.setattr("app.workers.lab_tasks.start_lab_task", task)
    lab = await client.post(
        "/api/v1/labs",
        headers=auth_header(student_token),
        json={"template_id": str(active_template.id)},
    )

    response = await client.post(f"/api/v1/labs/{lab.json()['id']}/start", headers=auth_header(student_token))

    assert response.status_code == 200
    assert response.json()["status"] == "STARTING"
    assert len(task.calls) == 1


@pytest.mark.asyncio
async def test_stop_only_allowed_from_running(
    client: AsyncClient,
    auth_header,
    student_token: str,
    active_template: LabTemplate,
) -> None:
    lab = await client.post(
        "/api/v1/labs",
        headers=auth_header(student_token),
        json={"template_id": str(active_template.id)},
    )

    response = await client.post(f"/api/v1/labs/{lab.json()['id']}/stop", headers=auth_header(student_token))

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_destroy_allowed_from_created(
    client: AsyncClient,
    auth_header,
    student_token: str,
    active_template: LabTemplate,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = DummyTask()
    monkeypatch.setattr("app.workers.lab_tasks.destroy_lab_task", task)
    lab = await client.post(
        "/api/v1/labs",
        headers=auth_header(student_token),
        json={"template_id": str(active_template.id)},
    )

    response = await client.post(f"/api/v1/labs/{lab.json()['id']}/destroy", headers=auth_header(student_token))

    assert response.status_code == 200
    assert response.json()["status"] == "DESTROYING"
    assert len(task.calls) == 1


@pytest.mark.asyncio
async def test_stop_allowed_from_running(
    client: AsyncClient,
    auth_header,
    student_token: str,
    active_template: LabTemplate,
    session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = DummyTask()
    monkeypatch.setattr("app.workers.lab_tasks.stop_lab_task", task)
    lab = await client.post(
        "/api/v1/labs",
        headers=auth_header(student_token),
        json={"template_id": str(active_template.id)},
    )
    lab_id = lab.json()["id"]
    async with session_factory() as session:
        result = await session.execute(select(LabInstance).where(LabInstance.id == uuid.UUID(lab_id)))
        instance = result.scalar_one()
        instance.status = "RUNNING"
        await session.commit()

    response = await client.post(f"/api/v1/labs/{lab_id}/stop", headers=auth_header(student_token))

    assert response.status_code == 200
    assert response.json()["status"] == "STOPPING"
    assert len(task.calls) == 1
