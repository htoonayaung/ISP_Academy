import uuid
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.containerlab_adapter import ContainerlabAdapter
from app.lab_runtime.directory_manager import LabDirectoryManager
from app.models.lab_instance import LabEvent, LabInstance, LabInstanceStatus
from app.models.lab_template import LabTemplate
from app.repositories.labs import LabRepository
from app.workers.lab_tasks import _destroy_lab, _start_lab, _stop_lab


@pytest.mark.asyncio
async def test_student_lab_events_hide_operational_output(
    client: AsyncClient,
    auth_header,
    student_token: str,
    active_template: LabTemplate,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    lab_response = await client.post(
        "/api/v1/labs",
        headers=auth_header(student_token),
        json={"template_id": str(active_template.id)},
    )
    lab_id = uuid.UUID(lab_response.json()["id"])
    async with session_factory() as session:
        repository = LabRepository(session)
        await repository.add_event(
            LabEvent(
                lab_instance_id=lab_id,
                event_type="LAB_FAILED",
                message="Containerlab deploy failed",
                stdout="/opt/isp-academy/lab-storage/internal",
                stderr="Traceback at /var/run/docker.sock",
            )
        )
        await repository.commit()

    response = await client.get(f"/api/v1/labs/{lab_id}/events", headers=auth_header(student_token))

    assert response.status_code == 200
    failed_event = next(event for event in response.json() if event["event_type"] == "LAB_FAILED")
    assert failed_event["message"] == "Lab operation failed. Ask an instructor to review details."
    assert failed_event["stdout"] is None
    assert failed_event["stderr"] is None


@pytest.mark.asyncio
async def test_admin_lab_events_keep_operational_output(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    student_token: str,
    active_template: LabTemplate,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    lab_response = await client.post(
        "/api/v1/labs",
        headers=auth_header(student_token),
        json={"template_id": str(active_template.id)},
    )
    lab_id = uuid.UUID(lab_response.json()["id"])
    async with session_factory() as session:
        repository = LabRepository(session)
        await repository.add_event(
            LabEvent(
                lab_instance_id=lab_id,
                event_type="LAB_FAILED",
                message="Containerlab deploy failed",
                stdout="operator detail",
                stderr="stderr detail",
            )
        )
        await repository.commit()

    response = await client.get(f"/api/v1/labs/{lab_id}/events", headers=auth_header(admin_token))

    assert response.status_code == 200
    failed_event = next(event for event in response.json() if event["event_type"] == "LAB_FAILED")
    assert failed_event["stdout"] == "operator detail"
    assert failed_event["stderr"] == "stderr detail"


def test_directory_manager_rejects_traversal_outside_lab_root(tmp_path: Path) -> None:
    manager = LabDirectoryManager(lab_root=str(tmp_path / "labs"))

    with pytest.raises(ValueError):
        manager.validate_inside_lab_root(tmp_path / "labs" / ".." / "outside")


def test_adapter_rejects_lab_directory_traversal(tmp_path: Path) -> None:
    lab_root = tmp_path / "labs"
    adapter = ContainerlabAdapter(lab_root=str(lab_root))
    lab = LabInstance(
        template_id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        lab_name="isp-test",
        lab_directory=str(lab_root / ".." / "outside"),
    )

    with pytest.raises(ValueError):
        adapter.save_lab_file(lab, "name: safe\n")


@pytest.mark.asyncio
async def test_two_labs_from_same_template_get_unique_names(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    student_token: str,
    active_template: LabTemplate,
) -> None:
    first = await client.post(
        "/api/v1/labs",
        headers=auth_header(student_token),
        json={"template_id": str(active_template.id)},
    )
    second = await client.post(
        "/api/v1/labs",
        headers=auth_header(admin_token),
        json={"template_id": str(active_template.id)},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["lab_name"] != second.json()["lab_name"]


@pytest.mark.asyncio
async def test_duplicate_start_request_is_rejected(
    client: AsyncClient,
    auth_header,
    student_token: str,
    active_template: LabTemplate,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class DummyTask:
        def delay(self, lab_id: str, actor_id: str) -> None:
            return None

    monkeypatch.setattr("app.workers.lab_tasks.start_lab_task", DummyTask())
    lab = await client.post(
        "/api/v1/labs",
        headers=auth_header(student_token),
        json={"template_id": str(active_template.id)},
    )
    lab_id = lab.json()["id"]

    first = await client.post(f"/api/v1/labs/{lab_id}/start", headers=auth_header(student_token))
    second = await client.post(f"/api/v1/labs/{lab_id}/start", headers=auth_header(student_token))

    assert first.status_code == 200
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_worker_tasks_skip_unexpected_states(
    session_factory: async_sessionmaker[AsyncSession],
    active_template: LabTemplate,
    seeded_users,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr("app.workers.lab_tasks.async_session_factory", session_factory)

    class Adapter:
        def deploy(self, lab):
            calls.append("deploy")

        def destroy(self, lab):
            calls.append("destroy")

    monkeypatch.setattr("app.workers.lab_tasks.ContainerlabAdapter", Adapter)
    async with session_factory() as session:
        lab = LabInstance(
            template_id=active_template.id,
            owner_id=seeded_users["student"].id,
            status=LabInstanceStatus.CREATED.value,
            lab_name="isp-hardening-test",
            lab_directory="/tmp/isp-academy-test-labs/instances/hardening",
        )
        session.add(lab)
        await session.commit()
        await session.refresh(lab)
        lab_id = lab.id

    await _start_lab(lab_id, seeded_users["student"].id)
    await _stop_lab(lab_id, seeded_users["student"].id)
    await _destroy_lab(lab_id, seeded_users["student"].id)

    assert calls == []
