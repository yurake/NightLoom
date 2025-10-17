"""FastAPI application entry point.

This file wires up the core routers but leaves the actual business
logic to dedicated service modules. During the backend implementation
phase we will flesh out the bootstrap/keyword endpoints and connect
LLM clients.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import ValidationError

from .api import bootstrap, keyword, scenes, choices, results
from .services.observability import observability_service
from .middleware.security import get_security_headers, cleanup_expired_data

app = FastAPI(
    title="NightLoom Backend",
    version="0.1.0",
    docs_url="/docs" if __debug__ else None,  # Disable docs in production
    redoc_url="/redoc" if __debug__ else None
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "testserver", "*.nightloom.app"]  # Configure for production
)

# Custom error handler for validation errors to include error_code field
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with custom error_code field."""
    errors = exc.errors()
    
    # Extract field information from validation errors
    fields = []
    for error in errors:
        if 'loc' in error and len(error['loc']) > 0:
            field_name = str(error['loc'][-1])  # Get the last part of the location path
            fields.append(field_name)
    
    # Check if this is a UUID validation error (should return 400 instead of 422)
    for error in errors:
        if error.get('type') == 'uuid_parsing' or 'uuid' in error.get('type', '').lower():
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": "VALIDATION_ERROR",
                    "message": "Invalid UUID format",
                    "details": {
                        "field": fields[0] if fields else "session_id",
                        "errors": errors,
                        "timestamp": observability_service.get_current_timestamp()
                    }
                }
            )
    
    return JSONResponse(
        status_code=422,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": "Validation failed",
            "details": {
                "field": fields[0] if fields else "unknown",
                "errors": errors,
                "timestamp": observability_service.get_current_timestamp()
            }
        }
    )

# CORS configuration for frontend-backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Frontend dev server
        "http://127.0.0.1:3000",
        # Add production origins as needed
        # "https://nightloom.app",
        # "https://www.nightloom.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["X-Request-ID"],
    max_age=86400,  # Cache preflight requests for 24 hours
)

# Routers are namespaced for clarity; actual handlers currently return
# placeholder data until the implementation tasks are completed.
app.include_router(bootstrap.router, prefix="/api/sessions", tags=["session"])
app.include_router(keyword.router, prefix="/api/sessions", tags=["session"])
app.include_router(scenes.router, tags=["scenes"])
app.include_router(choices.router, tags=["choices"])
app.include_router(results.router, tags=["results"])


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    
    # Add security headers
    security_headers = get_security_headers()
    for header, value in security_headers.items():
        response.headers[header] = value
    
    return response

@app.middleware("http")
async def cleanup_middleware(request: Request, call_next):
    """Periodic cleanup of expired security data."""
    import random
    
    # Run cleanup on ~1% of requests to avoid performance impact
    if random.random() < 0.01:
        cleanup_expired_data()
    
    response = await call_next(request)
    return response

@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Simple health check endpoint used by monitoring / CI."""
    return {"status": "ok", "timestamp": observability_service.get_current_timestamp()}

@app.get("/security-stats", tags=["admin"])
async def security_stats():
    """Get security statistics (admin only in production)."""
    from .middleware.security import get_security_stats
    return get_security_stats()
