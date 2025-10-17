"""
Scene retrieval API endpoints for NightLoom MVP.

Provides endpoints for retrieving scene data during diagnosis flow.
"""

from fastapi import APIRouter, HTTPException, Path
from uuid import UUID
from typing import Dict, Any

from app.services.session import default_session_service, SessionNotFoundError, InvalidSessionStateError, SessionServiceError
from app.services.observability import observability_service

router = APIRouter(tags=["scenes"])


@router.get("/{session_id}/scenes/{scene_index}")
async def get_scene(
    session_id: UUID = Path(..., description="Session identifier"),
    scene_index: int = Path(..., ge=1, le=4, description="Scene number (1-4)")
) -> Dict[str, Any]:
    """
    Retrieve scene data for the specified session and scene index.
    
    Args:
        session_id: UUID of the active session
        scene_index: Scene number (1-4)
        
    Returns:
        Scene data with narrative and choices
        
    Raises:
        404: Session not found
        400: Invalid session state or scene index
        503: LLM service unavailable
    """
    # Start performance tracking
    start_time = observability_service.start_timer("scene_retrieval")
    
    try:
        # Load scene from session service
        scene = default_session_service.load_scene(session_id, scene_index)
        
        # Get session to check fallback flags
        session = default_session_service.session_store.get_session(session_id)
        fallback_used = bool(session and session.fallbackFlags)
        
        # Track success metrics
        observability_service.increment_counter("scene_retrieval_success")
        observability_service.record_latency("scene_retrieval", start_time)
        
        # Return scene data
        response = {
            "sessionId": str(session_id),
            "scene": {
                "sceneIndex": scene.sceneIndex,
                "themeId": scene.themeId,
                "narrative": scene.narrative,
                "choices": [
                    {
                        "id": choice.id,
                        "text": choice.text,
                        "weights": choice.weights
                    }
                    for choice in scene.choices
                ]
            },
            "fallbackUsed": fallback_used
        }
        
        return response
        
    except SessionNotFoundError:
        observability_service.increment_counter("scene_retrieval_session_not_found")
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
        observability_service.increment_counter("scene_retrieval_invalid_state")
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "BAD_REQUEST",
                "message": "Session is not in valid state for scene access",
                "details": {
                    "session_id": str(session_id),
                    "scene_index": scene_index,
                    "error": str(e),
                    "timestamp": observability_service.get_current_timestamp()
                }
            }
        )
        
    except ValueError as e:
        # Handle scene access validation errors
        error_msg = str(e)
        if "cannot access scene" in error_msg or "Scene" in error_msg and "not found" in error_msg:
            observability_service.increment_counter("scene_retrieval_invalid_state")
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "BAD_REQUEST",
                    "message": "Session is not in valid state for scene access",
                    "details": {
                        "session_id": str(session_id),
                        "scene_index": scene_index,
                        "error": error_msg,
                        "timestamp": observability_service.get_current_timestamp()
                    }
                }
            )
        elif "state" in error_msg and "required" in error_msg:
            observability_service.increment_counter("scene_retrieval_invalid_state")
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "BAD_REQUEST",
                    "message": "Session is not in valid state for scene access",
                    "details": {
                        "session_id": str(session_id),
                        "scene_index": scene_index,
                        "error": error_msg,
                        "timestamp": observability_service.get_current_timestamp()
                    }
                }
            )
        else:
            # Re-raise other ValueError exceptions as 503 for unexpected errors
            observability_service.increment_counter("scene_retrieval_unexpected_error")
            raise HTTPException(
                status_code=503,
                detail={
                    "error_code": "LLM_SERVICE_UNAVAILABLE",
                    "message": "Scene service is temporarily unavailable",
                    "details": {
                        "session_id": str(session_id),
                        "scene_index": scene_index,
                        "retry_after": 30,
                        "timestamp": observability_service.get_current_timestamp()
                    }
                }
            )

    except SessionServiceError as e:
        if "Scene" in str(e) and "not found" in str(e):
            observability_service.increment_counter("scene_retrieval_invalid_index")
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "INVALID_SCENE_INDEX",
                    "message": f"Scene {scene_index} is not accessible",
                    "details": {
                        "session_id": str(session_id),
                        "scene_index": scene_index,
                        "valid_range": "1-4",
                        "timestamp": observability_service.get_current_timestamp()
                    }
                }
            )
        else:
            observability_service.increment_counter("scene_retrieval_service_error")
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "INTERNAL_ERROR",
                    "message": "Failed to retrieve scene data",
                    "details": {
                        "session_id": str(session_id),
                        "scene_index": scene_index,
                        "error": str(e),
                        "timestamp": observability_service.get_current_timestamp()
                    }
                }
            )
            
    except Exception as e:
        # Check if it's an HTTPException that was re-raised from inner code
        if isinstance(e, HTTPException):
            raise e
            
        observability_service.increment_counter("scene_retrieval_unexpected_error")
        observability_service.log_error("Unexpected error in scene retrieval", {
            "session_id": str(session_id),
            "scene_index": scene_index,
            "error": str(e)
        })
        
        # Try to return fallback scene if session exists
        try:
            session = default_session_service.session_store.get_session(session_id)
            if session and session.scenes:
                for scene in session.scenes:
                    if scene.sceneIndex == scene_index:
                        # Add fallback flag to session
                        if "SCENE_FALLBACK" not in session.fallbackFlags:
                            session.fallbackFlags.append("SCENE_FALLBACK")
                        default_session_service.session_store.update_session(session)
                        
                        # Return scene with fallback flag
                        return {
                            "sessionId": str(session_id),
                            "scene": {
                                "sceneIndex": scene.sceneIndex,
                                "themeId": scene.themeId,
                                "narrative": scene.narrative,
                                "choices": [
                                    {
                                        "id": choice.id,
                                        "text": choice.text,
                                        "weights": choice.weights
                                    }
                                    for choice in scene.choices
                                ]
                            },
                            "fallbackUsed": True
                        }
            
            # If no scenes exist, try to use fallback content from fallback_assets
            try:
                from app.services.fallback_assets import get_fallback_scene
                fallback_scene = get_fallback_scene(scene_index, session.themeId if session else "fallback")
                
                # Add fallback flag to session if it exists
                if session:
                    if "SCENE_FALLBACK" not in session.fallbackFlags:
                        session.fallbackFlags.append("SCENE_FALLBACK")
                    default_session_service.session_store.update_session(session)
                
                return {
                    "sessionId": str(session_id),
                    "scene": {
                        "sceneIndex": fallback_scene.sceneIndex,
                        "themeId": fallback_scene.themeId,
                        "narrative": fallback_scene.narrative,
                        "choices": [
                            {
                                "id": choice.id,
                                "text": choice.text,
                                "weights": choice.weights
                            }
                            for choice in fallback_scene.choices
                        ]
                    },
                    "fallbackUsed": True
                }
            except:
                pass
                
        except:
            pass  # If fallback fails, continue to error response
        
        # Return 503 for unexpected errors that might be LLM-related
        raise HTTPException(
            status_code=503,
            detail={
                "error_code": "LLM_SERVICE_UNAVAILABLE",
                "message": "Scene service is temporarily unavailable",
                "details": {
                    "session_id": str(session_id),
                    "scene_index": scene_index,
                    "retry_after": 30,
                    "timestamp": observability_service.get_current_timestamp()
                }
            }
        )


