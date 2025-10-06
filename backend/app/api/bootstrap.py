"""Bootstrap endpoint skeleton.

This module will be extended to call the axis generator service and
LLM once those components are implemented.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/bootstrap")
async def get_session_bootstrap() -> dict[str, object]:
    """Return placeholder session bootstrap metadata."""

    # NOTE: Implementation will be replaced with real data once the
    # axis generation and seed word selection logic is ready.
    return {
        "sessionId": "placeholder",
        "axes": [],
        "suggestions": [],
        "allowFreeInput": True,
    }
