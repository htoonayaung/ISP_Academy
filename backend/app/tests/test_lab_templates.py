from httpx import AsyncClient


VALID_LINUX_YAML = """
name: basic-linux
topology:
  nodes:
    host1:
      kind: linux
      image: alpine:latest
    host2:
      kind: linux
      image: alpine:latest
  links:
    - endpoints:
        - host1:eth1
        - host2:eth1
"""


async def test_admin_can_create_template(
    client: AsyncClient,
    admin_token: str,
    auth_header,
) -> None:
    response = await client.post(
        "/api/v1/lab-templates",
        headers=auth_header(admin_token),
        json={
            "name": "Basic Linux",
            "description": "Two Linux nodes connected together.",
            "category": "Linux",
            "difficulty": "Easy",
            "containerlab_yaml": VALID_LINUX_YAML,
            "default_startup_config": None,
            "estimated_cpu": 1,
            "estimated_memory_mb": 256,
            "estimated_duration_minutes": 30,
            "is_active": True,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["slug"] == "basic-linux"
    assert payload["is_active"] is True


async def test_instructor_can_create_template(
    client: AsyncClient,
    instructor_token: str,
    auth_header,
) -> None:
    response = await client.post(
        "/api/v1/lab-templates",
        headers=auth_header(instructor_token),
        json={
            "name": "Instructor Linux",
            "description": "Instructor-owned Linux template.",
            "category": "Linux",
            "difficulty": "Easy",
            "containerlab_yaml": VALID_LINUX_YAML,
            "estimated_cpu": 1,
            "estimated_memory_mb": 256,
            "estimated_duration_minutes": 30,
            "is_active": False,
        },
    )

    assert response.status_code == 201
    assert response.json()["created_by"]


async def test_admin_can_validate_template(
    client: AsyncClient,
    admin_token: str,
    auth_header,
) -> None:
    create_response = await client.post(
        "/api/v1/lab-templates",
        headers=auth_header(admin_token),
        json={
            "name": "Validate Linux",
            "description": "Template to validate.",
            "category": "Linux",
            "difficulty": "Easy",
            "containerlab_yaml": VALID_LINUX_YAML,
            "estimated_cpu": 1,
            "estimated_memory_mb": 256,
            "estimated_duration_minutes": 30,
            "is_active": True,
        },
    )

    template_id = create_response.json()["id"]
    response = await client.post(
        f"/api/v1/lab-templates/{template_id}/validate",
        headers=auth_header(admin_token),
    )

    assert response.status_code == 200
    assert response.json()["is_valid"] is True
    assert response.json()["errors"] == []

