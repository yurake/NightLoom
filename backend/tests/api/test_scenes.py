"""Test suite for scene retrieval endpoints - User Story 2 Contract Tests."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import uuid

from app.main import app
from app.models.session import Session, SessionState, Scene, Choice

client = TestClient(app)


class TestSceneRetrieval:
    """Contract tests for GET /api/sessions/{sessionId}/scenes/{sceneIndex}."""

    def test_get_scene_valid_session_and_index(self, mock_session_in_store):
        """Test retrieving a valid scene for an active session."""
        session_id = str(uuid.uuid4())
        scene_index = 2
        
        # Create session with scene 1 completed (so scene 2 is accessible)
        mock_session = mock_session_in_store(
            session_id=session_id,
            state=SessionState.PLAY,
            selected_keyword="探検",
            theme_id="adventure",
            initial_character="た",
            completed_scenes=[1]  # Scene 1 completed, so scene 2 is accessible
        )
        
        # Mock scene data
        mock_scene = Scene(
            sceneIndex=scene_index,
            themeId="adventure",
            narrative="森の奥で分かれ道を発見した。どちらの道を選ぶ？",
            choices=[
                Choice(
                    id=f"choice_{scene_index}_1",
                    text="左の明るい道を進む",
                    weights={"curiosity": 0.8, "caution": -0.3}
                ),
                Choice(
                    id=f"choice_{scene_index}_2",
                    text="右の神秘的な道を進む",
                    weights={"curiosity": 1.0, "caution": 0.2}
                ),
                Choice(
                    id=f"choice_{scene_index}_3",
                    text="立ち止まって周囲を観察する",
                    weights={"curiosity": 0.2, "caution": 0.9}
                ),
                Choice(
                    id=f"choice_{scene_index}_4",
                    text="来た道を戻る",
                    weights={"curiosity": -0.5, "caution": 1.0}
                )
            ]
        )
        
        with patch('app.services.session.SessionService.get_scene') as mock_get_scene:
            mock_get_scene.return_value = mock_scene
            
            response = client.get(f"/api/sessions/{session_id}/scenes/{scene_index}")
            
            assert response.status_code == 200
            data = response.json()
            
            # Validate response structure
            assert "sessionId" in data
            assert "scene" in data
            assert data["sessionId"] == session_id
            
            # Validate scene structure
            scene = data["scene"]
            assert scene["sceneIndex"] == scene_index
            assert scene["themeId"] == "adventure"
            assert "narrative" in scene
            assert "choices" in scene
            assert len(scene["choices"]) == 4
            
            # Validate choice structure
            for i, choice in enumerate(scene["choices"]):
                assert "id" in choice
                assert "text" in choice
                assert "weights" in choice
                assert choice["id"] == f"choice_{scene_index}_{i+1}"

    def test_get_scene_session_not_found(self):
        """Test scene retrieval with non-existent session."""
        session_id = str(uuid.uuid4())
        
        # No session created - session_store should be empty due to autouse fixture
        response = client.get(f"/api/sessions/{session_id}/scenes/1")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error_code"] == "SESSION_NOT_FOUND"
        assert "session_id" in data["detail"]["details"]

    def test_get_scene_invalid_session_state(self, mock_session_in_store):
        """Test scene retrieval for session in INIT state (not allowed)."""
        session_id = str(uuid.uuid4())
        
        mock_session = mock_session_in_store(
            session_id=session_id,
            state=SessionState.INIT,  # Invalid state for scene retrieval
            selected_keyword=None,  # No keyword selected yet
            theme_id="serene",
            initial_character="あ"
        )
        
        response = client.get(f"/api/sessions/{session_id}/scenes/1")
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error_code"] == "BAD_REQUEST"

    def test_get_scene_invalid_scene_index(self, mock_session_in_store):
        """Test scene retrieval with invalid scene index."""
        session_id = str(uuid.uuid4())
        
        mock_session = mock_session_in_store(
            session_id=session_id,
            state=SessionState.PLAY,
            selected_keyword="冒険",
            theme_id="adventure",
            initial_character="ぼ"
        )
        
        # Test scene index out of bounds (FastAPI will handle path validation)
        # Test negative numbers and very large numbers
        for invalid_index in [-1, 10]:
            response = client.get(f"/api/sessions/{session_id}/scenes/{invalid_index}")
            
            # FastAPI path validation should return 422 for out-of-range values
            assert response.status_code == 422

    def test_get_scene_llm_service_unavailable(self, mock_session_in_store):
        """Test scene retrieval when LLM service fails (503 fallback)."""
        session_id = str(uuid.uuid4())
        
        mock_session = mock_session_in_store(
            session_id=session_id,
            state=SessionState.PLAY,
            selected_keyword="平和",
            theme_id="serene",
            initial_character="へ"
        )
        
        with patch('app.services.session.SessionService.load_scene') as mock_load_scene:
            mock_load_scene.side_effect = Exception("LLM service unavailable")
            
            response = client.get(f"/api/sessions/{session_id}/scenes/1")
            
            # Should return 503 with error details or fallback scene
            assert response.status_code in [200, 503]
            
            if response.status_code == 200:
                # Fallback scene returned
                data = response.json()
                assert "fallbackUsed" in data
                assert data["fallbackUsed"] is True
            else:
                # Error response
                data = response.json()
                assert data["detail"]["error_code"] == "LLM_SERVICE_UNAVAILABLE"

    def test_get_scene_malformed_uuid(self):
        """Test scene retrieval with malformed session ID."""
        invalid_session_id = "not-a-uuid"
        
        response = client.get(f"/api/sessions/{invalid_session_id}/scenes/1")
        
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"

    def test_get_scene_performance_contract(self, mock_session_in_store):
        """Test that scene retrieval meets performance requirements."""
        session_id = str(uuid.uuid4())
        
        mock_session = mock_session_in_store(
            session_id=session_id,
            state=SessionState.PLAY,
            selected_keyword="集中",
            theme_id="focus",
            initial_character="し"
        )
        
        mock_scene = Scene(
            sceneIndex=1,
            themeId="focus",
            narrative="静かな図書館で勉強中、隣の席が空いている。",
            choices=[
                Choice(id="choice_1_1", text="そのまま集中して勉強を続ける", weights={"focus": 1.0}),
                Choice(id="choice_1_2", text="休憩を取って外の景色を見る", weights={"focus": -0.2}),
                Choice(id="choice_1_3", text="友人に連絡を取る", weights={"focus": -0.8}),
                Choice(id="choice_1_4", text="別の場所に移動する", weights={"focus": 0.1})
            ]
        )
        
        with patch('app.services.session.SessionService.get_scene') as mock_get_scene:
            mock_get_scene.return_value = mock_scene
            
            import time
            start_time = time.time()
            response = client.get(f"/api/sessions/{session_id}/scenes/1")
            end_time = time.time()
            
            assert response.status_code == 200
            
            # Performance requirement: p95 ≤ 800ms
            response_time_ms = (end_time - start_time) * 1000
            
            # In unit tests, this should be very fast (<100ms typically)
            # This is more of a smoke test; real performance testing is in E2E
            assert response_time_ms < 1000, f"Response time {response_time_ms:.1f}ms exceeds reasonable limit"


class TestSceneProgressTracking:
    """Tests for scene progression and state management."""
    
    def test_scene_sequence_validation(self, mock_session_in_store):
        """Test that scenes can only be accessed in sequence."""
        session_id = str(uuid.uuid4())
        
        # Mock session that has only completed scene 1
        mock_session = mock_session_in_store(
            session_id=session_id,
            state=SessionState.PLAY,
            selected_keyword="順序",
            theme_id="focus",
            initial_character="じ",
            completed_scenes=[1]  # Only scene 1 completed
        )
        
        with patch('app.services.session.SessionService.get_scene') as mock_get_scene:
            mock_scene = Scene(
                sceneIndex=2,
                themeId="focus",
                narrative="次のシーン。",
                choices=[
                    Choice(id="choice_2_1", text="選択肢1", weights={"test": 1.0}),
                    Choice(id="choice_2_2", text="選択肢2", weights={"test": 0.5}),
                    Choice(id="choice_2_3", text="選択肢3", weights={"test": 0.3}),
                    Choice(id="choice_2_4", text="選択肢4", weights={"test": 0.1})
                ]
            )
            mock_get_scene.return_value = mock_scene
            
            # Should be able to access scene 2 (next scene)
            response = client.get(f"/api/sessions/{session_id}/scenes/2")
            assert response.status_code == 200
            
            # Should not be able to access scene 4 (skipping scenes)
            response = client.get(f"/api/sessions/{session_id}/scenes/4")
            assert response.status_code == 400
            data = response.json()
            assert data["detail"]["error_code"] == "BAD_REQUEST"

    def test_scene_data_consistency(self, mock_session_in_store):
        """Test that scene data structure is consistent across calls."""
        session_id = str(uuid.uuid4())
        
        mock_session = mock_session_in_store(
            session_id=session_id,
            state=SessionState.PLAY,
            selected_keyword="一貫性",
            theme_id="serene",
            initial_character="い",
            completed_scenes=[1, 2]  # Scenes 1-2 completed, so scene 3 is accessible
        )
        
        mock_scene = Scene(
            sceneIndex=3,
            themeId="serene",
            narrative="湖のほとりで夕日を眺めている。",
            choices=[
                Choice(id="choice_3_1", text="写真を撮る", weights={"aesthetic": 0.8}),
                Choice(id="choice_3_2", text="瞑想する", weights={"mindfulness": 1.0}),
                Choice(id="choice_3_3", text="スケッチする", weights={"creativity": 0.9}),
                Choice(id="choice_3_4", text="そのまま眺める", weights={"presence": 0.7})
            ]
        )
        
        with patch('app.services.session.SessionService.get_scene') as mock_get_scene:
            mock_get_scene.return_value = mock_scene
            
            # Call the same scene multiple times
            responses = []
            for _ in range(3):
                response = client.get(f"/api/sessions/{session_id}/scenes/3")
                responses.append(response.json())
            
            # All responses should be identical (except for timestamp differences)
            for i in range(1, len(responses)):
                # Remove timestamps for comparison as they may differ
                resp1 = {k: v for k, v in responses[0].items() if 'timestamp' not in str(k).lower()}
                resp2 = {k: v for k, v in responses[i].items() if 'timestamp' not in str(k).lower()}
                assert resp2 == resp1, "Scene data should be consistent across calls"
