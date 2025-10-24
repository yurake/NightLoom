"""
Scene retrieval API endpoints for NightLoom MVP.

Provides endpoints for retrieving scene data during diagnosis flow.
"""

from fastapi import APIRouter, HTTPException, Path, Body
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Dict, Any, List, Optional

from app.services.session import default_session_service, SessionNotFoundError, InvalidSessionStateError, SessionServiceError
from app.services.external_llm import get_llm_service, LLMServiceError, AllProvidersFailedError
from app.services.observability import observability_service

router = APIRouter(tags=["scenes"])


class ScenarioGenerationRequest(BaseModel):
    """Request model for LLM scenario generation."""
    session_id: UUID = Field(..., description="Session identifier")
    scene_index: int = Field(..., ge=1, le=4, description="Scene number (1-4)")
    keyword: str = Field(..., description="Selected keyword for scenario context")
    axes: List[Dict[str, Any]] = Field(..., description="Evaluation axes for choice weights")
    previous_choices: Optional[List[Dict[str, Any]]] = Field(default=None, description="Previous user choices for continuity")


class ScenarioGenerationResponse(BaseModel):
    """Response model for generated scenario."""
    session_id: UUID
    scene: Dict[str, Any]
    provider_used: str
    generation_time_ms: float
    fallback_used: bool = False


@router.post("/llm/generate/scenario")
async def generate_scenario(
    request: ScenarioGenerationRequest = Body(..., description="Scenario generation request")
) -> ScenarioGenerationResponse:
    """
    Generate dynamic scenario using LLM service.
    
    T037 [US3] Create /api/llm/generate/scenario API endpoint
    
    Args:
        request: Scenario generation request with session info, keyword, and axes
        
    Returns:
        Generated scenario with narrative and choices
        
    Raises:
        400: Validation error or session not found
        503: LLM service unavailable
        500: Internal server error
    """
    # Start performance tracking
    start_time = observability_service.start_timer("llm_scenario_generation")
    
    try:
        # Validate session exists and is in correct state
        session = default_session_service.session_store.get_session(request.session_id)
        if not session:
            observability_service.increment_counter("llm_scenario_generation_session_not_found")
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "SESSION_NOT_FOUND",
                    "message": "Session not found or has expired",
                    "details": {
                        "session_id": str(request.session_id),
                        "timestamp": observability_service.get_current_timestamp()
                    }
                }
            )
        
        # Validate session state
        if session.state.value not in ["PLAY", "INIT"]:
            observability_service.increment_counter("llm_scenario_generation_invalid_state")
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "INVALID_SESSION_STATE",
                    "message": f"Session is in {session.state.value} state, expected PLAY or INIT",
                    "details": {
                        "session_id": str(request.session_id),
                        "current_state": session.state.value,
                        "expected_states": ["PLAY", "INIT"],
                        "timestamp": observability_service.get_current_timestamp()
                    }
                }
            )
        
        # Get LLM service
        llm_service = get_llm_service()
        
        # Update session with request data if needed
        if not session.selectedKeyword:
            session.selectedKeyword = request.keyword
        
        # Convert axes data to Axis objects if needed
        from app.models.session import Axis
        if not session.axes or len(session.axes) == 0:
            session.axes = [Axis(**axis_data) for axis_data in request.axes]
        
        # Generate scenario using LLM service
        generated_scene = await llm_service.generate_scenario(
            session=session,
            scene_index=request.scene_index,
            previous_choices=request.previous_choices
        )
        
        # Track success metrics
        observability_service.increment_counter("llm_scenario_generation_success")
        generation_time = observability_service.record_latency("llm_scenario_generation", start_time)
        
        # Determine provider used and fallback status
        provider_used = "external_llm"  # Default assumption
        fallback_used = False
        
        # Check for fallback flags in session
        if session.fallbackFlags:
            fallback_flags = [flag for flag in session.fallbackFlags if f"scenario_generation_scene_{request.scene_index}" in flag]
            if fallback_flags:
                fallback_used = True
                provider_used = "fallback"
        
        # Prepare response
        response_data = {
            "session_id": request.session_id,
            "scene": {
                "scene_index": generated_scene.sceneIndex,
                "narrative": generated_scene.narrative,
                "choices": [
                    {
                        "id": choice.id,
                        "text": choice.text,
                        "weights": choice.weights
                    }
                    for choice in generated_scene.choices
                ]
            },
            "provider_used": provider_used,
            "generation_time_ms": generation_time,
            "fallback_used": fallback_used
        }
        
        return ScenarioGenerationResponse(**response_data)
        
    except HTTPException:
        # Re-raise HTTP exceptions as is
        raise
        
    except (LLMServiceError, AllProvidersFailedError) as e:
        observability_service.increment_counter("llm_scenario_generation_service_error")
        raise HTTPException(
            status_code=503,
            detail={
                "error_code": "LLM_SERVICE_UNAVAILABLE",
                "message": "LLM service is temporarily unavailable for scenario generation",
                "details": {
                    "session_id": str(request.session_id),
                    "scene_index": request.scene_index,
                    "error": str(e),
                    "retry_after": 30,
                    "timestamp": observability_service.get_current_timestamp()
                }
            }
        )
        
    except ValueError as e:
        observability_service.increment_counter("llm_scenario_generation_validation_error")
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid request data for scenario generation",
                "details": {
                    "session_id": str(request.session_id),
                    "scene_index": request.scene_index,
                    "error": str(e),
                    "timestamp": observability_service.get_current_timestamp()
                }
            }
        )
        
    except Exception as e:
        observability_service.increment_counter("llm_scenario_generation_unexpected_error")
        observability_service.log_error("Unexpected error in LLM scenario generation", {
            "session_id": str(request.session_id),
            "scene_index": request.scene_index,
            "error": str(e)
        })
        
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to generate scenario",
                "details": {
                    "session_id": str(request.session_id),
                    "scene_index": request.scene_index,
                    "timestamp": observability_service.get_current_timestamp()
                }
            }
        )


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
        # Load scene from session service (now async for dynamic generation)
        scene = await default_session_service.load_scene(session_id, scene_index)
        
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
