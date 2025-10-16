"""
Contract tests for NightLoom MVP scene retrieval API.

Tests the /api/sessions/{sessionId}/scenes/{sceneIndex} endpoint according to T030 requirements.
Implements Fail First testing strategy as specified in tasks.md.
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app
from app.services.session_store import session_store

client = TestClient(app)


class TestSceneRetrievalAPI:
    """Test cases for scene retrieval endpoint."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Clear session store
        session_store._sessions.clear()
    
    def test_scene_retrieval_success(self):
        """Test successful scene retrieval for valid session and scene index."""
        # Create session and confirm keyword first
        bootstrap_response = client.post("/api/sessions/start")
        assert bootstrap_response.status_code == 200
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        # Confirm keyword to progress to scene generation
        keyword_response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json={"keyword": session_data["keywordCandidates"][0], "source": "suggestion"}
        )
        assert keyword_response.status_code == 200
        
        # Retrieve scene 1
        response = client.get(f"/api/sessions/{session_id}/scenes/1")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure according to session-api.yaml
        assert "sessionId" in data
        assert "scene" in data
        assert "fallbackUsed" in data
        
        # Verify session ID matches
        assert data["sessionId"] == session_id
        
        # Verify scene structure
        scene = data["scene"]
        assert scene["sceneIndex"] == 1
        assert "narrative" in scene
        assert "choices" in scene
        assert "themeId" in scene
        
        # Verify choices structure (should have exactly 4 choices)
        choices = scene["choices"]
        assert len(choices) == 4
        for choice in choices:
            assert "id" in choice
            assert "text" in choice
            assert "weights" in choice
            assert isinstance(choice["weights"], dict)
    
    def test_scene_retrieval_all_scenes(self):
        """Test retrieval of all 4 scenes in sequence."""
        # Setup session with keyword confirmation
        bootstrap_response = client.post("/api/sessions/start")
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        keyword_response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json={"keyword": session_data["keywordCandidates"][0], "source": "suggestion"}
        )
        assert keyword_response.status_code == 200
        
        # Test all 4 scenes
        for scene_index in range(1, 5):
            response = client.get(f"/api/sessions/{session_id}/scenes/{scene_index}")
            
            assert response.status_code == 200
            data = response.json()
            
            scene = data["scene"]
            assert scene["sceneIndex"] == scene_index
            assert len(scene["choices"]) == 4
    
    def test_scene_retrieval_invalid_session_id(self):
        """Test scene retrieval with non-existent session ID."""
        fake_session_id = str(uuid.uuid4())
        
        response = client.get(f"/api/sessions/{fake_session_id}/scenes/1")
        
        # Should return 404 according to session-api.yaml
        assert response.status_code == 404
        error_data = response.json()
        assert error_data["error_code"] == "SESSION_NOT_FOUND"
        assert "message" in error_data
        assert "details" in error_data
    
    def test_scene_retrieval_invalid_session_id_format(self):
        """Test scene retrieval with malformed session ID."""
        invalid_session_id = "not-a-uuid"
        
        response = client.get(f"/api/sessions/{invalid_session_id}/scenes/1")
        
        # Should return 400 for invalid UUID format
        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error_code"] == "BAD_REQUEST"
    
    def test_scene_retrieval_invalid_scene_index(self):
        """Test scene retrieval with invalid scene index."""
        # Setup valid session
        bootstrap_response = client.post("/api/sessions/start")
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        keyword_response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json={"keyword": session_data["keywordCandidates"][0], "source": "suggestion"}
        )
        assert keyword_response.status_code == 200
        
        # Test invalid scene indices
        invalid_indices = [0, 5, -1, 100]
        
        for scene_index in invalid_indices:
            response = client.get(f"/api/sessions/{session_id}/scenes/{scene_index}")
            
            # Should return 400 for invalid scene index
            assert response.status_code == 400
            error_data = response.json()
            assert error_data["error_code"] == "INVALID_SCENE_INDEX"
    
    def test_scene_retrieval_session_not_ready(self):
        """Test scene retrieval for session that hasn't confirmed keyword."""
        # Create session but don't confirm keyword
        bootstrap_response = client.post("/api/sessions/start")
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        response = client.get(f"/api/sessions/{session_id}/scenes/1")
        
        # Should return 400 for invalid session state
        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error_code"] == "BAD_REQUEST"
        assert "state" in error_data["message"].lower()
    
    def test_scene_retrieval_performance(self):
        """Test that scene retrieval meets performance requirements."""
        import time
        
        # Setup session
        bootstrap_response = client.post("/api/sessions/start")
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        keyword_response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json={"keyword": session_data["keywordCandidates"][0], "source": "suggestion"}
        )
        assert keyword_response.status_code == 200
        
        # Measure scene retrieval performance
        start_time = time.time()
        response = client.get(f"/api/sessions/{session_id}/scenes/1")
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Should complete within 800ms (p95 requirement)
        latency_ms = (end_time - start_time) * 1000
        assert latency_ms < 800, f"Scene retrieval took {latency_ms}ms, exceeds 800ms requirement"
    
    @patch('app.clients.llm.llm_client')
    def test_scene_retrieval_with_llm_fallback(self, mock_llm_client):
        """Test scene retrieval when LLM service fails and fallback is used."""
        # Mock LLM failure
        mock_llm_client.generate_scene = AsyncMock(side_effect=Exception("LLM service unavailable"))
        
        # Setup session
        bootstrap_response = client.post("/api/sessions/start")
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        keyword_response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json={"keyword": session_data["keywordCandidates"][0], "source": "suggestion"}
        )
        assert keyword_response.status_code == 200
        
        response = client.get(f"/api/sessions/{session_id}/scenes/1")
        
        # Should succeed with fallback
        assert response.status_code == 200
        data = response.json()
        
        # Fallback should be indicated
        assert data["fallbackUsed"] is True
        
        # Should still have valid scene structure
        scene = data["scene"]
        assert scene["sceneIndex"] == 1
        assert len(scene["choices"]) == 4
    
    def test_scene_retrieval_concurrent_requests(self):
        """Test concurrent scene retrieval requests."""
        import threading
        import time
        
        # Setup session
        bootstrap_response = client.post("/api/sessions/start")
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        keyword_response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json={"keyword": session_data["keywordCandidates"][0], "source": "suggestion"}
        )
        assert keyword_response.status_code == 200
        
        results = []
        errors = []
        
        def make_request(scene_index):
            try:
                response = client.get(f"/api/sessions/{session_id}/scenes/{scene_index}")
                if response.status_code == 200:
                    results.append(response.json())
                else:
                    errors.append(f"Scene {scene_index}: Status {response.status_code}")
            except Exception as e:
                errors.append(f"Scene {scene_index}: {str(e)}")
        
        # Create concurrent requests for different scenes
        threads = []
        for scene_index in range(1, 5):
            thread = threading.Thread(target=make_request, args=(scene_index,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify all requests succeeded
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 4
        
        # Verify each scene has correct index
        scene_indices = sorted([r["scene"]["sceneIndex"] for r in results])
        assert scene_indices == [1, 2, 3, 4]
    
    def test_scene_retrieval_observability_logging(self):
        """Test that scene retrieval events are logged for observability."""
        with patch('app.services.observability.observability.log_scene_retrieval') as mock_log:
            # Setup session
            bootstrap_response = client.post("/api/sessions/start")
            session_data = bootstrap_response.json()
            session_id = session_data["sessionId"]
            
            keyword_response = client.post(
                f"/api/sessions/{session_id}/keyword",
                json={"keyword": session_data["keywordCandidates"][0], "source": "suggestion"}
            )
            assert keyword_response.status_code == 200
            
            response = client.get(f"/api/sessions/{session_id}/scenes/1")
            assert response.status_code == 200
            
            # Verify logging was called
            mock_log.assert_called_once()
            call_args = mock_log.call_args[0]
            
            # Verify log contains scene info
            assert str(call_args[0]) == session_id  # session_id
            assert call_args[1] == 1  # scene_index
            assert isinstance(call_args[2], float)  # latency_ms


class TestSceneRetrievalEdgeCases:
    """Edge case tests for scene retrieval functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        session_store._sessions.clear()
    
    def test_scene_retrieval_same_scene_multiple_times(self):
        """Test retrieving the same scene multiple times."""
        # Setup session
        bootstrap_response = client.post("/api/sessions/start")
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        keyword_response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json={"keyword": session_data["keywordCandidates"][0], "source": "suggestion"}
        )
        assert keyword_response.status_code == 200
        
        # Retrieve scene 1 multiple times
        responses = []
        for i in range(3):
            response = client.get(f"/api/sessions/{session_id}/scenes/1")
            assert response.status_code == 200
            responses.append(response.json())
        
        # All responses should be identical (scene content should be stable)
        first_scene = responses[0]["scene"]
        for response_data in responses[1:]:
            scene = response_data["scene"]
            assert scene["sceneIndex"] == first_scene["sceneIndex"]
            assert scene["narrative"] == first_scene["narrative"]
            assert len(scene["choices"]) == len(first_scene["choices"])
    
    def test_scene_retrieval_out_of_order(self):
        """Test retrieving scenes in non-sequential order."""
        # Setup session
        bootstrap_response = client.post("/api/sessions/start")
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        keyword_response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json={"keyword": session_data["keywordCandidates"][0], "source": "suggestion"}
        )
        assert keyword_response.status_code == 200
        
        # Retrieve scenes in reverse order
        scene_order = [4, 2, 3, 1]
        
        for scene_index in scene_order:
            response = client.get(f"/api/sessions/{session_id}/scenes/{scene_index}")
            assert response.status_code == 200
            data = response.json()
            assert data["scene"]["sceneIndex"] == scene_index
    
    def test_scene_retrieval_after_session_completion(self):
        """Test scene retrieval after session has been completed."""
        # This test documents expected behavior when session is in COMPLETED state
        # Implementation will determine if this should succeed or fail
        pass


@pytest.fixture
def session_with_scenes():
    """Fixture providing a session ready for scene retrieval."""
    bootstrap_response = client.post("/api/sessions/start")
    session_data = bootstrap_response.json()
    session_id = session_data["sessionId"]
    
    keyword_response = client.post(
        f"/api/sessions/{session_id}/keyword",
        json={"keyword": session_data["keywordCandidates"][0], "source": "suggestion"}
    )
    
    return {
        "session_id": session_id,
        "keyword": session_data["keywordCandidates"][0],
        "theme_id": session_data["themeId"]
    }
