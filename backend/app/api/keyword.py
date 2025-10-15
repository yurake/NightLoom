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
        raise HTTPException(status_code=400, detail=f"Invalid session ID format: {str(e)}")
    except Exception as e:
        # Log error for observability
        observability.log_error(session_uuid if 'session_uuid' in locals() else None,
                               "keyword_confirmation_error", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to confirm keyword: {str(e)}")
