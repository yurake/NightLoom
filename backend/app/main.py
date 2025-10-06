"""FastAPI application entry point.

This file wires up the core routers but leaves the actual business
logic to dedicated service modules. During the backend implementation
phase we will flesh out the bootstrap/keyword endpoints and connect
LLM clients.
"""

from fastapi import FastAPI

from .api import bootstrap, keyword

app = FastAPI(title="NightLoom Backend", version="0.1.0")

# Routers are namespaced for clarity; actual handlers currently return
# placeholder data until the implementation tasks are completed.
app.include_router(bootstrap.router, prefix="/session", tags=["session"])
app.include_router(keyword.router, prefix="/session", tags=["session"])


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Simple health check endpoint used by monitoring / CI."""

    return {"status": "ok"}
