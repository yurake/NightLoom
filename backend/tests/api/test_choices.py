
"""
Contract tests for NightLoom MVP choice submission API.

Tests the /api/sessions/{sessionId}/scenes/{sceneIndex}/choice endpoint according to T031 requirements.
Implements Fail First testing strategy as specified in tasks.md.
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app
from app.services.session_store import session_store

client = TestClient(app)


class TestChoiceSubmissionAPI:
    """Test cases for choice submission endpoint."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Clear session store
        session_store._sessions.clear()
    
    def test_choice_submission_success(self):
        """Test successful choice submission for valid session and scene."""
        # Setup session with scenes available
        bootstrap_response = client.post("/api/sessions/start")
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        keyword_response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json={"keyword": session_data["keywordCandidates"][0], "source": "suggestion"}
        )
        assert keyword_response.status_code == 200
        
        # Get scene 1 to obtain valid choice IDs
        scene_response = client.get(f"/api/sessions/{session_id}/scenes/1")
        assert scene_response.status_code == 200
        scene_data = scene_response.json()
        scene = scene_data["scene"]
        first_choice_id = scene["choices"][0]["id"]
        
        # Submit choice for scene 1
        choice_request = {"choiceId": first_choice_id}
        response = client.post(
            f"/api/sessions/{session_id}/scenes/1/choice",
            json=choice_request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure according to session-api.yaml
        assert "sessionId" in data
        assert "sceneCompleted" in data
        assert data["sessionId"] == session_id
        assert data["sceneCompleted"] is True
        
        # Should have nextScene for scenes 1-3, null for scene 4
        if "nextScene" in data and data["nextScene"] is not None:
            next_scene = data["nextScene"]
            assert next_scene["sceneIndex"] == 2
            assert "narrative" in next_scene
            assert "choices" in next_scene
            assert len(next_scene["choices"]) == 4
    
    def test_choice_submission_all_scenes_progression(self):
        """Test choice submission through all 4 scenes."""
        # Setup session
        bootstrap_response = client.post("/api/sessions/start")
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        keyword_response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json={"keyword": session_data["keywordCandidates"][0], "source": "suggestion"}
        )
        assert keyword_response.status_code == 200
        
        # Progress through all 4 scenes
        for scene_index in range(1, 5):
            # Get scene choices
            scene_response = client.get(f"/api/sessions/{session_id}/scenes/{scene_index}")
            assert scene_response.status_code == 200
            scene = scene_response.json()["scene"]
            
            # Submit choice
            choice_id = scene["choices"][0]["id"]  # Always select first choice
            choice_response = client.post(
                f"/api/sessions/{session_id}/scenes/{scene_index}/choice",
                json={"choiceId": choice_id}
            )
            
            assert choice_response.status_code == 200
            choice_data = choice_response.json()
            
            # Verify scene completion
            assert choice_data["sceneCompleted"] is True
            
            # Scene 4 should have no next scene, others should
            if scene_index < 4:
                assert choice_data["nextScene"] is not None
                assert choice_data["nextScene"]["sceneIndex"] == scene_index + 1
            else:
                # Scene 4 completion should either have null nextScene or indicate completion
                assert choice_data.get("nextScene") is None or choice_data["nextScene"] is None
    
    def test_choice_submission_invalid_session_id(self):
        """Test choice submission with non-existent session ID."""
        fake_session_id = str(uuid.uuid4())
        
        choice_request = {"choiceId": "choice_1_1"}
        response = client.post(
            f"/api/sessions/{fake_session_id}/scenes/1/choice",
            json=choice_request
        )
        
        # Should return 404 according to session-api.yaml
        assert response.status_code == 404
        error_data = response.json()
        assert error_data["error_code"] == "SESSION_NOT_FOUND"
    
    def test_choice_submission_invalid_session_id_format(self):
        """Test choice submission with malformed session ID."""
        invalid_session_id = "not-a-uuid"
        
        choice_request = {"choiceId": "choice_1_1"}
        response = client.post(
            f"/api/sessions/{invalid_session_id}/scenes/1/choice",
            json=choice_request
        )
        
        # Should return 400 for invalid UUID format
        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error_code"] == "BAD_REQUEST"
    
    def test_choice_submission_invalid_scene_index(self):
        """Test choice submission with invalid scene index."""
        # Setup session
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
            choice_request = {"choiceId": "choice_1_1"}
            response = client.post(
                f"/api/sessions/{session_id}/scenes/{scene_index}/choice",
                json=choice_request
            )
            
            # Should return 400 for invalid scene index
            assert response.status_code == 400
            error_data = response.json()
            assert error_data["error_code"] == "INVALID_SCENE_INDEX"
    
    def test_choice_submission_invalid_choice_id(self):
        """Test choice submission with non-existent choice ID."""
        # Setup session
        bootstrap_response = client.post("/api/sessions/start")
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        keyword_response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json={"keyword": session_data["keywordCandidates"][0], "source": "suggestion"}
        )
        assert keyword_response.status_code == 200
        
        # Submit invalid choice ID
        choice_request = {"choiceId": "invalid_choice_id"}
        response = client.post(
            f"/api/sessions/{session_id}/scenes/1/choice",
            json=choice_request
        )
        
        # Should return 400 for invalid choice
        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error_code"] == "INVALID_CHOICE"
    
    def test_choice_submission_missing_choice_id(self):
        """Test choice submission with missing choiceId field."""
        # Setup session
        bootstrap_response = client.post("/api/sessions/start")
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        keyword_response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json={"keyword": session_data["keywordCandidates"][0], "source": "suggestion"}
        )
        assert keyword_response.status_code == 200
        
        # Submit request without choiceId
        response = client.post(
            f"/api/sessions/{session_id}/scenes/1/choice",
            json={}
        )
        
        # Should return 422 for validation error
        assert response.status_code == 422
        error_data = response.json()
        assert "choiceId" in str(error_data)
    
    def test_choice_submission_empty_choice_id(self):
        """Test choice submission with empty choiceId."""
        # Setup session
        bootstrap_response = client.post("/api/sessions/start")
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        keyword_response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json={"keyword": session_data["keywordCandidates"][0], "source": "suggestion"}
        )
        assert keyword_response.status_code == 200
        
        # Submit empty choice ID
        choice_request = {"choiceId": ""}
        response = client.post(
            f"/api/sessions/{session_id}/scenes/1/choice",
            json=choice_request
        )
        
        # Should return 400 for invalid choice
        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error_code"] == "INVALID_CHOICE"
    
    def test_choice_submission_duplicate_for_same_scene(self):
        """Test submitting choice twice for the same scene."""
        # Setup session
        bootstrap_response = client.post("/api/sessions/start")
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        keyword_response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json={"keyword": session_data["keywordCandidates"][0], "source": "suggestion"}
        )
        assert keyword_response.status_code == 200
        
        # Get valid choice ID
        scene_response = client.get(f"/api/sessions/{session_id}/scenes/1")
        scene_data = scene_response.json()
        choice_id = scene_data["scene"]["choices"][0]["id"]
        
        # First submission should succeed
        choice_request = {"choiceId": choice_id}
        response1 = client.post(
            f"/api/sessions/{session_id}/scenes/1/choice",
            json=choice_request
        )
        assert response1.status_code == 200
        
        # Second submission should fail (scene already completed)
        response2 = client.post(
            f"/api/sessions/{session_id}/scenes/1/choice",
            json=choice_request
        )
        
        # Should return 400 for invalid state
        assert response2.status_code == 400
        error_data = response2.json()
        assert error_data["error_code"] == "BAD_REQUEST"
        assert "already completed" in error_data["message"].lower() or "invalid state" in error_data["message"].lower()
    
    def test_choice_submission_performance(self):
        """Test that choice submission meets performance requirements."""
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
        
        # Get valid choice ID
        scene_response = client.get(f"/api/sessions/{session_id}/scenes/1")
        scene_data = scene_response.json()
        choice_id = scene_data["scene"]["choices"][0]["id"]
        
        # Measure choice submission performance
        start_time = time.time()
        response = client.post(
            f"/api/sessions/{session_id}/scenes/1/choice",
            json={"choiceId": choice_id}
        )
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Should complete within 800ms (p95 requirement)
        latency_ms = (end_time - start_time) * 1000
        assert latency_ms < 800, f"Choice submission took {latency_ms}ms, exceeds 800ms requirement"
    
    def test_choice_submission_score_accumulation(self):
        """Test that choice weights are properly accumulated in session."""
        # Setup session
        bootstrap_response = client.post("/api/sessions/start")
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        keyword_response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json={"keyword": session_data["keywordCandidates"][0], "source": "suggestion"}
        )
        assert keyword_response.status_code == 200
        
        # Get scene and choice weights
        scene_response = client.get(f"/api/sessions/{session_id}/scenes/1")
        scene_data = scene_response.json()
        first_choice = scene_data["scene"]["choices"][0]
        choice_weights = first_choice["weights"]
        
        # Submit choice
        response = client.post(
            f"/api/sessions/{session_id}/scenes/1/choice",
            json={"choiceId": first_choice["id"]}
        )
        
        assert response.status_code == 200
        
        # Verify session state contains accumulated scores
        # This test verifies the internal logic but may need adjustment based on implementation
        stored_session = session_store.get_session(uuid.UUID(session_id))
        if stored_session and hasattr(stored_session, 'accumulatedScores'):
            for axis_id, weight in choice_weights.items():
                assert axis_id in stored_session.accumulatedScores
                # First choice, so accumulated score should equal choice weight
                assert stored_session.accumulatedScores[axis_id] == weight
    
    @patch('app.clients.llm.llm_client')
    def test_choice_submission_with_llm_fallback(self, mock_llm_client):
        """Test choice submission when LLM service fails during next scene generation."""
        # Mock LLM failure for scene generation
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
        
        # Get valid choice ID
        scene_response = client.get(f"/api/sessions/{session_id}/scenes/1")
        scene_data = scene_response.json()
        choice_id = scene_data["scene"]["choices"][0]["id"]
        
        # Submit choice (should trigger next scene generation)
        response = client.post(
            f"/api/sessions/{session_id}/scenes/1/choice",
            json={"choiceId": choice_id}
        )
        
        # Should succeed with fallback
        assert response.status_code == 200
        data = response.json()
        
        # Choice should be recorded
        assert data["sceneCompleted"] is True
        
        # Next scene should be generated using fallback
        if data.get("nextScene"):
            assert data["nextScene"]["sceneIndex"] == 2
    
    def test_choice_submission_observability_logging(self):
        """Test that choice submission events are logged for observability."""
        with patch('app.services.observability.observability.log_choice_submission') as mock_log:
            # Setup session
            bootstrap_response = client.post("/api/sessions/start")
            session_data = bootstrap_response.json()
            session_id = session_data["sessionId"]
            
            keyword_response = client.post(
                f"/api/sessions/{session_id}/keyword",
                json={"keyword": session_data["keywordCandidates"][0], "source": "suggestion"}
            )
            assert keyword_response.status_code == 200
            
            # Get valid choice ID
            scene_response = client.get(f"/api/sessions/{session_id}/scenes/1")
            scene_data = scene_response.json()
            choice_id = scene_data["scene"]["choices"][0]["id"]
            
            # Submit choice
            response = client.post(
                f"/api/sessions/{session_id}/scenes/1/choice",
                json={"choiceId": choice_id}
            )
            
            assert response.status_code == 200
            
            # Verify logging was called
            mock_log.assert_called_once()
            call_args = mock_log.call_args[0]
            
            # Verify log contains choice info
            assert str(call_args[0]) == session_id  # session_id
            assert call_args[1] == 1  # scene_index
            assert call_args[2] == choice_id  # choice_id
            assert isinstance(call_args[3], float)  # latency_ms


