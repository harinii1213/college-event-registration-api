import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch

from main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def auth_headers():
    return {
        "Authorization": "Bearer test-token"
    }


# ---------------------------------------------------------
# 1. Main Workflow - Health Check
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "success"


# ---------------------------------------------------------
# 2. Validation Failure
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_create_event_validation_failure(client):
    response = await client.post(
        "/events",
        json={
            "name": "",
            "description": "",
            "date": "",
            "venue": ""
        }
    )

    assert response.status_code == 422


# ---------------------------------------------------------
# 3. Authorization Boundary
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_unauthorized_event_access(client):
    fake_event = type(
        "FakeEvent",
        (),
        {
            "id": 1,
            "name": "Test Event",
            "description": "Test Description",
            "date": "2026-09-20",
            "venue": "College Hall",
            "owner_username": "another_user",
        },
    )()

    with patch(
        "main.get_current_user",
        new=AsyncMock(return_value="current_user")
    ), patch(
        "main.event_service.get_event",
        new=AsyncMock(return_value=fake_event)
    ):
        response = await client.get(
            "/events/1",
            headers={"Authorization": "Bearer fake-token"},
        )

    assert response.status_code == 403
    assert "not authorized" in response.json()["detail"].lower()


# ---------------------------------------------------------
# 4. Service Failure
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_service_failure(client):
    with patch(
        "main.get_current_user",
        new=AsyncMock(return_value="admin")
    ), patch(
        "main.event_service.get_events",
        new=AsyncMock(side_effect=Exception("Database service failure"))
    ):
        response = await client.get(
            "/events",
            headers={"Authorization": "Bearer fake-token"},
        )

    assert response.status_code == 500
    assert "Failed to retrieve events" in response.json()["detail"]