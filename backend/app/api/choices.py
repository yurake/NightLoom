"""
Choice submission API endpoints for NightLoom MVP.

Provides endpoints for submitting user choices during diagnosis flow.
"""

from fastapi import APIRouter, HTTPException, Path, Body
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Dict, Any, Optional

from app.services.session import default_session_service, SessionNotFoundError, InvalidSessionStateError, SessionServiceError
from app.services.observability import observability_service

router = APIRouter(tags=["choices"])


class ChoiceSubmission(BaseModel):
    """Request model for choice submission."""
    choiceId: str = Field(..., min_length=1, description="ID of the selected choice")


@router.post("/{session_id}/scenes/{scene_index}/choice")
async def submit_choice(
    session_id: UUID = Path(..., description="Session identifier"),
    scene_index: int = Path(..., ge=1, le=4, description="Scene number (1-4)"),
    choice_data: ChoiceSubmission = Body(..., description="Choice selection data")
) -> Dict[str, Any]:
    """
    Submit user choice for the specified scene.
    
    Args:
        session_id: UUID of the active session
        scene_index: Current scene number (1-4)
        choice_ Choice submission containing choiceId
        
    Returns:
        Choice submission result with next scene data (if available)
        
    Raises:
        404: Session not found
        400: Invalid session state or scene index
        422: Invalid choice data
        503: LLM service unavailable
    """
    # Start performance tracking
    start_time = observability_service.start_timer("choice_submission")
    
    try:
        # Validate choice ID format
        choice_id = choice_data.choiceId
        if not _validate_choice_id_format(choice_id, scene_index):
            observability_service.increment_counter("choice_submission_invalid_format")
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "VALIDATION_ERROR",
                    "message": "Invalid choice ID format",
                    "details": {
                        "field": "choiceId",
                        "expected": f"choice_{scene_index}_[1-4]",
                        "provided": choice_id,
                        "session_id": str(session_id),
                        "timestamp": observability_service.get_current_timestamp()
                    }
                }
            )
        
        # Submit choice and get next scene
        next_scene = default_session_service.record_choice(session_id, scene_index, choice_id)
        
        # Track success metrics
        observability_service.increment_counter("choice_submission_success")
        observability_service.record_latency("choice_submission", start_time)
        
        # Prepare response
        response = {
            "sessionId": str(session_id),
            "sceneCompleted": True
        }
        
        # Include next scene if available
        if next_scene:
            response["nextScene"] = {
                "sceneIndex": next_scene.sceneIndex,
                "themeId": next_scene.themeId,
                "narrative": next_scene.narrative,
                "choices": [
                    {
                        "id": choice.id,
                        "text": choice.text,
                        "weights": choice.weights
                    }
                    for choice in next_scene.choices
                ]
            }
        else:
            response["nextScene"] = None
            
        return response
        
    except SessionNotFoundError:
        observability_service.increment_counter("choice_submission_session_not_found")
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "SESSION_NOT_FOUND",
                "message": "Session not found or has expired",
                "details": {
                    "session_id": str(session_id),
                    "timestamp": observability_service.get_current_timestamp()
                }
            }
        )
        
    except InvalidSessionStateError as e:
        observability_service.increment_counter("choice_submission_invalid_state")
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "BAD_REQUEST",
                "message": "Session is not in valid state for choice submission",
                "details": {
                    "session_id": str(session_id),
                    "scene_index": scene_index,
                    "choice_id": choice_id,
                    "error": str(e),
                    "timestamp": observability_service.get_current_timestamp()
                }
            }
        )
        
    except ValueError as e:
        # Handle choice validation errors
        error_msg = str(e)
        if "Invalid choice" in error_msg or "choice ID" in error_msg:
            observability_service.increment_counter("choice_submission_invalid_choice")
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "VALIDATION_ERROR",
                    "message": "Invalid choice for this scene",
                    "details": {
                        "field": "choiceId",
                        "session_id": str(session_id),
                        "scene_index": scene_index,
                        "choice_id": choice_id,
                        "error": error_msg,
                        "timestamp": observability_service.get_current_timestamp()
                    }
                }
            )
        elif "cannot access scene" in error_msg or "Scene" in error_msg and "not found" in error_msg:
            observability_service.increment_counter("choice_submission_invalid_scene")
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "BAD_REQUEST",
                    "message": f"Session cannot access scene {scene_index}",
                    "details": {
                        "session_id": str(session_id),
                        "scene_index": scene_index,
                        "choice_id": choice_id,
                        "error": error_msg,
                        "timestamp": observability_service.get_current_timestamp()
                    }
                }
            )
        elif "already completed" in error_msg:
            observability_service.increment_counter("choice_submission_already_completed")
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "BAD_REQUEST",
                    "message": f"Scene {scene_index} has already been completed",
                    "details": {
                        "session_id": str(session_id),
                        "scene_index": scene_index,
                        "choice_id": choice_id,
                        "error": error_msg,
                        "timestamp": observability_service.get_current_timestamp()
                    }
                }
            )
        else:
            # Re-raise other ValueError exceptions as 400 for validation errors
            observability_service.increment_counter("choice_submission_unexpected_error")
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "BAD_REQUEST",
                    "message": "Invalid choice submission",
                    "details": {
                        "session_id": str(session_id),
                        "scene_index": scene_index,
                        "choice_id": choice_id,
                        "error": str(e),
                        "timestamp": observability_service.get_current_timestamp()
                    }
                }
            )
            
    except SessionServiceError as e:
        if "Scene" in str(e) and ("not found" in str(e) or "not accessible" in str(e)):
            observability_service.increment_counter("choice_submission_invalid_scene")
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "INVALID_SCENE_INDEX",
                    "message": f"Scene {scene_index} is not accessible for choice submission",
                    "details": {
                        "session_id": str(session_id),
                        "scene_index": scene_index,
                        "valid_range": "1-4",
                        "timestamp": observability_service.get_current_timestamp()
                    }
                }
            )
        else:
            observability_service.increment_counter("choice_submission_service_error")
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "INTERNAL_ERROR",
                    "message": "Failed to process choice submission",
                    "details": {
                        "session_id": str(session_id),
                        "scene_index": scene_index,
                        "choice_id": choice_id,
                        "error": str(e),
                        "timestamp": observability_service.get_current_timestamp()
                    }
                }
            )
            
    except Exception as e:
        # Check if it's an HTTPException that was re-raised from inner code
        if isinstance(e, HTTPException):
            raise e
            
        observability_service.increment_counter("choice_submission_unexpected_error")
        observability_service.log_error("Unexpected error in choice submission", {
            "session_id": str(session_id),
            "scene_index": scene_index,
            "choice_id": choice_id,
            "error": str(e)
        })
        
        # Return 503 for unexpected errors that might be LLM-related
        raise HTTPException(
            status_code=503,
            detail={
                "error_code": "LLM_SERVICE_UNAVAILABLE",
                "message": "Choice processing service is temporarily unavailable",
                "details": {
                    "session_id": str(session_id),
                    "scene_index": scene_index,
                    "choice_id": choice_id,
                    "retry_after": 30,
                    "timestamp": observability_service.get_current_timestamp()
                }
            }
        )


