import subprocess

from httpx import AsyncClient


async def test_invalid_yaml_is_rejected(
    client: AsyncClient,
    admin_token: str,
    auth_header,
) -> None:
    response = await client.post(
        "/api/v1/lab-templates",
        headers=auth_header(admin_token),
        json={
            "name": "Invalid YAML",
            "description": "Invalid YAML should be rejected.",
            "category": "Linux",
            "difficulty": "Easy",
            "containerlab_yaml": "name: [broken",
            "estimated_cpu": 1,
            "estimated_memory_mb": 256,
            "estimated_duration_minutes": 30,
            "is_active": True,
        },
    )

    assert response.status_code == 422


async def test_host_mounts_are_rejected(
    client: AsyncClient,
    admin_token: str,
    auth_header,
) -> None:
    raw_yaml = """
name: mount-test
topology:
  nodes:
    host1:
      kind: linux
      image: alpine:latest
      binds:
        - /etc:/host-etc
"""
    response = await client.post(
        "/api/v1/lab-templates",
        headers=auth_header(admin_token),
        json={
            "name": "Mount Test",
            "description": "Host mounts should be rejected.",
            "category": "Linux",
            "difficulty": "Easy",
            "containerlab_yaml": raw_yaml,
            "estimated_cpu": 1,
            "estimated_memory_mb": 256,
            "estimated_duration_minutes": 30,
            "is_active": True,
        },
    )

    assert response.status_code == 422
    assert "forbidden host mount" in response.text


async def test_privileged_containers_are_rejected_by_default(
    client: AsyncClient,
    admin_token: str,
    auth_header,
) -> None:
    raw_yaml = """
name: privileged-test
topology:
  nodes:
    host1:
      kind: linux
      image: alpine:latest
      privileged: true
"""
    response = await client.post(
        "/api/v1/lab-templates",
        headers=auth_header(admin_token),
        json={
            "name": "Privileged Test",
            "description": "Privileged mode should be rejected.",
            "category": "Linux",
            "difficulty": "Easy",
            "containerlab_yaml": raw_yaml,
            "estimated_cpu": 1,
            "estimated_memory_mb": 256,
            "estimated_duration_minutes": 30,
            "is_active": True,
        },
    )

    assert response.status_code == 422
    assert "privileged mode" in response.text


async def test_non_allowlisted_images_are_rejected(
    client: AsyncClient,
    admin_token: str,
    auth_header,
) -> None:
    raw_yaml = """
name: image-test
topology:
  nodes:
    r1:
      kind: linux
      image: ghcr.io/vendor/random-network-image:latest
"""
    response = await client.post(
        "/api/v1/lab-templates",
        headers=auth_header(admin_token),
        json={
            "name": "Image Test",
            "description": "Non-allowlisted images should be rejected.",
            "category": "Linux",
            "difficulty": "Easy",
            "containerlab_yaml": raw_yaml,
            "estimated_cpu": 1,
            "estimated_memory_mb": 256,
            "estimated_duration_minutes": 30,
            "is_active": True,
        },
    )

    assert response.status_code == 422
    assert "non-allowlisted image" in response.text


async def test_validation_does_not_execute_containerlab(
    client: AsyncClient,
    admin_token: str,
    auth_header,
    monkeypatch,
) -> None:
    def fail_if_called(*args, **kwargs):
        raise AssertionError("Phase 3 must not execute subprocess or Containerlab")

    monkeypatch.setattr(subprocess, "run", fail_if_called)
    raw_yaml = """
name: no-exec-test
topology:
  nodes:
    host1:
      kind: linux
      image: alpine:latest
"""
    response = await client.post(
        "/api/v1/lab-templates",
        headers=auth_header(admin_token),
        json={
            "name": "No Exec Test",
            "description": "Validator should parse only.",
            "category": "Linux",
            "difficulty": "Easy",
            "containerlab_yaml": raw_yaml,
            "estimated_cpu": 1,
            "estimated_memory_mb": 256,
            "estimated_duration_minutes": 30,
            "is_active": True,
        },
    )

    assert response.status_code == 201

