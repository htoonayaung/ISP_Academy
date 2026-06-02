from httpx import AsyncClient


async def test_non_admin_cannot_access_demo_status(
    client: AsyncClient,
    instructor_token: str,
    student_token: str,
    auth_header,
) -> None:
    instructor_response = await client.get("/api/v1/admin/demo/status", headers=auth_header(instructor_token))
    student_response = await client.get("/api/v1/admin/demo/status", headers=auth_header(student_token))

    assert instructor_response.status_code == 403
    assert student_response.status_code == 403


async def test_non_admin_cannot_run_demo_setup(
    client: AsyncClient,
    instructor_token: str,
    student_token: str,
    auth_header,
) -> None:
    payload = {"include_linux_demo": True}
    instructor_response = await client.post("/api/v1/admin/demo/setup", headers=auth_header(instructor_token), json=payload)
    student_response = await client.post("/api/v1/admin/demo/setup", headers=auth_header(student_token), json=payload)

    assert instructor_response.status_code == 403
    assert student_response.status_code == 403
