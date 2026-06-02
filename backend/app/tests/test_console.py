import subprocess
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.lab_console_adapter import LabConsoleAdapter
from app.models.lab_instance import LabInstance, LabInstanceStatus, LabNode
from app.models.lab_template import LabTemplate


class DummyAsyncResult:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def get(self, timeout: int) -> dict:
        return self.payload


class DummyTask:
    def __init__(self) -> None:
        self.kwargs: dict | None = None

    def apply_async(self, kwargs: dict) -> DummyAsyncResult:
        self.kwargs = kwargs
        return DummyAsyncResult(
            {
                "status": "ok",
                "command": kwargs["command"],
                "stdout": "route output",
                "stderr": "",
                "exit_code": 0,
                "duration_ms": 12,
            }
        )


@pytest.mark.asyncio
async def test_admin_can_list_console_nodes(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    active_template: LabTemplate,
    session_factory: async_sessionmaker[AsyncSession],
    seeded_users,
) -> None:
    lab, node = await _create_running_lab_with_node(session_factory, active_template.id, seeded_users["student"].id)

    response = await client.get(f"/api/v1/labs/{lab.id}/console/nodes", headers=auth_header(admin_token))

    assert response.status_code == 200
    assert response.json()["nodes"][0]["id"] == str(node.id)
    assert response.json()["nodes"][0]["console_type"] == "frr_vtysh"


@pytest.mark.asyncio
async def test_student_can_list_own_lab_console_nodes(
    client: AsyncClient,
    auth_header,
    student_token: str,
    active_template: LabTemplate,
    session_factory: async_sessionmaker[AsyncSession],
    seeded_users,
) -> None:
    lab, _ = await _create_running_lab_with_node(session_factory, active_template.id, seeded_users["student"].id)

    response = await client.get(f"/api/v1/labs/{lab.id}/console/nodes", headers=auth_header(student_token))

    assert response.status_code == 200
    assert len(response.json()["nodes"]) == 1


@pytest.mark.asyncio
async def test_student_cannot_list_another_lab_console_nodes(
    client: AsyncClient,
    auth_header,
    student_token: str,
    active_template: LabTemplate,
    session_factory: async_sessionmaker[AsyncSession],
    seeded_users,
) -> None:
    lab, _ = await _create_running_lab_with_node(session_factory, active_template.id, seeded_users["admin"].id)

    response = await client.get(f"/api/v1/labs/{lab.id}/console/nodes", headers=auth_header(student_token))

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_console_rejects_lab_not_running(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    active_template: LabTemplate,
    session_factory: async_sessionmaker[AsyncSession],
    seeded_users,
) -> None:
    lab, node = await _create_running_lab_with_node(
        session_factory,
        active_template.id,
        seeded_users["student"].id,
        status_value=LabInstanceStatus.STOPPED.value,
    )

    response = await client.post(
        f"/api/v1/labs/{lab.id}/nodes/{node.id}/console/execute",
        headers=auth_header(admin_token),
        json={"command": "show ip route"},
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_console_rejects_unknown_node(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    active_template: LabTemplate,
    session_factory: async_sessionmaker[AsyncSession],
    seeded_users,
) -> None:
    lab, _ = await _create_running_lab_with_node(session_factory, active_template.id, seeded_users["student"].id)

    response = await client.post(
        f"/api/v1/labs/{lab.id}/nodes/{uuid.uuid4()}/console/execute",
        headers=auth_header(admin_token),
        json={"command": "show ip route"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_console_rejects_unsafe_command(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    active_template: LabTemplate,
    session_factory: async_sessionmaker[AsyncSession],
    seeded_users,
) -> None:
    lab, node = await _create_running_lab_with_node(session_factory, active_template.id, seeded_users["student"].id)

    response = await client.post(
        f"/api/v1/labs/{lab.id}/nodes/{node.id}/console/execute",
        headers=auth_header(admin_token),
        json={"command": "show ip route ; docker ps"},
    )

    assert response.status_code == 422
    assert "blocked" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_console_allows_show_ip_route_for_frr(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    active_template: LabTemplate,
    session_factory: async_sessionmaker[AsyncSession],
    seeded_users,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = DummyTask()
    monkeypatch.setattr("app.workers.console_tasks.execute_console_command_task", task)
    lab, node = await _create_running_lab_with_node(session_factory, active_template.id, seeded_users["student"].id)

    response = await client.post(
        f"/api/v1/labs/{lab.id}/nodes/{node.id}/console/execute",
        headers=auth_header(admin_token),
        json={"command": "show ip route"},
    )

    assert response.status_code == 200
    assert response.json()["stdout"] == "route output"
    assert task.kwargs is not None
    assert task.kwargs["command"] == "show ip route"


def test_console_adapter_uses_subprocess_args_without_shell(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    def fake_run(args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)

    result = LabConsoleAdapter().execute_frr("clab-demo-r1", "show ip route")

    assert result.exit_code == 0
    assert captured["args"] == ["docker", "exec", "clab-demo-r1", "vtysh", "-c", "show ip route"]
    assert "shell" not in captured["kwargs"]


def test_console_adapter_limits_output(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(args, **kwargs):
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="x" * 50, stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)

    result = LabConsoleAdapter(output_limit=10).execute_frr("clab-demo-r1", "show ip route")

    assert result.stdout == "x" * 10 + "\n[output truncated]"


def test_batch_command_builds_safe_docker_exec_args(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    def fake_run(args, **kwargs):
        captured["args"] = args
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)

    LabConsoleAdapter().execute_frr_batch("clab-demo-r1", ["configure terminal", "router ospf", "end"])

    assert captured["args"] == [
        "docker",
        "exec",
        "clab-demo-r1",
        "vtysh",
        "-c",
        "configure terminal",
        "-c",
        "router ospf",
        "-c",
        "end",
    ]


async def _create_running_lab_with_node(
    session_factory: async_sessionmaker[AsyncSession],
    template_id: uuid.UUID,
    owner_id: uuid.UUID,
    status_value: str = LabInstanceStatus.RUNNING.value,
) -> tuple[LabInstance, LabNode]:
    async with session_factory() as session:
        lab = LabInstance(
            template_id=template_id,
            owner_id=owner_id,
            status=status_value,
            lab_name=f"isp-console-{uuid.uuid4().hex[:8]}",
            lab_directory=f"/tmp/isp-academy-test-labs/instances/{uuid.uuid4()}",
        )
        session.add(lab)
        await session.flush()
        node = LabNode(
            lab_instance_id=lab.id,
            name="r1",
            kind="frr",
            container_name="clab-demo-r1",
            management_ipv4="172.20.20.2",
            status="RUNNING",
        )
        session.add(node)
        await session.commit()
        await session.refresh(lab)
        await session.refresh(node)
        return lab, node
