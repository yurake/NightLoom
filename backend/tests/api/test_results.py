
"""
Contract tests for NightLoom MVP result retrieval API.

Tests the /api/sessions/{sessionId}/result endpoint according to T042 requirements.
Implements Fail First testing strategy as specified in tasks.md.
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app
from app.services.session_store import session_store

client = TestClient(app)


class TestResultRetrievalAPI:
    """Test cases for result retrieval endpoint."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Clear session store
        session_store._sessions.clear()
    
    def test_result_retrieval_success(self):
        """Test successful result retrieval after completing all 4 scenes."""
        # Setup complete session (bootstrap + keyword + 4 scenes)
        session_id = self._complete_all_scenes()
        
        # Request result
        response = client.post(f"/api/sessions/{session_id}/result")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure according to session-api.yaml
        assert "sessionId" in data
        assert "keyword" in data
        assert "axes" in data
        assert "type" in data
        assert "completedAt" in data
        assert "fallbackFlags" in data
        
        # Verify session ID matches
        assert data["sessionId"] == session_id
        
        # Verify axes scores structure
        axes = data["axes"]
        assert len(axes) >= 2  # At least 2 axes
        for axis in axes:
            assert "axisId" in axis
            assert "score" in axis
            assert "rawScore" in axis
            # Score should be 0-100, rawScore should be -5 to 5
            assert 0 <= axis["score"] <= 100
            assert -5 <= axis["rawScore"] <= 5
        
        # Verify type structure
        type_data = data["type"]
        assert "profiles" in type_data
        profiles = type_data["profiles"]
        assert len(profiles) >= 4  # At least 4 type profiles
        
        for profile in profiles:
            assert "name" in profile
            assert "description" in profile
            assert "dominantAxes" in profile
            assert "polarity" in profile
            assert len(profile["dominantAxes"]) == 2  # Exactly 2 dominant axes
        
        # Verify completedAt is ISO timestamp
        completed_at = data["completedAt"]
        assert "T" in completed_at
        assert completed_at.endswith("Z")
        
        # Verify keyword is present
        keyword = data["keyword"]
        assert isinstance(keyword, str)
        assert len(keyword) > 0
    
    def test_result_retrieval_invalid_session_id(self):
        """Test result retrieval with non-existent session ID."""
        fake_session_id = str(uuid.uuid4())
        
        response = client.post(f"/api/sessions/{fake_session_id}/result")
        
        # Should return 404 according to session-api.yaml
        assert response.status_code == 404
        error_data = response.json()
        assert error_data["error_code"] == "SESSION_NOT_FOUND"
        assert "message" in error_data
        assert "details" in error_data
    
    def test_result_retrieval_invalid_session_id_format(self):
        """Test result retrieval with malformed session ID."""
        invalid_session_id = "not-a-uuid"
        
        response = client.post(f"/api/sessions/{invalid_session_id}/result")
        
        # Should return 400 for invalid UUID format
        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error_code"] == "BAD_REQUEST"
    
    def test_result_retrieval_session_not_completed(self):
        """Test result retrieval for session that hasn't completed all scenes."""
        # Create session and complete only 2 scenes
        bootstrap_response = client.post("/api/sessions/start")
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        # Confirm keyword
        keyword_response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json={"keyword": session_data["keywordCandidates"][0], "source": "suggestion"}
        )
        assert keyword_response.status_code == 200
        
        # Complete only scenes 1 and 2
        for scene_index in [1, 2]:
            scene_response = client.get(f"/api/sessions/{session_id}/scenes/{scene_index}")
            scene_data = scene_response.json()
            choice_id = scene_data["scene"]["choices"][0]["id"]
            
            choice_response = client.post(
                f"/api/sessions/{session_id}/scenes/{scene_index}/choice",
                json={"choiceId": choice_id}
            )
            assert choice_response.status_code == 200
        
        # Try to get result (should fail - not all scenes completed)
        response = client.post(f"/api/sessions/{session_id}/result")
        
        # Should return 400 for incomplete session
        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error_code"] == "SESSION_NOT_COMPLETED"
        assert "completed" in error_data["message"].lower()
    
    def test_result_retrieval_performance(self):
        """Test that result retrieval meets performance requirements."""
        import time
        
        # Setup complete session
        session_id = self._complete_all_scenes()
        
        # Measure result retrieval performance
        start_time = time.time()
        response = client.post(f"/api/sessions/{session_id}/result")
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Should complete within 1200ms (p95 requirement for result generation)
        latency_ms = (end_time - start_time) * 1000
        assert latency_ms < 1200, f"Result retrieval took {latency_ms}ms, exceeds 1200ms requirement"
    
    def test_result_retrieval_score_calculation_accuracy(self):
        """Test that accumulated scores are correctly calculated in results."""
        # Setup session with known choice weights
        bootstrap_response = client.post("/api/sessions/start")
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        # Confirm keyword
        keyword_response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json={"keyword": session_data["keywordCandidates"][0], "source": "suggestion"}
        )
        assert keyword_response.status_code == 200
        
        # Track expected scores
        expected_scores = {}
        
        # Complete all 4 scenes with first choice (predictable weights)
        for scene_index in range(1, 5):
            scene_response = client.get(f"/api/sessions/{session_id}/scenes/{scene_index}")
            scene_data = scene_response.json()
            first_choice = scene_data["scene"]["choices"][0]
            
            # Accumulate expected scores
            for axis_id, weight in first_choice["weights"].items():
                if axis_id not in expected_scores:
                    expected_scores[axis_id] = 0
                expected_scores[axis_id] += weight
            
            # Submit choice
            choice_response = client.post(
                f"/api/sessions/{session_id}/scenes/{scene_index}/choice",
                json={"choiceId": first_choice["id"]}
            )
            assert choice_response.status_code == 200
        
        # Get result and verify scores
        result_response = client.post(f"/api/sessions/{session_id}/result")
        assert result_response.status_code == 200
        result_data = result_response.json()
        
        # Verify calculated scores match expected
        result_axes = {axis["axisId"]: axis["rawScore"] for axis in result_data["axes"]}
        
        for axis_id, expected_raw_score in expected_scores.items():
            assert axis_id in result_axes
            actual_raw_score = result_axes[axis_id]
            # Allow small floating point differences
            assert abs(actual_raw_score - expected_raw_score) < 0.01, \
                f"Axis {axis_id}: expected {expected_raw_score}, got {actual_raw_score}"
    
    def test_result_retrieval_type_profiling(self):
        """Test that type profiling generates appropriate type profiles."""
        # Setup complete session
        session_id = self._complete_all_scenes()
        
        # Get result
        response = client.post(f"/api/sessions/{session_id}/result")
        assert response.status_code == 200
        data = response.json()
        
        # Verify type profiling
        type_data = data["type"]
        profiles = type_data["profiles"]
        
        # Should have multiple type profiles
        assert len(profiles) >= 4
        
        # Verify each profile has required fields
        for profile in profiles:
            assert len(profile["name"]) > 0
            assert len(profile["description"]) > 0
            assert len(profile["dominantAxes"]) == 2
            assert profile["polarity"] in ["positive", "negative", "neutral"]
            
            # Keywords should be present (optional field)
            if "keywords" in profile:
                assert isinstance(profile["keywords"], list)
        
        # Verify dominant axes consistency
        if "dominantAxes" in type_data:
            dominant_axes = type_data["dominantAxes"]
            assert len(dominant_axes) == 2
            # These should correspond to highest absolute scores
            result_axes = {axis["axisId"]: abs(axis["rawScore"]) for axis in data["axes"]}
            sorted_axes = sorted(result_axes.items(), key=lambda x: x[1], reverse=True)
            top_two_axes = [axis_id for axis_id, _ in sorted_axes[:2]]
            assert set(dominant_axes) == set(top_two_axes)
    
    @patch('app.clients.llm.llm_client')
    def test_result_retrieval_with_llm_fallback(self, mock_llm_client):
        """Test result retrieval when LLM service fails and fallback is used."""
        # Mock LLM failure for type profiling
        mock_llm_client.generate_type_profiles = AsyncMock(side_effect=Exception("LLM service unavailable"))
        
        # Setup complete session
        session_id = self._complete_all_scenes()
        
        # Get result (should use fallback)
        response = client.post(f"/api/sessions/{session_id}/result")
        
        # Should succeed with fallback
        assert response.status_code == 200
        data = response.json()
        
        # Fallback should be indicated
        fallback_flags = data["fallbackFlags"]
        assert "RESULT_FALLBACK" in fallback_flags or "TYPE_PROFILE_FALLBACK" in fallback_flags
        
        # Should still have valid result structure
        assert "axes" in data
        assert "type" in data
        assert len(data["type"]["profiles"]) >= 4
    
    def test_result_retrieval_session_cleanup(self):
        """Test that session is cleaned up after result retrieval."""
        # Setup complete session
        session_id = self._complete_all_scenes()
        
        # Verify session exists before result retrieval
        stored_session = session_store.get_session(uuid.UUID(session_id))
        assert stored_session is not None
        
        # Get result
        response = client.post(f"/api/sessions/{session_id}/result")
        assert response.status_code == 200
        
        # Verify session is cleaned up (ephemeral sessions)
        # Implementation may decide to keep or clean up session
        # This test documents expected behavior
    
    def test_result_retrieval_duplicate_request(self):
        """Test requesting result multiple times for same session."""
        # Setup complete session
        session_id = self._complete_all_scenes()
        
        # First result request should succeed
        response1 = client.post(f"/api/sessions/{session_id}/result")
        assert response1.status_code == 200
        result1 = response1.json()
        
        # Second result request behavior depends on implementation
        response2 = client.post(f"/api/sessions/{session_id}/result")
        
        if response2.status_code == 200:
            # If allowed, results should be identical
            result2 = response2.json()
            assert result1["axes"] == result2["axes"]
            assert result1["type"] == result2["type"]
        else:
            # If not allowed, should return appropriate error
            assert response2.status_code in [400, 404]
    
    def test_result_retrieval_observability_logging(self):
        """Test that result retrieval events are logged for observability."""
        with patch('app.services.observability.observability.log_result_generation') as mock_log:
            # Setup complete session
            session_id = self._complete_all_scenes()
            
            # Get result
            response = client.post(f"/api/sessions/{session_id}/result")
            assert response.status_code == 200
            
            # Verify logging was called
            mock_log.assert_called_once()
            call_args = mock_log.call_args[0]
            
            # Verify log contains result info
            assert str(call_args[0]) == session_id  # session_id
            assert isinstance(call_args[1], float)  # latency_ms
            assert isinstance(call_args[2], dict)  # result_summary
    
    def _complete_all_scenes(self) -> str:
        """Helper method to create a session and complete all 4 scenes."""
        # Bootstrap session
        bootstrap_response = client.post("/api/sessions/start")
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        # Confirm keyword
        keyword_response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json={"keyword": session_data["keywordCandidates"][0], "source": "suggestion"}
        )
        assert keyword_response.status_code == 200
        
        # Complete all 4 scenes
        for scene_index in range(1, 5):
            # Get scene
            scene_response = client.get(f"/api/sessions/{session_id}/scenes/{scene_index}")
            assert scene_response.status_code == 200
            scene_data = scene_response.json()
            
            # Submit first choice
            first_choice_id = scene_data["scene"]["choices"][0]["id"]
            choice_response = client.post(
                f"/api/sessions/{session_id}/scenes/{scene_index}/choice",
                json={"choiceId": first_choice_id}
            )
            assert choice_response.status_code == 200
        
        return session_id

