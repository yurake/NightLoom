"""Keyword confirmation endpoint implementation."""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.session import default_session_service
from ..services.observability import observability

router = APIRouter()


class KeywordRequest(BaseModel):
    keyword: str
    source: str  # 'suggestion' | 'manual'


@router.post("/{session_id}/keyword")
async def post_session_keyword(session_id: str, request: KeywordRequest) -> dict[str, object]:
    """Accept a keyword and return first scene data."""
    try:
        import time
        from uuid import UUID
        
        start_time = time.time()
        
        # Convert string session_id to UUID
        session_uuid = UUID(session_id)
        
        # Use session service to confirm keyword and get first scene
        first_scene = await default_session_service.confirm_keyword(
            session_uuid, request.keyword, request.source
        )
        
        # Calculate latency for observability
        latency_ms = (time.time() - start_time) * 1000
        
        # Log keyword confirmation for observability
        observability.log_keyword_confirmation(
            session_uuid, request.keyword, request.source, latency_ms
        )
        
        return {
            "sessionId": session_id,
            "scene": first_scene.model_dump() if first_scene else None,
            "fallbackUsed": False  # TODO: Get from session service
        }
        
    except ValueError as e:
        # Check if this is a UUID parsing error vs session state error
        error_msg = str(e)
        if ("invalid" in error_msg.lower() and "uuid" in error_msg.lower()) or "badly formed hexadecimal" in error_msg.lower():
            # This is a UUID parsing error - return 400
            raise HTTPException(
                status_code=400,
                detail=f"Invalid session ID format: {str(e)}"
            )
        elif "state" in error_msg.lower() and ("required" in error_msg.lower() or "init" in error_msg.lower()):
            # This is a session state error - return 500
            raise HTTPException(
                status_code=500,
                detail=f"Session state error: {str(e)}"
            )
        else:
            # Default to 400 for other ValueError cases (likely validation)
            raise HTTPException(
                status_code=400,
                detail=f"Invalid session ID format: {str(e)}"
            )
    except Exception as e:
        # Log error for observability
        observability.log_error(session_uuid if 'session_uuid' in locals() else None,
                               "keyword_confirmation_error", str(e))
        
        # Import SessionServiceError for proper exception handling
        from app.services.session import SessionServiceError, InvalidSessionStateError
        
        # Check if keyword validation failed
        if isinstance(e, SessionServiceError) and "Invalid keyword length" in str(e):
            raise HTTPException(
                status_code=500,
                detail=f"Invalid keyword: {str(e)}"
            )
        
        # Check for session state errors (no longer INIT) - including ValueError from SessionGuard
        if (isinstance(e, InvalidSessionStateError) or
            isinstance(e, ValueError) or
            "require_state" in str(e).lower() or
            "required" in str(e).lower() or
            "state" in str(e).lower()):
            raise HTTPException(
                status_code=500,
                detail=f"Session state error: {str(e)}"
            )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to confirm keyword: {str(e)}"
        )