@router.get("/{session_id}/scenes/{scene_index}/validate")
async def validate_scene_access(
    session_id: UUID = Path(..., description="Session identifier"),
    scene_index: int = Path(..., ge=1, le=4, description="Scene number (1-4)")
) -> Dict[str, Any]:
    """
    Validate whether a scene is accessible without retrieving its data.
    
    Args:
        session_id: UUID of the active session
        scene_index: Scene number (1-4)
        
    Returns:
        Validation result with accessibility status
    """
    try:
        # Check session existence and scene accessibility
        session = default_session_service.session_store.get_session(session_id)
        if not session:
            raise SessionNotFoundError("Session not found")
            
        # Use session guard to check accessibility
        from app.services.session_store import SessionGuard
        accessible = SessionGuard.can_access_scene(session, scene_index)
        
        return {
            "sessionId": str(session_id),
            "sceneIndex": scene_index,
            "accessible": accessible,
            "currentState": session.state.value,
            "completedScenes": len(session.choices) if session.choices else 0
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
                "message": "Failed to validate scene access",
                "details": {"error": str(e)}
            }
        )


@router.get("/{session_id}/progress")
async def get_session_progress(
    session_id: UUID = Path(..., description="Session identifier")
) -> Dict[str, Any]:
    """
    Get current progress information for the session.
    
    Args:
        session_id: UUID of the active session
        
    Returns:
        Progress information including completed scenes and current state
    """
    try:
        session = default_session_service.session_store.get_session(session_id)
        if not session:
            raise SessionNotFoundError("Session not found")
            
        completed_scenes = len(session.choices) if session.choices else 0
        current_scene = completed_scenes + 1 if completed_scenes < 4 else 4
        
        return {
            "sessionId": str(session_id),
            "state": session.state.value,
            "completedScenes": completed_scenes,
            "totalScenes": 4,
            "currentScene": current_scene,
            "progressPercentage": (completed_scenes / 4) * 100,
            "canProceedToResult": completed_scenes >= 4,
            "selectedKeyword": session.selectedKeyword,
            "themeId": session.themeId
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
                "message": "Failed to retrieve session progress",
                "details": {"error": str(e)}
            }
        )
