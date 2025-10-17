"""
Result retrieval API endpoints for NightLoom MVP.

Provides endpoints for generating and retrieving diagnosis results.
"""

from fastapi import APIRouter, HTTPException, Path
from uuid import UUID
from typing import Dict, Any

from app.services.session import default_session_service, SessionNotFoundError, InvalidSessionStateError, SessionServiceError
from app.services.observability import observability_service

router = APIRouter(tags=["results"])


@router.post("/{session_id}/result")
async def generate_result(
    session_id: UUID = Path(..., description="Session identifier")
) -> Dict[str, Any]:
    """
    Generate and retrieve final diagnosis result for completed session.
    
    Args:
        session_id: UUID of the completed session
        
    Returns:
        Complete diagnosis result with scores and type profiles
        
    Raises:
        404: Session not found
        400: Session not completed or invalid state
        503: LLM service unavailable
    """
    # Start performance tracking
    start_time = observability_service.start_timer("result_generation")
    
    try:
        # Generate result through session service
        result = await default_session_service.generate_result(session_id)
        
        # Track success metrics
        observability_service.increment_counter("result_generation_success")
        observability_service.record_latency("result_generation", start_time)
        
        # Log successful result generation
        observability_service.log_info("Result generated successfully", {
            "session_id": str(session_id),
            "axis_count": len(result.get("axes", [])),
            "profile_count": len(result.get("type", {}).get("profiles", [])),
            "fallback_used": bool(result.get("fallbackFlags")),
            "generation_time_ms": observability_service.get_elapsed_time(start_time)
        })
        
        return result
        
    except SessionNotFoundError:
        observability_service.increment_counter("result_generation_session_not_found")
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
        observability_service.increment_counter("result_generation_invalid_state")
        
        # Check if it's specifically about incomplete sessions
        if "not completed" in str(e).lower() or "scenes" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "SESSION_NOT_COMPLETED",
                    "message": "Session has not completed all required scenes",
                    "details": {
                        "session_id": str(session_id),
                        "required_scenes": 4,
                        "error": str(e),
                        "timestamp": observability_service.get_current_timestamp()
                    }
                }
            )
        # Check if it's about INIT state (keyword not selected)
        elif "INIT state" in str(e) or "keyword must be selected" in str(e):
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "BAD_REQUEST",
                    "message": "Session is not in valid state for result generation",
                    "details": {
                        "session_id": str(session_id),
                        "error": str(e),
                        "timestamp": observability_service.get_current_timestamp()
                    }
                }
            )
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "BAD_REQUEST",
                    "message": "Session is not in valid state for result generation",
                    "details": {
                        "session_id": str(session_id),
                        "error": str(e),
                        "timestamp": observability_service.get_current_timestamp()
                    }
                }
            )
            
    except ValueError as e:
        # Handle session validation errors
        error_msg = str(e)
        if "completed" in error_msg and "scenes" in error_msg:
            observability_service.increment_counter("result_generation_invalid_state")
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "SESSION_NOT_COMPLETED",
                    "message": "Session has not completed all required scenes",
                    "details": {
                        "session_id": str(session_id),
                        "required_scenes": 4,
                        "error": error_msg,
                        "timestamp": observability_service.get_current_timestamp()
                    }
                }
            )
        elif "state" in error_msg and "required" in error_msg:
            observability_service.increment_counter("result_generation_invalid_state")
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "BAD_REQUEST",
                    "message": "Session is not in valid state for result generation",
                    "details": {
                        "session_id": str(session_id),
                        "error": error_msg,
                        "timestamp": observability_service.get_current_timestamp()
                    }
                }
            )
        else:
            # Re-raise other ValueError exceptions as 503 for unexpected errors
            observability_service.increment_counter("result_generation_unexpected_error")
            raise HTTPException(
                status_code=503,
                detail={
                    "error_code": "LLM_SERVICE_UNAVAILABLE",
                    "message": "Result generation service is temporarily unavailable",
                    "details": {
                        "session_id": str(session_id),
                        "retry_after": 30,
                        "timestamp": observability_service.get_current_timestamp()
                    }
                }
            )

    except SessionServiceError as e:
        # Check if it's an LLM-related error
        if "LLM" in str(e) or "generate" in str(e).lower():
            observability_service.increment_counter("result_generation_llm_error")
            raise HTTPException(
                status_code=503,
                detail={
                    "error_code": "LLM_SERVICE_UNAVAILABLE",
                    "message": "Result generation service is temporarily unavailable",
                    "details": {
                        "session_id": str(session_id),
                        "error": str(e),
                        "retry_after": 30,
                        "timestamp": observability_service.get_current_timestamp()
                    }
                }
            )
        else:
            observability_service.increment_counter("result_generation_service_error")
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "INTERNAL_ERROR",
                    "message": "Failed to generate diagnosis result",
                    "details": {
                        "session_id": str(session_id),
                        "error": str(e),
                        "timestamp": observability_service.get_current_timestamp()
                    }
                }
            )
            
    except Exception as e:
        # Check if it's an HTTPException that was re-raised from inner code
        if isinstance(e, HTTPException):
            raise e
            
        observability_service.increment_counter("result_generation_unexpected_error")
        observability_service.log_error("Unexpected error in result generation", {
            "session_id": str(session_id),
            "error": str(e)
        })
        
        # Return 503 for unexpected errors that might be LLM-related
        raise HTTPException(
            status_code=503,
            detail={
                "error_code": "LLM_SERVICE_UNAVAILABLE",
                "message": "Result generation service is temporarily unavailable",
                "details": {
                    "session_id": str(session_id),
                    "retry_after": 30,
                    "timestamp": observability_service.get_current_timestamp()
                }
            }
        )


