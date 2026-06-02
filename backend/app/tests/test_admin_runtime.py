import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.lab_runtime.directory_manager import LabDirectoryManager
from app.models.lab_instance import LabInstance, LabInstanceStatus
from app.models.lab_template import LabTemplate
from app.repositories.labs import LabRepository
from app.services.admin_runtime_service import AdminRuntimeService


class DummyTask:
    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []

    def delay(self, *args: str) -> None:
        self.calls.append(tuple(args))


@pytest.mark.asyncio
async def test_non_admin_cannot_access_runtime_status(
    client: AsyncClient,
    auth_header,
    student_token: str,
) -> None:
    response = await client.get("/api/v1/admin/runtime/labs/status", headers=auth_header(student_token))

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_access_runtime_status(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    active_template: LabTemplate,
    session_factory: async_sessionmaker[AsyncSession],
    seeded_users,
) -> None:
    await _create_lab(session_factory, active_template.id, seeded_users["student"].id, "isp-demo-visible", LabInstanceStatus.RUNNING.value)

    response = await client.get("/api/v1/admin/runtime/labs/status", headers=auth_header(admin_token))

    assert response.status_code == 200
    data = response.json()
    assert data["status_counts"]["RUNNING"] == 1
    assert data["demo_labs"][0]["lab_name"] == "isp-demo-visible"
    assert data["containers"]["source"] == "database-and-worker-refreshed-node-cache"


@pytest.mark.asyncio
async def test_mark_failed_requires_confirmation(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    active_template: LabTemplate,
    session_factory: async_sessionmaker[AsyncSession],
    seeded_users,
) -> None:
    lab = await _create_lab(
        session_factory,
        active_template.id,
        seeded_users["student"].id,
        "isp-demo-stuck",
        LabInstanceStatus.STARTING.value,
        minutes_old=30,
    )

    response = await client.post(
        f"/api/v1/admin/runtime/labs/{lab.id}/recover",
        headers=auth_header(admin_token),
        json={"action": "mark_failed", "confirm": "NOPE"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_mark_failed_changes_stuck_lab_status(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    active_template: LabTemplate,
    session_factory: async_sessionmaker[AsyncSession],
    seeded_users,
) -> None:
    lab = await _create_lab(
        session_factory,
        active_template.id,
        seeded_users["student"].id,
        "isp-demo-stuck-mark",
        LabInstanceStatus.DESTROYING.value,
        minutes_old=30,
    )

    response = await client.post(
        f"/api/v1/admin/runtime/labs/{lab.id}/recover",
        headers=auth_header(admin_token),
        json={"action": "mark_failed", "confirm": "RECOVER_LAB"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "FAILED"


@pytest.mark.asyncio
async def test_retry_destroy_requires_confirmation(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    active_template: LabTemplate,
    session_factory: async_sessionmaker[AsyncSession],
    seeded_users,
) -> None:
    lab = await _create_lab(session_factory, active_template.id, seeded_users["student"].id, "isp-demo-retry", LabInstanceStatus.FAILED.value)

    response = await client.post(
        f"/api/v1/admin/runtime/labs/{lab.id}/recover",
        headers=auth_header(admin_token),
        json={"action": "retry_destroy", "confirm": ""},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_retry_destroy_queues_worker_task(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    active_template: LabTemplate,
    session_factory: async_sessionmaker[AsyncSession],
    seeded_users,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = DummyTask()
    monkeypatch.setattr("app.workers.lab_tasks.destroy_lab_task", task)
    lab = await _create_lab(session_factory, active_template.id, seeded_users["student"].id, "isp-demo-retry-ok", LabInstanceStatus.FAILED.value)

    response = await client.post(
        f"/api/v1/admin/runtime/labs/{lab.id}/recover",
        headers=auth_header(admin_token),
        json={"action": "retry_destroy", "confirm": "RECOVER_LAB"},
    )

    assert response.status_code == 200
    assert response.json()["queued_task"] is True
    assert len(task.calls) == 1


@pytest.mark.asyncio
async def test_force_destroy_demo_only_rejects_non_demo_lab(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    active_template: LabTemplate,
    session_factory: async_sessionmaker[AsyncSession],
    seeded_users,
) -> None:
    lab = await _create_lab(session_factory, active_template.id, seeded_users["student"].id, "isp-active-lab-abcd", LabInstanceStatus.FAILED.value)

    response = await client.post(
        f"/api/v1/admin/runtime/labs/{lab.id}/recover",
        headers=auth_header(admin_token),
        json={"action": "force_destroy_demo_only", "confirm": "RECOVER_LAB"},
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_cleanup_demo_requires_confirmation(
    client: AsyncClient,
    auth_header,
    admin_token: str,
) -> None:
    response = await client.post(
        "/api/v1/admin/runtime/cleanup/demo",
        headers=auth_header(admin_token),
        json={"confirm": "NOPE"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_student_forbidden_from_cleanup_demo(
    client: AsyncClient,
    auth_header,
    student_token: str,
) -> None:
    response = await client.post(
        "/api/v1/admin/runtime/cleanup/demo",
        headers=auth_header(student_token),
        json={"confirm": "CLEANUP_DEMO_RUNTIME"},
    )

    assert response.status_code == 403


def test_cleanup_demo_lab_directory_never_removes_outside_lab_root(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    marker = outside / "keep.txt"
    marker.write_text("keep", encoding="utf-8")
    lab = LabInstance(
        template_id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        lab_name="isp-demo-outside",
        lab_directory=str(outside),
        status=LabInstanceStatus.DESTROYED.value,
    )
    service = AdminRuntimeService(
        LabRepository(None),  # type: ignore[arg-type]
        directory_manager=LabDirectoryManager(lab_root=str(tmp_path / "lab-root")),
    )

    with pytest.raises(ValueError):
        service.cleanup_demo_lab_directory(lab)

    assert marker.exists()


@pytest.mark.asyncio
async def test_runtime_status_does_not_require_docker_socket(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_subprocess(*args, **kwargs):
        raise AssertionError("Runtime status API must not execute Docker or Containerlab")

    monkeypatch.setattr("subprocess.run", fail_subprocess)

    response = await client.get("/api/v1/admin/runtime/labs/status", headers=auth_header(admin_token))

    assert response.status_code == 200


async def _create_lab(
    session_factory: async_sessionmaker[AsyncSession],
    template_id: uuid.UUID,
    owner_id: uuid.UUID,
    lab_name: str,
    status_value: str,
    minutes_old: int = 0,
) -> LabInstance:
    async with session_factory() as session:
        timestamp = datetime.now(UTC) - timedelta(minutes=minutes_old)
        lab = LabInstance(
            template_id=template_id,
            owner_id=owner_id,
            status=status_value,
            lab_name=lab_name,
            lab_directory=f"/tmp/isp-academy-test-labs/instances/{uuid.uuid4()}",
            created_at=timestamp,
            updated_at=timestamp,
        )
        session.add(lab)
        await session.commit()
        await session.refresh(lab)
        return lab
