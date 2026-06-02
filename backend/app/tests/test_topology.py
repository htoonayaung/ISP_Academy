import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.ai import AILabBuilderPreview, AILabBuilderPreviewStatus, AILabBuilderValidationStatus
from app.models.lab_instance import LabInstance, LabInstanceStatus, LabNode
from app.models.lab_template import LabTemplate
from app.services.topology_parser import TopologyParser


TWO_ROUTER_YAML = """
name: ospf-demo
topology:
  nodes:
    r1:
      kind: frr
      image: frrouting/frr:latest
      role: router
    r2:
      kind: frr
      image: frrouting/frr:latest
      role: router
  links:
    - endpoints: ["r1:eth1", "r2:eth1"]
      subnet: 10.0.12.0/30
"""


def test_parse_basic_linux_topology() -> None:
    topology = TopologyParser().parse_containerlab_yaml(
        """
name: linux
topology:
  nodes:
    host1:
      kind: linux
      image: alpine:3.20
"""
    )

    assert topology.nodes[0].id == "host1"
    assert topology.nodes[0].kind == "linux"
    assert topology.links == []
    assert "No topology links were found." in topology.warnings


def test_parse_two_router_frr_ospf_topology_links() -> None:
    topology = TopologyParser().parse_containerlab_yaml(TWO_ROUTER_YAML)

    assert [node.id for node in topology.nodes] == ["r1", "r2"]
    assert topology.links[0].source == "r1"
    assert topology.links[0].target == "r2"
    assert topology.links[0].source_interface == "eth1"
    assert topology.links[0].target_interface == "eth1"
    assert topology.links[0].subnet == "10.0.12.0/30"


def test_unknown_endpoint_produces_warning() -> None:
    topology = TopologyParser().parse_containerlab_yaml(
        """
name: bad-link
topology:
  nodes:
    r1:
      kind: frr
      image: frrouting/frr:latest
  links:
    - endpoints: ["r1:eth1", "r9:eth1"]
"""
    )

    assert any("unknown node r9" in warning for warning in topology.warnings)
    assert topology.links[0].target == "r9"


def test_invalid_yaml_returns_friendly_error() -> None:
    with pytest.raises(Exception) as exc_info:
        TopologyParser().parse_containerlab_yaml("topology: [")

    assert "Could not parse topology" in str(exc_info.value)


def test_yaml_is_not_executed(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_run(*args, **kwargs):
        raise AssertionError("Topology parser must not execute shell commands")

    monkeypatch.setattr("subprocess.run", fail_run)

    with pytest.raises(Exception):
        TopologyParser().parse_containerlab_yaml("!!python/object/apply:os.system ['echo unsafe']")


@pytest.mark.asyncio
async def test_lab_template_topology_endpoint(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    active_template: LabTemplate,
) -> None:
    response = await client.get(f"/api/v1/lab-templates/{active_template.id}/topology", headers=auth_header(admin_token))

    assert response.status_code == 200
    assert response.json()["nodes"][0]["id"] == "host1"


@pytest.mark.asyncio
async def test_lab_topology_merges_runtime_node_status(
    client: AsyncClient,
    auth_header,
    student_token: str,
    active_template: LabTemplate,
    session_factory: async_sessionmaker[AsyncSession],
    seeded_users,
) -> None:
    lab = await _create_lab(session_factory, active_template.id, seeded_users["student"].id, "isp-active-lab-topology")
    async with session_factory() as session:
        session.add(
            LabNode(
                lab_instance_id=lab.id,
                name="host1",
                kind="linux",
                container_name="clab-demo-host1",
                management_ipv4="172.20.20.2",
                status="RUNNING",
            )
        )
        await session.commit()

    response = await client.get(f"/api/v1/labs/{lab.id}/topology", headers=auth_header(student_token))

    assert response.status_code == 200
    node = response.json()["nodes"][0]
    assert node["status"] == "RUNNING"
    assert node["management_ipv4"] == "172.20.20.2"
    assert node["container_name"] is None


@pytest.mark.asyncio
async def test_student_cannot_access_another_students_lab_topology(
    client: AsyncClient,
    auth_header,
    student_token: str,
    active_template: LabTemplate,
    session_factory: async_sessionmaker[AsyncSession],
    seeded_users,
) -> None:
    lab = await _create_lab(session_factory, active_template.id, seeded_users["admin"].id, "isp-active-lab-other")

    response = await client.get(f"/api/v1/labs/{lab.id}/topology", headers=auth_header(student_token))

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_student_cannot_access_ai_preview_topology(
    client: AsyncClient,
    auth_header,
    student_token: str,
    session_factory: async_sessionmaker[AsyncSession],
    seeded_users,
) -> None:
    preview = await _create_preview(session_factory, seeded_users["admin"].id)

    response = await client.get(
        f"/api/v1/ai-lab-builder/previews/{preview.id}/topology",
        headers=auth_header(student_token),
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_access_ai_preview_topology(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    session_factory: async_sessionmaker[AsyncSession],
    seeded_users,
) -> None:
    preview = await _create_preview(session_factory, seeded_users["admin"].id)

    response = await client.get(
        f"/api/v1/ai-lab-builder/previews/{preview.id}/topology",
        headers=auth_header(admin_token),
    )

    assert response.status_code == 200
    assert response.json()["nodes"][0]["id"] == "r1"


async def _create_lab(
    session_factory: async_sessionmaker[AsyncSession],
    template_id: uuid.UUID,
    owner_id: uuid.UUID,
    lab_name: str,
) -> LabInstance:
    async with session_factory() as session:
        lab = LabInstance(
            template_id=template_id,
            owner_id=owner_id,
            status=LabInstanceStatus.RUNNING.value,
            lab_name=lab_name,
            lab_directory=f"/tmp/isp-academy-test-labs/instances/{uuid.uuid4()}",
        )
        session.add(lab)
        await session.commit()
        await session.refresh(lab)
        return lab


async def _create_preview(
    session_factory: async_sessionmaker[AsyncSession],
    requested_by: uuid.UUID,
) -> AILabBuilderPreview:
    async with session_factory() as session:
        preview = AILabBuilderPreview(
            requested_by=requested_by,
            prompt="Create OSPF lab",
            lab_plan_json={
                "title": "OSPF Preview",
                "nodes": [
                    {"name": "r1", "kind": "frr", "role": "router", "image": "frrouting/frr:latest"},
                    {"name": "r2", "kind": "frr", "role": "router", "image": "frrouting/frr:latest"},
                ],
                "links": [{"endpoints": ["r1:eth1", "r2:eth1"], "subnet": "10.0.12.0/30"}],
            },
            generated_containerlab_yaml=TWO_ROUTER_YAML,
            generated_configs=[],
            generated_verification_rules=[],
            validation_status=AILabBuilderValidationStatus.PASSED.value,
            validation_errors=[],
            status=AILabBuilderPreviewStatus.VALID.value,
        )
        session.add(preview)
        await session.commit()
        await session.refresh(preview)
        return preview