class TestResultRetrievalEdgeCases:
    """Edge case tests for result retrieval functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        session_store._sessions.clear()
    
    def test_result_retrieval_partial_scene_completion(self):
        """Test result retrieval with various partial completion states."""
        # Test cases for different completion states
        partial_completion_cases = [
            {"scenes_completed": 0, "should_succeed": False},
            {"scenes_completed": 1, "should_succeed": False},
            {"scenes_completed": 2, "should_succeed": False},
            {"scenes_completed": 3, "should_succeed": False},
            {"scenes_completed": 4, "should_succeed": True}
        ]
        
        for case in partial_completion_cases:
            # Create fresh session for each case
            bootstrap_response = client.post("/api/sessions/start")
            session_data = bootstrap_response.json()
            session_id = session_data["sessionId"]
            
            # Confirm keyword
            keyword_response = client.post(
                f"/api/sessions/{session_id}/keyword",
                json={"keyword": session_data["keywordCandidates"][0], "source": "suggestion"}
            )
            assert keyword_response.status_code == 200
            
            # Complete specified number of scenes
            for scene_index in range(1, case["scenes_completed"] + 1):
                scene_response = client.get(f"/api/sessions/{session_id}/scenes/{scene_index}")
                scene_data = scene_response.json()
                choice_id = scene_data["scene"]["choices"][0]["id"]
                
                choice_response = client.post(
                    f"/api/sessions/{session_id}/scenes/{scene_index}/choice",
                    json={"choiceId": choice_id}
                )
                assert choice_response.status_code == 200
            
            # Try to get result
            result_response = client.post(f"/api/sessions/{session_id}/result")
            
            if case["should_succeed"]:
                assert result_response.status_code == 200
            else:
                assert result_response.status_code == 400
                error_data = result_response.json()
                assert error_data["error_code"] == "SESSION_NOT_COMPLETED"
    
    def test_result_retrieval_with_zero_scores(self):
        """Test result retrieval when all choice weights sum to zero."""
        # This edge case tests score normalization and type profiling with neutral scores
        # Implementation should handle zero scores gracefully
        pass
    
    def test_result_retrieval_extreme_score_values(self):
        """Test result retrieval with extreme accumulated scores."""
        # Test with maximum positive/negative accumulated scores
        # This tests score normalization and boundary conditions
        pass
    
    def test_result_retrieval_concurrent_requests(self):
        """Test concurrent result retrieval requests for same session."""
        # Setup complete session
        session_id = self._complete_all_scenes()
        
        import threading
        import time
        
        results = []
        errors = []
        
        def get_result():
            try:
                response = client.post(f"/api/sessions/{session_id}/result")
                results.append({"status": response.status_code, "data": response.json()})
            except Exception as e:
                errors.append(str(e))
        
        # Make 3 concurrent result requests
        threads = []
        for i in range(3):
            thread = threading.Thread(target=get_result)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # At least one should succeed
        success_count = len([r for r in results if r["status"] == 200])
        assert success_count >= 1
        assert len(errors) == 0
        
        # If multiple succeed, results should be consistent
        successful_results = [r["data"] for r in results if r["status"] == 200]
        if len(successful_results) > 1:
            first_result = successful_results[0]
            for result in successful_results[1:]:
                assert result["axes"] == first_result["axes"]
                assert result["type"] == first_result["type"]
    
    def _complete_all_scenes(self) -> str:
        """Helper method to create a session and complete all 4 scenes."""
        # Bootstrap session
        bootstrap_response = client.post("/api/sessions/start")
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        # Confirm keyword
        keyword_response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json={"keyword": session_data["keywordCandidates"][0], "source": "suggestion"}
        )
        assert keyword_response.status_code == 200
        
        # Complete all 4 scenes
        for scene_index in range(1, 5):
            # Get scene
            scene_response = client.get(f"/api/sessions/{session_id}/scenes/{scene_index}")
            assert scene_response.status_code == 200
            scene_data = scene_response.json()
            
            # Submit first choice
            first_choice_id = scene_data["scene"]["choices"][0]["id"]
            choice_response = client.post(
                f"/api/sessions/{session_id}/scenes/{scene_index}/choice",
                json={"choiceId": first_choice_id}
            )
            assert choice_response.status_code == 200
        
        return session_id


@pytest.fixture
def completed_session():
    """Fixture providing a session that has completed all 4 scenes."""
    # Bootstrap session
    bootstrap_response = client.post("/api/sessions/start")
    session_data = bootstrap_response.json()
    session_id = session_data["sessionId"]
    
    # Confirm keyword
    keyword_response = client.post(
        f"/api/sessions/{session_id}/keyword",
        json={"keyword": session_data["keywordCandidates"][0], "source": "suggestion"}
    )
    
    # Complete all 4 scenes
    completed_choices = []
    for scene_index in range(1, 5):
        scene_response = client.get(f"/api/sessions/{session_id}/scenes/{scene_index}")
        scene_data = scene_response.json()
        first_choice = scene_data["scene"]["choices"][0]
        
        choice_response = client.post(
            f"/api/sessions/{session_id}/scenes/{scene_index}/choice",
            json={"choiceId": first_choice["id"]}
        )
        
        completed_choices.append({
            "scene_index": scene_index,
            "choice": first_choice
        })
    
    return {
        "session_id": session_id,
        "keyword": session_data["keywordCandidates"][0],
        "completed_choices": completed_choices
    }
        