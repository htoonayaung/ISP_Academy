import inspect
import uuid
from pathlib import Path

import pytest
import yaml

from app.adapters.containerlab_adapter import ContainerlabAdapter
from app.lab_runtime.status_parser import parse_containerlab_nodes
from app.models.lab_instance import LabInstance


def test_adapter_rejects_paths_outside_lab_root(tmp_path: Path) -> None:
    adapter = ContainerlabAdapter(lab_root=str(tmp_path / "labs"))

    with pytest.raises(ValueError):
        adapter.validate_lab_path(tmp_path / "outside" / "clab.yml")


def test_adapter_does_not_use_shell_true() -> None:
    source = inspect.getsource(ContainerlabAdapter._run)

    assert "shell=True" not in source


def test_save_lab_file_stays_inside_lab_root(tmp_path: Path) -> None:
    lab_root = tmp_path / "labs"
    lab_directory = lab_root / "instances" / "lab1"
    adapter = ContainerlabAdapter(lab_root=str(lab_root))
    lab = LabInstance(
        template_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        owner_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
        lab_name="isp-test",
        lab_directory=str(lab_directory),
    )

    path = adapter.save_lab_file(lab, yaml.safe_dump({"name": "isp-test", "topology": {"nodes": {}}}))

    assert path == lab_directory / "clab.yml"
    assert path.exists()


def test_api_container_has_no_docker_socket_mount() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    compose_path = repo_root / "deployments/docker-compose.yml"
    if not compose_path.exists():
        pytest.skip("docker-compose.yml is outside the backend image build context")
    compose = compose_path.read_text(encoding="utf-8")
    backend_block = compose.split("  celery_worker:", 1)[0]

    assert "/var/run/docker.sock" not in backend_block


def test_status_parser_handles_containerlab_lab_name_map() -> None:
    nodes = parse_containerlab_nodes(
        uuid.UUID("00000000-0000-0000-0000-000000000003"),
        {
            "lab-name": [
                {
                    "name": "clab-lab-host1",
                    "kind": "linux",
                    "state": "running",
                    "ipv4_address": "172.20.20.2/24",
                }
            ]
        },
    )

    assert len(nodes) == 1
    assert nodes[0].name == "clab-lab-host1"
    assert nodes[0].management_ipv4 == "172.20.20.2/24"