class TestChoiceSubmissionEdgeCases:
    """Edge case tests for choice submission functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        session_store._sessions.clear()
    
    def test_choice_submission_session_not_ready(self):
        """Test choice submission for session that hasn't confirmed keyword."""
        # Create session but don't confirm keyword
        bootstrap_response = client.post("/api/sessions/start")
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        # Try to submit choice without keyword confirmation
        choice_request = {"choiceId": "choice_1_1"}
        response = client.post(
            f"/api/sessions/{session_id}/scenes/1/choice",
            json=choice_request
        )
        
        # Should return 400 for invalid session state
        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error_code"] == "BAD_REQUEST"
        assert "state" in error_data["message"].lower()
    
    def test_choice_submission_concurrent_requests_same_scene(self):
        """Test concurrent choice submissions for the same scene."""
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
        
        # Get valid choice IDs
        scene_response = client.get(f"/api/sessions/{session_id}/scenes/1")
        scene_data = scene_response.json()
        choices = scene_data["scene"]["choices"]
        
        results = []
        errors = []
        
        def submit_choice(choice_index):
            try:
                choice_id = choices[choice_index]["id"]
                response = client.post(
                    f"/api/sessions/{session_id}/scenes/1/choice",
                    json={"choiceId": choice_id}
                )
                results.append({"status": response.status_code, "choice_index": choice_index})
            except Exception as e:
                errors.append(f"Choice {choice_index}: {str(e)}")
        
        # Submit all 4 choices concurrently (only one should succeed)
        threads = []
        for i in range(4):
            thread = threading.Thread(target=submit_choice, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Only one choice should succeed, others should fail
        success_count = len([r for r in results if r["status"] == 200])
        failure_count = len([r for r in results if r["status"] != 200])
        
        assert success_count == 1, f"Expected 1 success, got {success_count}"
        assert failure_count == 3, f"Expected 3 failures, got {failure_count}"
        assert len(errors) == 0, f"Unexpected errors: {errors}"
    
    def test_choice_submission_malformed_json(self):
        """Test choice submission with malformed JSON."""
        # Setup session
        bootstrap_response = client.post("/api/sessions/start")
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        keyword_response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json={"keyword": session_data["keywordCandidates"][0], "source": "suggestion"}
        )
        assert keyword_response.status_code == 200
        
        # Submit malformed request
        response = client.post(
            f"/api/sessions/{session_id}/scenes/1/choice",
            data="invalid json"
        )
        
        # Should return 422 for JSON decode error
        assert response.status_code == 422
    
    def test_choice_submission_wrong_scene_choice_mismatch(self):
        """Test submitting choice ID from one scene to another scene."""
        # Setup session
        bootstrap_response = client.post("/api/sessions/start")
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        keyword_response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json={"keyword": session_data["keywordCandidates"][0], "source": "suggestion"}
        )
        assert keyword_response.status_code == 200
        
        # Get choice ID from scene 1
        scene1_response = client.get(f"/api/sessions/{session_id}/scenes/1")
        scene1_data = scene1_response.json()
        scene1_choice_id = scene1_data["scene"]["choices"][0]["id"]
        
        # Try to submit scene 1 choice ID to scene 2
        response = client.post(
            f"/api/sessions/{session_id}/scenes/2/choice",
            json={"choiceId": scene1_choice_id}
        )
        
        # Should return 400 for invalid choice (choice ID doesn't match scene)
        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error_code"] == "INVALID_CHOICE"


@pytest.fixture
def session_with_choices():
    """Fixture providing a session ready for choice submission."""
    bootstrap_response = client.post("/api/sessions/start")
    session_data = bootstrap_response.json()
    session_id = session_data["sessionId"]
    
    keyword_response = client.post(
        f"/api/sessions/{session_id}/keyword",
        json={"keyword": session_data["keywordCandidates"][0], "source": "suggestion"}
    )
    
    scene_response = client.get(f"/api/sessions/{session_id}/scenes/1")
    scene_data = scene_response.json()
    
    return {
        "session_id": session_id,
        "keyword": session_data["keywordCandidates"][0],
        "scene": scene_data["scene"],
        "choices": scene_data["scene"]["choices"]
    }