@router.get("/{session_id}/result/status")
async def get_result_status(
    session_id: UUID = Path(..., description="Session identifier")
) -> Dict[str, Any]:
    """
    Check if session is ready for result generation.
    
    Args:
        session_id: UUID of the session
        
    Returns:
        Status information about result readiness
    """
    try:
        # Get session from session store directly to avoid state checks
        session = default_session_service.session_store.get_session(session_id)
        if not session:
            raise SessionNotFoundError("Session not found")
            
        # Check completion status
        completed_scenes = len(session.choices) if session.choices else 0
        is_ready = completed_scenes >= 4
        has_result = session.state.value == "RESULT" if hasattr(session.state, 'value') else False
        
        return {
            "sessionId": str(session_id),
            "state": session.state.value if hasattr(session.state, 'value') else str(session.state),
            "completedScenes": completed_scenes,
            "totalScenes": 4,
            "readyForResult": is_ready,
            "hasResult": has_result,
            "selectedKeyword": session.selectedKeyword,
            "themeId": session.themeId,
            "fallbackFlags": session.fallbackFlags or []
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
                "message": "Failed to check result status",
                "details": {"error": str(e)}
            }
        )


@router.delete("/{session_id}/cleanup")
async def cleanup_session(
    session_id: UUID = Path(..., description="Session identifier")
) -> Dict[str, Any]:
    """
    Clean up session data after result display.
    
    Args:
        session_id: UUID of the session to cleanup
        
    Returns:
        Cleanup confirmation
    """
    try:
        # Clean up session through session service
        was_deleted = default_session_service.cleanup_session(session_id)
        
        # Track cleanup metrics
        if was_deleted:
            observability_service.increment_counter("session_cleanup_success")
        else:
            observability_service.increment_counter("session_cleanup_not_found")
            
        return {
            "sessionId": str(session_id),
            "success": True,
            "wasDeleted": was_deleted,
            "timestamp": observability_service.get_current_timestamp()
        }
        
    except Exception as e:
        observability_service.increment_counter("session_cleanup_error")
        observability_service.log_error("Error during session cleanup", {
            "session_id": str(session_id),
            "error": str(e)
        })
        
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to cleanup session",
                "details": {
                    "session_id": str(session_id),
                    "error": str(e)
                }
            }
        )


@router.get("/stats")
async def get_session_stats() -> Dict[str, Any]:
    """
    Get session statistics for monitoring.
    
    Returns:
        Current session statistics
    """
    try:
        stats = default_session_service.get_session_stats()
        
        # Add additional metrics
        current_timestamp = observability_service.get_current_timestamp()
        
        return {
            **stats,
            "timestamp": current_timestamp,
            "service_status": "healthy"
        }
        
    except Exception as e:
        observability_service.log_error("Error retrieving session stats", {
            "error": str(e)
        })
        
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to retrieve session statistics",
                "details": {"error": str(e)}
            }
        )
