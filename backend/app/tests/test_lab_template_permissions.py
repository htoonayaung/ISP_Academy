from httpx import AsyncClient

from app.tests.test_lab_templates import VALID_LINUX_YAML


async def test_student_can_list_active_templates_only(
    client: AsyncClient,
    admin_token: str,
    student_token: str,
    auth_header,
) -> None:
    for name, is_active in (("Active Template", True), ("Inactive Template", False)):
        response = await client.post(
            "/api/v1/lab-templates",
            headers=auth_header(admin_token),
            json={
                "name": name,
                "description": "Visibility test.",
                "category": "Linux",
                "difficulty": "Easy",
                "containerlab_yaml": VALID_LINUX_YAML,
                "estimated_cpu": 1,
                "estimated_memory_mb": 256,
                "estimated_duration_minutes": 30,
                "is_active": is_active,
            },
        )
        assert response.status_code == 201

    list_response = await client.get("/api/v1/lab-templates", headers=auth_header(student_token))

    assert list_response.status_code == 200
    names = {item["name"] for item in list_response.json()}
    assert "Active Template" in names
    assert "Inactive Template" not in names


async def test_student_cannot_create_template(
    client: AsyncClient,
    student_token: str,
    auth_header,
) -> None:
    response = await client.post(
        "/api/v1/lab-templates",
        headers=auth_header(student_token),
        json={
            "name": "Student Template",
            "description": "Should be denied.",
            "category": "Linux",
            "difficulty": "Easy",
            "containerlab_yaml": VALID_LINUX_YAML,
            "estimated_cpu": 1,
            "estimated_memory_mb": 256,
            "estimated_duration_minutes": 30,
            "is_active": True,
        },
    )

    assert response.status_code == 403


async def test_instructor_cannot_update_another_instructors_template(
    client: AsyncClient,
    instructor_token: str,
    auth_header,
) -> None:
    create_response = await client.post(
        "/api/v1/lab-templates",
        headers=auth_header(instructor_token),
        json={
            "name": "Owned By Instructor One",
            "description": "Template owned by first instructor.",
            "category": "Linux",
            "difficulty": "Easy",
            "containerlab_yaml": VALID_LINUX_YAML,
            "estimated_cpu": 1,
            "estimated_memory_mb": 256,
            "estimated_duration_minutes": 30,
            "is_active": False,
        },
    )
    template_id = create_response.json()["id"]

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": "instructor2", "password": "InstructorPassword123!"},
    )
    instructor2_token = login_response.json()["access_token"]

    update_response = await client.patch(
        f"/api/v1/lab-templates/{template_id}",
        headers=auth_header(instructor2_token),
        json={"description": "Trying to change another instructor template."},
    )

    assert update_response.status_code == 403


async def test_student_cannot_validate_template(
    client: AsyncClient,
    admin_token: str,
    student_token: str,
    auth_header,
) -> None:
    create_response = await client.post(
        "/api/v1/lab-templates",
        headers=auth_header(admin_token),
        json={
            "name": "Student Validate Denied",
            "description": "Students cannot validate templates.",
            "category": "Linux",
            "difficulty": "Easy",
            "containerlab_yaml": VALID_LINUX_YAML,
            "estimated_cpu": 1,
            "estimated_memory_mb": 256,
            "estimated_duration_minutes": 30,
            "is_active": True,
        },
    )

    response = await client.post(
        f"/api/v1/lab-templates/{create_response.json()['id']}/validate",
        headers=auth_header(student_token),
    )

    assert response.status_code == 403

