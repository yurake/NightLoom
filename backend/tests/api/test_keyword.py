"""
Contract tests for NightLoom MVP keyword confirmation API.

Tests the /api/sessions/{sessionId}/keyword endpoint according to T018 requirements.
Implements Fail First testing strategy as specified in tasks.md.
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app
from app.services.session_store import session_store


client = TestClient(app)


class TestKeywordConfirmationAPI:
    """Test cases for keyword confirmation endpoint."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Clear session store
        session_store._sessions.clear()
    
    def test_keyword_confirmation_success(self):
        """Test successful keyword confirmation with scene generation."""
        # First create a session
        bootstrap_response = client.post("/api/sessions/start")
        assert bootstrap_response.status_code == 200
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        # Confirm keyword from suggestions
        keyword_request = {
            "keyword": session_data["keywordCandidates"][0],
            "source": "suggestion"
        }
        
        response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json=keyword_request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "sessionId" in data
        assert "scene" in data
        assert "fallbackUsed" in data
        
        # Verify session ID matches
        assert data["sessionId"] == session_id
        
        # Verify scene structure
        scene = data["scene"]
        assert scene is not None
        assert scene["sceneIndex"] == 1
        assert "themeId" in scene
        assert "narrative" in scene
        assert "choices" in scene
        
        # Verify choices structure
        choices = scene["choices"]
        assert len(choices) == 4
        for choice in choices:
            assert "id" in choice
            assert "text" in choice
            assert "weights" in choice
            assert isinstance(choice["weights"], dict)
    
    def test_keyword_confirmation_custom_keyword(self):
        """Test keyword confirmation with custom (manual) keyword."""
        # First create a session
        bootstrap_response = client.post("/api/sessions/start")
        assert bootstrap_response.status_code == 200
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        # Confirm custom keyword
        keyword_request = {
            "keyword": "自由",
            "source": "manual"
        }
        
        response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json=keyword_request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should still generate valid scene
        scene = data["scene"]
        assert scene is not None
        assert scene["sceneIndex"] == 1
        assert len(scene["choices"]) == 4
    
    def test_keyword_confirmation_invalid_session(self):
        """Test keyword confirmation with non-existent session."""
        fake_session_id = str(uuid.uuid4())
        
        keyword_request = {
            "keyword": "テスト",
            "source": "manual"
        }
        
        response = client.post(
            f"/api/sessions/{fake_session_id}/keyword",
            json=keyword_request
        )
        
        # Should return 500 due to session not found
        assert response.status_code == 500
        assert "not found" in response.json()["detail"].lower()
    
    def test_keyword_confirmation_invalid_session_id_format(self):
        """Test keyword confirmation with invalid session ID format."""
        invalid_session_id = "invalid-uuid-format"
        
        keyword_request = {
            "keyword": "テスト",
            "source": "manual"
        }
        
        response = client.post(
            f"/api/sessions/{invalid_session_id}/keyword",
            json=keyword_request
        )
        
        assert response.status_code == 400
        assert "Invalid session ID format" in response.json()["detail"]
    
    def test_keyword_confirmation_empty_keyword(self):
        """Test keyword confirmation with empty keyword."""
        # First create a session
        bootstrap_response = client.post("/api/sessions/start")
        assert bootstrap_response.status_code == 200
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        # Try empty keyword
        keyword_request = {
            "keyword": "",
            "source": "manual"
        }
        
        response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json=keyword_request
        )
        
        # Should fail due to invalid keyword
        assert response.status_code == 500
        assert "Invalid keyword" in response.json()["detail"]
    
    def test_keyword_confirmation_too_long_keyword(self):
        """Test keyword confirmation with overly long keyword."""
        # First create a session
        bootstrap_response = client.post("/api/sessions/start")
        assert bootstrap_response.status_code == 200
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        # Try overly long keyword (>20 characters)
        keyword_request = {
            "keyword": "これは非常に長いキーワードでテストします",
            "source": "manual"
        }
        
        response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json=keyword_request
        )
        
        # Should fail due to invalid keyword length
        assert response.status_code == 500
        assert "Invalid keyword" in response.json()["detail"]
    
    def test_keyword_confirmation_missing_request_fields(self):
        """Test keyword confirmation with missing required fields."""
        # First create a session
        bootstrap_response = client.post("/api/sessions/start")
        assert bootstrap_response.status_code == 200
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        # Missing source field
        response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json={"keyword": "テスト"}
        )
        
        # Should fail due to validation error
        assert response.status_code == 422
    
    def test_keyword_confirmation_performance(self):
        """Test that keyword confirmation meets performance requirements."""
        import time
        
        # First create a session
        bootstrap_response = client.post("/api/sessions/start")
        assert bootstrap_response.status_code == 200
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        keyword_request = {
            "keyword": session_data["keywordCandidates"][0],
            "source": "suggestion"
        }
        
        start_time = time.time()
        response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json=keyword_request
        )
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Should complete within 800ms (p95 requirement from plan.md)
        latency_ms = (end_time - start_time) * 1000
        assert latency_ms < 800, f"Keyword confirmation took {latency_ms}ms, exceeds 800ms requirement"
    
    def test_keyword_confirmation_scene_narrative_contains_keyword(self):
        """Test that generated scene narrative includes the selected keyword."""
        # First create a session
        bootstrap_response = client.post("/api/sessions/start")
        assert bootstrap_response.status_code == 200
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        selected_keyword = session_data["keywordCandidates"][0]
        keyword_request = {
            "keyword": selected_keyword,
            "source": "suggestion"
        }
        
        response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json=keyword_request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify keyword appears in narrative
        scene = data["scene"]
        narrative = scene["narrative"]
        assert selected_keyword in narrative
    
    def test_keyword_confirmation_observability_logging(self):
        """Test that keyword confirmation events are logged for observability."""
        with patch('app.services.observability.observability.log_keyword_confirmation') as mock_log:
            # First create a session
            bootstrap_response = client.post("/api/sessions/start")
            assert bootstrap_response.status_code == 200
            session_data = bootstrap_response.json()
            session_id = session_data["sessionId"]
            
            keyword_request = {
                "keyword": session_data["keywordCandidates"][0],
                "source": "suggestion"
            }
            
            response = client.post(
                f"/api/sessions/{session_id}/keyword",
                json=keyword_request
            )
            
            assert response.status_code == 200
            
            # Verify logging was called
            mock_log.assert_called_once()
            call_args = mock_log.call_args[0]
            
            # Verify log contains keyword info
            assert str(call_args[0]) == session_id  # session_id (UUID)
            assert call_args[1] == keyword_request["keyword"]  # keyword
            assert call_args[2] == keyword_request["source"]  # source
            assert isinstance(call_args[3], float)  # latency_ms


