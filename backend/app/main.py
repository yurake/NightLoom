"""FastAPI application entry point.

This file wires up the core routers but leaves the actual business
logic to dedicated service modules. During the backend implementation
phase we will flesh out the bootstrap/keyword endpoints and connect
LLM clients.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import bootstrap, keyword

app = FastAPI(title="NightLoom Backend", version="0.1.0")

# CORS configuration for frontend-backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Frontend dev server
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Routers are namespaced for clarity; actual handlers currently return
# placeholder data until the implementation tasks are completed.
app.include_router(bootstrap.router, prefix="/api/sessions", tags=["session"])
app.include_router(keyword.router, prefix="/api/sessions", tags=["session"])


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Simple health check endpoint used by monitoring / CI."""

    return {"status": "ok"}
