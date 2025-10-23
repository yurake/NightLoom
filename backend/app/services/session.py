"""
Session service for NightLoom MVP diagnosis flow management.

Handles session lifecycle from bootstrap through result generation,
integrating with LLM services and maintaining session state.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

from app.models.session import Session, SessionState, ChoiceRecord, Axis, Scene, AxisScore, TypeProfile
from app.services.session_store import session_store, SessionGuard
from app.services.external_llm import ExternalLLMService, get_llm_service
from app.clients.llm import LLMService, default_llm_service
from app.services.scoring import ScoringService
from app.services.typing import TypingService


class SessionServiceError(Exception):
    """Base exception for session service errors."""
    pass


class SessionNotFoundError(SessionServiceError):
    """Raised when session is not found."""
    pass


class InvalidSessionStateError(SessionServiceError):
    """Raised when session is in invalid state for operation."""
    pass


class SessionService:
    """High-level session management service."""
    
    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        external_llm_service: Optional[ExternalLLMService] = None,
        scoring_service: Optional[ScoringService] = None,
        typing_service: Optional[TypingService] = None
    ):
        self.llm_service = llm_service or default_llm_service
        self.external_llm_service = external_llm_service or get_llm_service()
        self.scoring_service = scoring_service or ScoringService()
        self.typing_service = typing_service or TypingService()
    
    async def start_session(self, initial_character: Optional[str] = None) -> Session:
        """
        Start a new diagnosis session with LLM-generated keywords.
        
        Args:
            initial_character: Optional hiragana character for keyword generation
            
        Returns:
            New session in INIT state with bootstrap data including dynamic keywords
        """
        if initial_character is None:
            initial_character = "あ"  # Default fallback
        
        # Create initial session for LLM service
        session = Session(
            id=uuid.uuid4(),
            state=SessionState.INIT,
            initialCharacter=initial_character,
            themeId="adventure",  # Default theme, could be dynamically chosen later
            fallbackFlags=[],
            createdAt=datetime.now(timezone.utc)
        )
        
        # Generate keywords using external LLM service
        try:
            keywords = await self.external_llm_service.generate_keywords(session)
        except Exception as e:
            # Log the specific error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"[SESSION] External LLM keyword generation failed: {type(e).__name__}: {str(e)}")
            logger.debug(f"[SESSION] Full exception details:", exc_info=True)
            
            # Fallback to legacy LLM service or static keywords
            try:
                axes, keywords, theme_id, fallback_used = await self.llm_service.generate_bootstrap_data(
                    initial_character
                )
                if fallback_used:
                    session.fallbackFlags.append("BOOTSTRAP_FALLBACK")
            except Exception as fallback_error:
                # Final fallback to static keywords
                from app.services.fallback_assets import get_fallback_keywords
                keywords = get_fallback_keywords(initial_character)
                session.fallbackFlags.append("KEYWORD_GENERATION_FALLBACK")
        
        # Get default axes (will be dynamic in Phase 4)
        try:
            axes, _, theme_id, axes_fallback_used = await self.llm_service.generate_bootstrap_data(
                initial_character
            )
            if axes_fallback_used:
                session.fallbackFlags.append("AXES_FALLBACK")
        except Exception:
            from app.services.fallback_assets import get_fallback_axes
            axes = get_fallback_axes()
            session.fallbackFlags.append("AXES_FALLBACK")
            theme_id = "adventure"
        
        # Update session with generated data
        session.keywordCandidates = keywords
        session.axes = axes
        session.themeId = theme_id
        
        # Store session
        session_store.create_session(session)
        
        return session
    
    async def confirm_keyword(self, session_id: UUID, keyword: str, source: str) -> Scene:
        """
        Confirm keyword selection and return first scene.
        
        Args:
            session_id: Session identifier
            keyword: Selected keyword (from candidates or custom)
            source: Selection source ('suggestion' or 'manual')
            
        Returns:
            First scene for diagnosis
        """
        # Load and validate session
        session = session_store.get_session(session_id)
        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        SessionGuard.require_state(session, SessionState.INIT)
        
        # Validate keyword
        if not keyword or len(keyword.strip()) == 0:
            raise SessionServiceError("Invalid keyword: empty keyword not allowed")
        if len(keyword) >= 20:
            raise SessionServiceError("Invalid keyword length: exceeds maximum allowed length")
        
        # Update session with selected keyword first
        session.selectedKeyword = keyword
        
        # Generate dynamic axes based on selected keyword using external LLM service
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[SESSION] Generating dynamic axes for keyword: {keyword}")
        
        try:
            dynamic_axes = await self.external_llm_service.generate_axes(session)
            session.axes = dynamic_axes
            logger.info(f"[SESSION] Generated {len(dynamic_axes)} dynamic axes for keyword '{keyword}'")
        except Exception as e:
            logger.error(f"[SESSION] Dynamic axis generation failed: {type(e).__name__}: {str(e)}")
            logger.debug(f"[SESSION] Full exception details:", exc_info=True)
            
            # Fallback to static axes if dynamic generation fails
            try:
                axes, _, _, axes_fallback_used = await self.llm_service.generate_bootstrap_data(keyword)
                session.axes = axes
                if axes_fallback_used:
                    session.fallbackFlags.append("AXES_FALLBACK")
                logger.info(f"[SESSION] Used fallback axes for keyword '{keyword}'")
            except Exception as fallback_error:
                from app.services.fallback_assets import get_fallback_axes
                session.axes = get_fallback_axes()
                session.fallbackFlags.append("AXES_FALLBACK")
                logger.warning(f"[SESSION] Used static fallback axes for keyword '{keyword}'")
        
        # Generate only the first scene initially to improve response time
        # Remaining scenes will be generated on-demand when accessed
        logger.info(f"[SESSION] Generating first scene for keyword: {keyword}")
        scenes = []
        
        try:
            # Generate only the first scene for faster initial response
            first_scene = await self.external_llm_service.generate_scenario(
                session=session,
                scene_index=1,
                previous_choices=[]
            )
            scenes.append(first_scene)
            logger.info(f"[SESSION] Generated first dynamic scene for keyword '{keyword}'")
            
        except Exception as e:
            logger.error(f"[SESSION] First scene generation failed: {type(e).__name__}: {str(e)}")
            
            # Fallback to static scene generation for first scene only
            try:
                fallback_scenes, fallback_used = await self.llm_service.generate_scenes(
                    session.axes, keyword, session.themeId
                )
                if fallback_scenes and len(fallback_scenes) >= 1:
                    scenes.append(fallback_scenes[0])
                    session.fallbackFlags.append("SCENE_1_FALLBACK")
                    logger.info(f"[SESSION] Used fallback first scene for keyword '{keyword}'")
                else:
                    raise SessionServiceError("Fallback scene generation failed for first scene")
            except Exception as fallback_error:
                logger.error(f"[SESSION] Fallback scene generation also failed: {type(fallback_error).__name__}: {str(fallback_error)}")
                raise SessionServiceError(f"Failed to generate first scene: {str(e)}")
        
        # Update session
        session.state = SessionState.PLAY
        session.scenes = scenes
        
        session_store.update_session(session)
        
        # Return first scene
        return scenes[0] if scenes else None
    
    async def load_scene(self, session_id: UUID, scene_index: int) -> Scene:
        """
        Load scene by index, generating dynamically if needed.
        
        Args:
            session_id: Session identifier
            scene_index: Scene number (1-4)
            
        Returns:
            Requested scene
        """
        # Load and validate session
        session = session_store.get_session(session_id)
        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        SessionGuard.require_state(session, SessionState.PLAY)
        
        # Validate scene access
        if not SessionGuard.can_access_scene(session, scene_index):
            raise InvalidSessionStateError(f"Cannot access scene {scene_index}")
        
        # Check if scene already exists
        for scene in session.scenes:
            if scene.sceneIndex == scene_index:
                return scene
        
        # Scene doesn't exist - generate it dynamically with context
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[SESSION] Dynamically generating scene {scene_index} for session {session_id}")
        
        # Collect previous scenes and choices for continuity
        previous_choices = []
        for choice_record in session.choices:
            if choice_record.sceneIndex < scene_index:
                # Find the scene and choice text from previous scenes
                for prev_scene in session.scenes:
                    if prev_scene.sceneIndex == choice_record.sceneIndex:
                        for choice in prev_scene.choices:
                            if choice.id == choice_record.choiceId:
                                previous_choices.append({
                                    "scene_index": choice_record.sceneIndex,
                                    "choice_id": choice_record.choiceId,
                                    "text": choice.text,
                                    "scene_narrative": prev_scene.narrative
                                })
                                break
                        break
        
        try:
            # Generate scene using external LLM service with continuity
            dynamic_scene = await self.external_llm_service.generate_scenario(
                session=session,
                scene_index=scene_index,
                previous_choices=previous_choices
            )
            
            # Add generated scene to session
            session.scenes.append(dynamic_scene)
            session_store.update_session(session)
            
            logger.info(f"[SESSION] Successfully generated dynamic scene {scene_index}")
            return dynamic_scene
            
        except Exception as e:
            logger.error(f"[SESSION] Dynamic scene {scene_index} generation failed: {type(e).__name__}: {str(e)}")
            
            # Fallback to static scene generation
            try:
                fallback_scenes, fallback_used = await self.llm_service.generate_scenes(
                    session.axes, session.selectedKeyword, session.themeId
                )
                if fallback_scenes and len(fallback_scenes) >= scene_index:
                    fallback_scene = fallback_scenes[scene_index - 1]
                    session.scenes.append(fallback_scene)
                    session.fallbackFlags.append(f"SCENE_{scene_index}_FALLBACK")
                    session_store.update_session(session)
                    logger.info(f"[SESSION] Used fallback scene {scene_index}")
                    return fallback_scene
                else:
                    raise SessionServiceError(f"Fallback scene generation failed for scene {scene_index}")
            except Exception as fallback_error:
                logger.error(f"[SESSION] Fallback scene generation also failed: {type(fallback_error).__name__}: {str(fallback_error)}")
                raise SessionServiceError(f"Scene {scene_index} not found and cannot be generated")
    
    def get_scene(self, session: Session, scene_index: int) -> Scene:
        """
        Get scene by index from session.
        
        Args:
            session: Session object
            scene_index: Scene number (1-4)
            
        Returns:
            Requested scene
        """
        # Validate scene access
        if not SessionGuard.can_access_scene(session, scene_index):
            raise InvalidSessionStateError(f"Cannot access scene {scene_index}")
        
        # Find scene
        for scene in session.scenes:
            if scene.sceneIndex == scene_index:
                return scene
        
        raise SessionServiceError(f"Scene {scene_index} not found")
    
    def submit_choice(self, session: Session, scene_index: int, choice_id: str) -> Dict[str, Any]:
        """
        Submit choice and return result with next scene.
        
        Args:
            session: Session object
            scene_index: Current scene number
            choice_id: Selected choice identifier
            
        Returns:
            Dictionary with nextScene and sceneCompleted status
        """
        # Validate choice can be made
        SessionGuard.validate_choice_transition(session, scene_index, choice_id)
        
        # Record choice
        choice_record = ChoiceRecord(
            sceneIndex=scene_index,
            choiceId=choice_id,
            timestamp=datetime.now(timezone.utc)
        )
        session.choices.append(choice_record)
        
        # Update session
        session_store.update_session(session)
        
        # Return next scene if available
        next_scene_index = scene_index + 1
        next_scene = None
        
        if next_scene_index <= 4:
            for scene in session.scenes:
                if scene.sceneIndex == next_scene_index:
                    next_scene = scene
                    break
        
        return {
            "nextScene": next_scene,
            "sceneCompleted": True
        }
    
    def record_choice(self, session_id: UUID, scene_index: int, choice_id: str) -> Optional[Scene]:
        """
        Record user choice and return next scene if available.
        
        Args:
            session_id: Session identifier
            scene_index: Current scene number
            choice_id: Selected choice identifier
            
        Returns:
            Next scene or None if all scenes completed
        """
        # Load and validate session
        session = session_store.get_session(session_id)
        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        # Validate choice can be made
        SessionGuard.validate_choice_transition(session, scene_index, choice_id)
        
        # Record choice
        choice_record = ChoiceRecord(
            sceneIndex=scene_index,
            choiceId=choice_id,
            timestamp=datetime.now(timezone.utc)
        )
        session.choices.append(choice_record)
        
        # Update session
        session_store.update_session(session)
        
        # Return next scene if available
        next_scene_index = scene_index + 1
        if next_scene_index <= 4:
            for scene in session.scenes:
                if scene.sceneIndex == next_scene_index:
                    return scene
        
        return None
    
    async def generate_result(self, session_id: UUID) -> Dict:
        """
        Generate final result for completed session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Result data with scores and type profiles
        """
        # Load and validate session
        session = session_store.get_session(session_id)
        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        # Check session state first before checking completion
        if session.state == SessionState.INIT:
            raise InvalidSessionStateError("Session is in INIT state, keyword must be selected first")
        
        SessionGuard.require_all_scenes_completed(session)
        
        try:
            # Calculate scores
            raw_scores = await self.scoring_service.calculate_scores(session)
            normalized_scores = await self.scoring_service.normalize_scores(raw_scores)
            
            # T048: Generate type profiles using AI analysis (external LLM service)
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[SESSION] Generating AI analysis for session {session_id}")
            
            try:
                # Use external LLM service for AI-powered analysis
                ai_profiles = await self.external_llm_service.analyze_results(session)
                type_profiles = ai_profiles
                fallback_used = False
                logger.info(f"[SESSION] Successfully generated AI analysis with {len(ai_profiles)} profiles")
            except Exception as ai_error:
                logger.error(f"[SESSION] AI analysis failed: {type(ai_error).__name__}: {str(ai_error)}")
                
                # Fallback to existing LLM service
                try:
                    type_profiles, fallback_used = await self.llm_service.generate_type_profiles(
                        session.axes, raw_scores, session.selectedKeyword
                    )
                    logger.info(f"[SESSION] Used fallback type profile generation")
                except Exception as fallback_error:
                    logger.error(f"[SESSION] Fallback type generation also failed: {type(fallback_error).__name__}: {str(fallback_error)}")
                    from app.services.fallback_assets import get_fallback_type_profiles
                    type_profiles = get_fallback_type_profiles()
                    fallback_used = True
                    session.fallbackFlags.append("AI_RESULT_ANALYSIS_FALLBACK")
            
            # Update session with results
            session.rawScores = raw_scores
            session.normalizedScores = normalized_scores
            session.typeProfiles = type_profiles
            session.state = SessionState.RESULT
            session.completedAt = datetime.now(timezone.utc)
            
            if fallback_used:
                session.fallbackFlags.append("TYPE_FALLBACK")
            
            session_store.update_session(session)
            
            # Prepare result response
            result = {
                "sessionId": str(session.id),
                "keyword": session.selectedKeyword,
                "axes": [
                    {
                        "axisId": axis_id,
                        "score": normalized_scores[axis_id],
                        "rawScore": raw_scores[axis_id]
                    }
                    for axis_id in raw_scores.keys()
                ],
                "type": {
                    "dominantAxes": self.typing_service.get_dominant_axes(normalized_scores),
                    "profiles": [profile.dict() for profile in type_profiles],
                    "fallbackUsed": fallback_used
                },
                "completedAt": session.completedAt.isoformat(),
                "fallbackFlags": session.fallbackFlags
            }
            
            return result
            
        except Exception as e:
            raise SessionServiceError(f"Failed to generate result: {str(e)}")
    
    def cleanup_session(self, session_id: UUID) -> bool:
        """
        Remove session from storage.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was removed, False if it didn't exist
        """
        return session_store.delete_session(session_id)
    
    def get_session_stats(self) -> Dict:
        """
        Get current session statistics for monitoring.
        
        Returns:
            Dictionary with session counts and stats
        """
        total_sessions = session_store.count_sessions()
        completed_sessions = session_store.cleanup_completed_sessions()
        
        return {
            "total_sessions": total_sessions,
            "completed_sessions_cleaned": completed_sessions,
            "active_sessions": total_sessions - completed_sessions
        }


# Default service instance
default_session_service = SessionService()

# Add session_store attribute for API access
default_session_service.session_store = session_store
