import pytest
from httpx import AsyncClient
from fastapi import status

from app.main import app


@pytest.mark.anyio
async def test_health_endpoint() -> None:
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}
