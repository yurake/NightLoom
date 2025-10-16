"""Test configuration for backend package."""

from __future__ import annotations

import sys
from pathlib import Path
import pytest
from uuid import UUID
from unittest.mock import patch

# Ensure `import app` resolves to the backend application package when tests run
# via uv / pytest in isolated environments.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models.session import Session, SessionState
from app.services.session_store import session_store


@pytest.fixture(autouse=True)
def clear_session_store():
    """Clear global session store before each test."""
    session_store._sessions.clear()
    yield
    session_store._sessions.clear()


@pytest.fixture
def mock_session_in_store():
    """Create a mock session and store it in the global session_store."""
    def _create_session(
        session_id: str,
        state: SessionState = SessionState.PLAY,
        selected_keyword: str = "テスト",
        theme_id: str = "focus",
        initial_character: str = "て",
        keyword_candidates: list = None,
        completed_scenes: list = None
    ) -> Session:
        if keyword_candidates is None:
            keyword_candidates = ["テスト", "てがみ", "てんき", "てつだい"]
        
        # Initialize with empty scenes list
        from app.models.session import Scene, Choice
        scenes = []
        
        # Always create mock scenes for consistency, even in INIT state
        for i in range(1, 5):  # Create scenes 1-4
            scene = Scene(
                sceneIndex=i,
                themeId=theme_id,
                narrative=f"テストシーン {i} の物語",
                choices=[
                    Choice(id=f"choice_{i}_1", text="選択肢1", weights={"test": 0.8}),
                    Choice(id=f"choice_{i}_2", text="選択肢2", weights={"test": 0.6}),
                    Choice(id=f"choice_{i}_3", text="選択肢3", weights={"test": 0.4}),
                    Choice(id=f"choice_{i}_4", text="選択肢4", weights={"test": 0.2})
                ]
            )
            scenes.append(scene)
        
        session = Session(
            id=session_id,
            state=state,
            selectedKeyword=selected_keyword if state == SessionState.PLAY else None,
            themeId=theme_id,
            initialCharacter=initial_character,
            keywordCandidates=keyword_candidates,
            scenes=scenes
        )
        
        # Add completed scenes if specified
        if completed_scenes:
            session.choices = []
            for scene_index in completed_scenes:
                choice_record = type('ChoiceRecord', (), {
                    'sceneIndex': scene_index,
                    'choiceId': f'choice_{scene_index}_1',
                    'timestamp': '2024-01-01T10:00:00Z'
                })()
                session.choices.append(choice_record)
        
        # Store in global session_store
        session_uuid = UUID(session_id) if isinstance(session_id, str) else session_id
        session_store._sessions[session_uuid] = session
        return session
    
    return _create_session


@pytest.fixture
def patch_session_service_methods():
    """Patch commonly used session service methods for tests."""
    with patch('app.services.session.SessionService.get_scene') as mock_get_scene, \
         patch('app.services.session.SessionService.submit_choice') as mock_submit_choice, \
         patch('app.services.session.SessionService.generate_next_scene') as mock_generate_next:
        yield {
            'get_scene': mock_get_scene,
            'submit_choice': mock_submit_choice,
            'generate_next_scene': mock_generate_next
        }