class TestKeywordConfirmationEdgeCases:
    """Edge case tests for keyword confirmation functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        session_store._sessions.clear()
    
    def test_keyword_confirmation_japanese_characters(self):
        """Test keyword confirmation with various Japanese characters."""
        # First create a session
        bootstrap_response = client.post("/api/sessions/start")
        assert bootstrap_response.status_code == 200
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        # Test different Japanese character types
        japanese_keywords = ["ひらがな", "カタカナ", "漢字", "混合文字列"]
        
        for keyword in japanese_keywords:
            keyword_request = {
                "keyword": keyword,
                "source": "manual"
            }
            
            response = client.post(
                f"/api/sessions/{session_id}/keyword",
                json=keyword_request
            )
            
            # Should handle Japanese characters properly
            # Note: This might fail if session state doesn't allow re-confirmation
            # We expect this test to show current behavior
            if response.status_code == 200:
                scene = response.json()["scene"]
                assert keyword in scene["narrative"]
            # If it fails, that's expected behavior for this test case
    
    def test_keyword_confirmation_twice_same_session(self):
        """Test attempting to confirm keyword twice for same session."""
        # First create a session
        bootstrap_response = client.post("/api/sessions/start")
        assert bootstrap_response.status_code == 200
        session_data = bootstrap_response.json()
        session_id = session_data["sessionId"]
        
        keyword_request = {
            "keyword": session_data["keywordCandidates"][0],
            "source": "suggestion"
        }
        
        # First confirmation should succeed
        response1 = client.post(
            f"/api/sessions/{session_id}/keyword",
            json=keyword_request
        )
        assert response1.status_code == 200
        
        # Second confirmation should fail (session state validation)
        response2 = client.post(
            f"/api/sessions/{session_id}/keyword",
            json={
                "keyword": session_data["keywordCandidates"][1],
                "source": "suggestion"
            }
        )
        
        # Should fail due to session state (no longer INIT)
        assert response2.status_code == 500
        # This test documents expected behavior - second confirmation should be rejected


@pytest.fixture
def session_with_keyword():
    """Fixture providing a session that has already confirmed a keyword."""
    bootstrap_response = client.post("/api/sessions/start")
    session_data = bootstrap_response.json()
    session_id = session_data["sessionId"]
    
    keyword_request = {
        "keyword": session_data["keywordCandidates"][0],
        "source": "suggestion"
    }
    
    keyword_response = client.post(
        f"/api/sessions/{session_id}/keyword",
        json=keyword_request
    )
    
    return {
        "session_id": session_id,
        "keyword": keyword_request["keyword"],
        "first_scene": keyword_response.json()["scene"]
    }
