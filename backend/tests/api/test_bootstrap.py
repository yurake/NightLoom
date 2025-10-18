"""
Integration tests for NightLoom MVP bootstrap API.

Tests the /api/sessions/start endpoint and initial session creation flow.
Implements Fail First testing strategy as specified in tasks.md.
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app
from app.services.session_store import session_store
from app.clients.llm import MockLLMService


client = TestClient(app)


class TestBootstrapAPI:
    """Test cases for session bootstrap endpoint."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Clear session store
        session_store._sessions.clear()
    
    def test_bootstrap_success(self):
        """Test successful session bootstrap."""
        response = client.post("/api/sessions/start")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "sessionId" in data
        assert "axes" in data
        assert "keywordCandidates" in data
        assert "initialCharacter" in data
        assert "themeId" in data
        assert "fallbackUsed" in data
        
        # Verify session ID format
        session_id = data["sessionId"]
        assert uuid.UUID(session_id)  # Should not raise exception
        
        # Verify axes structure
        axes = data["axes"]
        assert len(axes) >= 2
        for axis in axes:
            assert "id" in axis
            assert "name" in axis
            assert "description" in axis
            assert "direction" in axis
        
        # Verify keyword candidates
        keywords = data["keywordCandidates"]
        assert len(keywords) == 4
        for keyword in keywords:
            assert isinstance(keyword, str)
            assert len(keyword) >= 1
        
        # Verify initial character
        initial_char = data["initialCharacter"]
        assert isinstance(initial_char, str)
        assert len(initial_char) == 1
        
        # Verify theme ID
        theme_id = data["themeId"]
        assert isinstance(theme_id, str)
        assert len(theme_id) > 0
    
    def test_bootstrap_with_custom_character(self):
        """Test bootstrap with custom initial character."""
        response = client.post("/api/sessions/start", json={"initial_character": "か"})
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["initialCharacter"] == "か"
        # Keywords should be different for different characters
        keywords = data["keywordCandidates"]
        assert len(keywords) == 4
    
    @patch('app.api.bootstrap.default_session_service')
    def test_bootstrap_with_llm_fallback(self, mock_session_service):
        """Test bootstrap when LLM service fails and fallback is used."""
        # Import needed classes
        from app.models.session import Session, SessionState
        from app.services.fallback_assets import get_fallback_axes
        from datetime import datetime, timezone
        import uuid
        
        # Create a mock session with fallback flag set
        mock_session = Session(
            id=uuid.uuid4(),
            state=SessionState.INIT,
            initialCharacter="あ",
            keywordCandidates=["希望", "挑戦", "成長", "発見"],
            themeId="fallback",
            axes=get_fallback_axes(),  # Need axes for response
            fallbackFlags=["BOOTSTRAP_FALLBACK"],  # This should make fallbackUsed=True
            createdAt=datetime.now(timezone.utc)
        )
        
        # Mock the start_session method
        mock_session_service.start_session = AsyncMock(return_value=mock_session)
        
        response = client.post("/api/sessions/start")
        
        # Should still succeed due to fallback
        assert response.status_code == 200
        data = response.json()
        
        # Fallback should be indicated
        assert data["fallbackUsed"] is True
        
        # Should still have valid data structure
        assert len(data["keywordCandidates"]) == 4
        assert data["themeId"] == "fallback"
        assert len(data["axes"]) >= 2
    
    def test_bootstrap_multiple_sessions(self):
        """Test creating multiple concurrent sessions."""
        responses = []
        session_ids = set()
        
        # Create 3 sessions
        for i in range(3):
            response = client.post("/api/sessions/start")
            assert response.status_code == 200
            
            data = response.json()
            session_id = data["sessionId"]
            
            # Each session should have unique ID
            assert session_id not in session_ids
            session_ids.add(session_id)
            
            responses.append(data)
        
        # Verify each session has different content (due to randomization)
        assert len(set(r["sessionId"] for r in responses)) == 3
    
    def test_bootstrap_response_performance(self):
        """Test that bootstrap response meets performance requirements."""
        import time
        
        start_time = time.time()
        response = client.post("/api/sessions/start")
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Should complete within 800ms (p95 requirement from plan.md)
        latency_ms = (end_time - start_time) * 1000
        assert latency_ms < 800, f"Bootstrap took {latency_ms}ms, exceeds 800ms requirement"
    
    def test_bootstrap_session_storage(self):
        """Test that session is properly stored after bootstrap."""
        response = client.post("/api/sessions/start")
        
        assert response.status_code == 200
        data = response.json()
        session_id = uuid.UUID(data["sessionId"])
        
        # Verify session is stored
        stored_session = session_store.get_session(session_id)
        assert stored_session is not None
        assert stored_session.state.value == "INIT"
        assert stored_session.initialCharacter == data["initialCharacter"]
        assert stored_session.keywordCandidates == data["keywordCandidates"]
        assert stored_session.themeId == data["themeId"]
    
    def test_bootstrap_invalid_request_body(self):
        """Test bootstrap with invalid request body."""
        # Invalid initial character (too long)
        response = client.post("/api/sessions/start", json={"initial_character": "invalid"})
        
        # Should either reject or use fallback
        # Exact behavior depends on validation implementation
        assert response.status_code in [200, 400]
        
        if response.status_code == 200:
            # If accepted, should use fallback character
            data = response.json()
            assert len(data["initialCharacter"]) == 1
    
    def test_bootstrap_observability_logging(self):
        """Test that bootstrap events are logged for observability."""
        with patch('app.services.observability.observability.log_session_start') as mock_log:
            response = client.post("/api/sessions/start")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify logging was called
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            
            # Verify log contains session info
            assert str(call_args[0][0]) == data["sessionId"]  # session_id
            assert call_args[0][1] == data["initialCharacter"]  # initial_character
            assert call_args[0][2] == data["themeId"]  # theme_id


class TestBootstrapEdgeCases:
    """Edge case tests for bootstrap functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        session_store._sessions.clear()
    
    def test_bootstrap_with_empty_body(self):
        """Test bootstrap with empty request body."""
        response = client.post("/api/sessions/start", json={})
        
        assert response.status_code == 200
        data = response.json()
        
        # Should use default initial character
        assert data["initialCharacter"] in ["あ", "か", "さ", "た", "な"]  # Common defaults
    
    def test_bootstrap_concurrent_requests(self):
        """Test handling of concurrent bootstrap requests."""
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request():
            try:
                response = client.post("/api/sessions/start")
                if response.status_code == 200:
                    results.append(response.json())
                else:
                    errors.append(f"Status {response.status_code}")
            except Exception as e:
                errors.append(str(e))
        
        # Create 5 concurrent requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests succeeded
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        
        # Verify all session IDs are unique
        session_ids = [r["sessionId"] for r in results]
        assert len(set(session_ids)) == 5
    
    def test_bootstrap_memory_usage(self):
        """Test that bootstrap doesn't cause memory leaks."""
        import gc
        
        initial_sessions = session_store.count_sessions()
        
        # Create many sessions to test memory handling
        for i in range(10):
            response = client.post("/api/sessions/start")
            assert response.status_code == 200
        
        # Force garbage collection
        gc.collect()
        
        # Verify sessions are properly stored
        final_sessions = session_store.count_sessions()
        assert final_sessions == initial_sessions + 10


@pytest.fixture
def mock_llm_service():
    """Fixture providing a mock LLM service."""
    return MockLLMService(simulate_failures=False)


@pytest.fixture
def failing_llm_service():
    """Fixture providing a failing LLM service for fallback testing."""
    return MockLLMService(simulate_failures=True)
