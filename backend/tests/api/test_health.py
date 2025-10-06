import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import status

from app.main import app


@pytest.mark.anyio
async def test_health_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}
