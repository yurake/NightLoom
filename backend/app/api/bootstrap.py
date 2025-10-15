"""Bootstrap endpoint implementation.

This module provides session bootstrap functionality with LLM integration
and fallback support.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.session import default_session_service
from ..services.observability import observability

router = APIRouter()


class BootstrapRequest(BaseModel):
    initial_character: Optional[str] = None


@router.post("/start")
async def start_session(request: Optional[BootstrapRequest] = None) -> dict[str, object]:
    """Create a new session with bootstrap data."""
    try:
        initial_character = None
        if request and request.initial_character:
            # Validate initial character length
            if len(request.initial_character) > 1:
                initial_character = "あ"  # Use fallback for invalid character
            else:
                initial_character = request.initial_character
        
        # Create session using service
        session = await default_session_service.start_session(initial_character)
        
        # Log session start for observability (after session creation)
        observability.log_session_start(str(session.id), session.initialCharacter, session.themeId)
        
        # Return bootstrap data in expected format
        return {
            "sessionId": str(session.id),
            "axes": [axis.model_dump() for axis in session.axes],
            "keywordCandidates": session.keywordCandidates,
            "initialCharacter": session.initialCharacter,
            "themeId": session.themeId,
            "fallbackUsed": len(session.fallbackFlags) > 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")
