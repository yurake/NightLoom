"""
Session service for NightLoom MVP diagnosis flow management.

Handles session lifecycle from bootstrap through result generation,
integrating with LLM services and maintaining session state.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from app.models.session import Session, SessionState, ChoiceRecord, Axis, Scene, AxisScore, TypeProfile
from app.services.session_store import session_store, SessionGuard
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
        scoring_service: Optional[ScoringService] = None,
        typing_service: Optional[TypingService] = None
    ):
        self.llm_service = llm_service or default_llm_service
        self.scoring_service = scoring_service or ScoringService()
        self.typing_service = typing_service or TypingService()
    
    async def start_session(self, initial_character: Optional[str] = None) -> Session:
        """
        Start a new diagnosis session.
        
        Args:
            initial_character: Optional hiragana character for keyword generation
            
        Returns:
            New session in INIT state with bootstrap data
        """
        # Generate bootstrap data from LLM service
        if initial_character is None:
            initial_character = "あ"  # Default fallback
        
        fallback_used = False
        try:
            axes, keywords, theme_id, fallback_used = await self.llm_service.generate_bootstrap_data(
                initial_character
            )
        except Exception as e:
            # Use fallback when LLM service fails
            from app.services.fallback_assets import get_fallback_axes, get_fallback_keywords
            axes = get_fallback_axes()
            keywords = get_fallback_keywords(initial_character)
            theme_id = "fallback"
            fallback_used = True
        
        # Create new session
        session = Session(
            id=uuid.uuid4(),
            state=SessionState.INIT,
            initialCharacter=initial_character,
            keywordCandidates=keywords,
            themeId=theme_id,
            axes=axes,
            fallbackFlags=["BOOTSTRAP_FALLBACK"] if fallback_used else [],
            createdAt=datetime.utcnow()
        )
        
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
        if not keyword or len(keyword) > 20:
            raise SessionServiceError("Invalid keyword length")
        
        # Generate scenes using LLM service with existing axes
        try:
            scenes, fallback_used = await self.llm_service.generate_scenes(
                session.axes, keyword, session.themeId
            )
        except Exception as e:
            raise SessionServiceError(f"Failed to generate scenes: {str(e)}")
        
        # Update session
        session.selectedKeyword = keyword
        session.state = SessionState.PLAY
        session.scenes = scenes
        
        if fallback_used:
            session.fallbackFlags.append("SCENE_FALLBACK")
        
        session_store.update_session(session)
        
        # Return first scene
        return scenes[0] if scenes else None
    
    def load_scene(self, session_id: UUID, scene_index: int) -> Scene:
        """
        Load scene by index.
        
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
        
        # Find scene
        for scene in session.scenes:
            if scene.sceneIndex == scene_index:
                return scene
        
        raise SessionServiceError(f"Scene {scene_index} not found")
    
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
            timestamp=datetime.utcnow()
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
        
        SessionGuard.require_all_scenes_completed(session)
        
        try:
            # Calculate scores
            raw_scores = await self.scoring_service.calculate_scores(session)
            normalized_scores = await self.scoring_service.normalize_scores(raw_scores)
            
            # Generate type profiles using existing axes
            type_profiles, fallback_used = await self.llm_service.generate_type_profiles(
                session.axes, raw_scores, session.selectedKeyword
            )
            
            # Update session with results
            session.rawScores = raw_scores
            session.normalizedScores = normalized_scores
            session.typeProfiles = type_profiles
            session.state = SessionState.RESULT
            session.completedAt = datetime.utcnow()
            
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
