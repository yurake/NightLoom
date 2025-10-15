"""
In-memory session store with state guard helpers for NightLoom MVP.

Provides thread-safe session storage and state transition validation.
Sessions are ephemeral and automatically expire after result retrieval.
"""

import threading
from typing import Dict, Optional
from uuid import UUID

from app.models.session import Session, SessionState


class SessionStore:
    """Thread-safe in-memory store for diagnosis sessions."""
    
    def __init__(self):
        self._sessions: Dict[UUID, Session] = {}
        self._lock = threading.RLock()
    
    def create_session(self, session: Session) -> None:
        """Store a new session."""
        with self._lock:
            self._sessions[session.id] = session
    
    def get_session(self, session_id: UUID) -> Optional[Session]:
        """Retrieve session by ID."""
        with self._lock:
            return self._sessions.get(session_id)
    
    def update_session(self, session: Session) -> None:
        """Update existing session."""
        with self._lock:
            if session.id in self._sessions:
                self._sessions[session.id] = session
            else:
                raise ValueError(f"Session {session.id} not found for update")
    
    def delete_session(self, session_id: UUID) -> bool:
        """Delete session and return True if it existed."""
        with self._lock:
            return self._sessions.pop(session_id, None) is not None
    
    def count_sessions(self) -> int:
        """Return current session count (for monitoring)."""
        with self._lock:
            return len(self._sessions)
    
    def cleanup_completed_sessions(self) -> int:
        """Remove all completed sessions and return count removed."""
        with self._lock:
            completed_ids = [
                session_id for session_id, session in self._sessions.items()
                if session.is_completed()
            ]
            for session_id in completed_ids:
                del self._sessions[session_id]
            return len(completed_ids)


class SessionGuard:
    """State guard helpers for session operations."""
    
    @staticmethod
    def require_state(session: Session, required_state: SessionState) -> None:
        """Raise ValueError if session is not in required state."""
        if session.state != required_state:
            raise ValueError(
                f"Session {session.id} is in {session.state} state, "
                f"but {required_state} is required"
            )
    
    @staticmethod
    def require_keyword_selected(session: Session) -> None:
        """Raise ValueError if session has no selected keyword."""
        if not session.selectedKeyword:
            raise ValueError(f"Session {session.id} has no selected keyword")
    
    @staticmethod
    def require_scene_completed(session: Session, scene_index: int) -> None:
        """Raise ValueError if specified scene has not been completed."""
        completed_scenes = [choice.sceneIndex for choice in session.choices]
        if scene_index not in completed_scenes:
            raise ValueError(
                f"Session {session.id} has not completed scene {scene_index}"
            )
    
    @staticmethod
    def require_all_scenes_completed(session: Session) -> None:
        """Raise ValueError if not all 4 scenes have been completed."""
        if len(session.choices) != 4:
            raise ValueError(
                f"Session {session.id} has completed {len(session.choices)}/4 scenes"
            )
    
    @staticmethod
    def can_access_scene(session: Session, scene_index: int) -> bool:
        """Check if user can access the specified scene."""
        if session.state != SessionState.PLAY:
            return False
        
        # Scene 1 is accessible after keyword selection
        if scene_index == 1:
            return session.selectedKeyword is not None
        
        # Other scenes require previous scene completion
        completed_scenes = [choice.sceneIndex for choice in session.choices]
        required_previous_scene = scene_index - 1
        return required_previous_scene in completed_scenes
    
    @staticmethod
    def validate_choice_transition(session: Session, scene_index: int, choice_id: str) -> None:
        """Validate that a choice can be made for the given scene."""
        # Must be in PLAY state
        SessionGuard.require_state(session, SessionState.PLAY)
        
        # Must have access to this scene
        if not SessionGuard.can_access_scene(session, scene_index):
            raise ValueError(
                f"Session {session.id} cannot access scene {scene_index}"
            )
        
        # Cannot re-choose for already completed scenes
        completed_scenes = [choice.sceneIndex for choice in session.choices]
        if scene_index in completed_scenes:
            raise ValueError(
                f"Session {session.id} has already completed scene {scene_index}"
            )
        
        # Validate choice_id format
        expected_prefix = f"choice_{scene_index}_"
        if not choice_id.startswith(expected_prefix):
            raise ValueError(
                f"Invalid choice_id '{choice_id}' for scene {scene_index}. "
                f"Expected format: {expected_prefix}{{index}}"
            )


# Global session store instance
session_store = SessionStore()