@router.post("/{session_id}/scenes/{scene_index}/choice/validate")
async def validate_choice(
    session_id: UUID = Path(..., description="Session identifier"),
    scene_index: int = Path(..., ge=1, le=4, description="Scene number (1-4)"),
    choice_data: ChoiceSubmission = Body(..., description="Choice to validate")
) -> Dict[str, Any]:
    """
    Validate a choice without submitting it.
    
    Args:
        session_id: UUID of the active session
        scene_index: Current scene number (1-4)
        choice_ Choice data to validate
        
    Returns:
        Validation result indicating if choice is valid
    """
    try:
        choice_id = choice_data.choiceId
        
        # Validate choice ID format
        format_valid = _validate_choice_id_format(choice_id, scene_index)
        
        # Check if choice exists in session
        session = default_session_service.session_store.get_session(session_id)
        if not session:
            raise SessionNotFoundError("Session not found")
            
        choice_exists = False
        if session.scenes:
            for scene in session.scenes:
                if scene.sceneIndex == scene_index:
                    choice_exists = any(choice.id == choice_id for choice in scene.choices)
                    break
        
        return {
            "sessionId": str(session_id),
            "sceneIndex": scene_index,
            "choiceId": choice_id,
            "valid": format_valid and choice_exists,
            "formatValid": format_valid,
            "choiceExists": choice_exists
        }
        
    except SessionNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "SESSION_NOT_FOUND",
                "message": "Session not found or has expired",
                "details": {"session_id": str(session_id)}
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to validate choice",
                "details": {"error": str(e)}
            }
        )


def _validate_choice_id_format(choice_id: str, scene_index: int) -> bool:
    """
    Validate that choice ID follows expected format: choice_{scene_index}_{choice_number}
    
    Args:
        choice_id: Choice identifier to validate
        scene_index: Expected scene index
        
    Returns:
        True if format is valid, False otherwise
    """
    if not choice_id:
        return False
        
    parts = choice_id.split('_')
    if len(parts) != 3:
        return False
        
    if parts[0] != 'choice':
        return False
        
    try:
        scene_num = int(parts[1])
        choice_num = int(parts[2])
        
        # Scene number should match
        if scene_num != scene_index:
            return False
            
        # Choice number should be 1-4
        if choice_num < 1 or choice_num > 4:
            return False
            
        return True
        
    except ValueError:
        return False
