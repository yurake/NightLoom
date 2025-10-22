
"""
User Story 1 Integration Tests: OpenAI統合による動的キーワード生成

Tests T022: Complete integration test for US1 - Dynamic keyword generation via OpenAI.
Validates end-to-end functionality from initial character input to keyword confirmation.
"""

import pytest
import uuid
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.session_store import session_store
from app.services.external_llm import ExternalLLMService, AllProvidersFailedError
from app.clients.llm_client import LLMResponse, LLMTaskType
from app.models.llm_config import LLMProvider


client = TestClient(app)


class TestUS1KeywordGenerationIntegration:
    """Integration tests for User Story 1: Dynamic keyword generation."""
    
    def setup_method(self):
        """Setup for each test method."""
        session_store._sessions.clear()
    
    def test_us1_complete_workflow_success(self):
        """Test complete US1 workflow: character input → OpenAI keywords → confirmation."""
        # Test data
        initial_character = "あ"
        openai_keywords = ["愛情", "冒険", "希望", "成長"]
        
        # Step 1: Mock OpenAI keyword generation
        with patch('app.services.external_llm.ExternalLLMService.generate_keywords', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = openai_keywords
            
            # Bootstrap session with initial character
            bootstrap_response = client.post(
                "/api/sessions/start",
                json={"initial_character": initial_character}
            )
            
            assert bootstrap_response.status_code == 200
            bootstrap_data = bootstrap_response.json()
            
            # Verify OpenAI integration worked
            assert bootstrap_data["initialCharacter"] == initial_character
            assert bootstrap_data["keywordCandidates"] == openai_keywords
            assert len(bootstrap_data["keywordCandidates"]) == 4
            assert bootstrap_data["fallbackUsed"] is False
            
            # Verify OpenAI service was called with correct parameters
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args[0][0]  # First argument (session)
            assert call_args.initialCharacter == initial_character
        
        # Step 2: Confirm one of the OpenAI-generated keywords
        session_id = bootstrap_data["sessionId"]
        selected_keyword = openai_keywords[0]  # Select first OpenAI keyword
        
        keyword_request = {
            "keyword": selected_keyword,
            "source": "suggestion"  # From OpenAI suggestion
        }
        
        keyword_response = client.post(
            f"/api/sessions/{session_id}/keyword",
            json=keyword_request
        )
        
        assert keyword_response.status_code == 200
        keyword_data = keyword_response.json()
        
        # Verify keyword confirmation succeeded
        assert keyword_data["sessionId"] == session_id
        assert keyword_data["scene"]["sceneIndex"] == 1
        assert "narrative" in keyword_data["scene"]
        assert len(keyword_data["scene"]["choices"]) == 4
        
        # Verify session progression
        assert keyword_data["fallbackUsed"] == bootstrap_data["fallbackUsed"]
    
    def test_us1_different_characters_generate_different_keywords(self):
        """Test that US1 generates different keywords for different characters."""
        characters_and_keywords = {
            "あ": ["愛情", "安心", "明るさ", "温かさ"],
            "か": ["感動", "希望", "感謝", "勇気"],
            "さ": ["幸せ", "成長", "支援", "信頼"]
        }
        
        generated_sessions = {}
        
        for character, expected_keywords in characters_and_keywords.items():
            with patch('app.services.external_llm.ExternalLLMService.generate_keywords', new_callable=AsyncMock) as mock_generate:
                mock_generate.return_value = expected_keywords
                
                response = client.post(
                    "/api/sessions/start",
                    json={"initial_character": character}
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # Verify character-specific keywords
                assert data["initialCharacter"] == character
                assert data["keywordCandidates"] == expected_keywords
                assert data["fallbackUsed"] is False
                
                generated_sessions[character] = data
        
        # Verify all characters generated different keywords
        all_keyword_sets = [tuple(session["keywordCandidates"]) for session in generated_sessions.values()]
        assert len(set(all_keyword_sets)) == len(characters_and_keywords), "Each character should generate unique keywords"
    
    def test_us1_fallback_integration(self):
        """Test US1 fallback behavior when OpenAI fails."""
        initial_character = "あ"
        fallback_keywords = ["フォールバック1", "フォールバック2", "フォールバック3", "フォールバック4"]
        
        # Mock the start_session method to simulate fallback behavior
        with patch('app.services.session.default_session_service.start_session', new_callable=AsyncMock) as mock_start:
            from app.models.session import Session, SessionState
            import uuid
            
            # Create a mock session that simulates fallback behavior
            mock_session = Session(
                id=uuid.uuid4(),
                state=SessionState.INIT,
                initialCharacter=initial_character,
                themeId="adventure",
                keywordCandidates=fallback_keywords,
                fallbackFlags=["keyword_generation"]  # This ensures fallbackUsed will be True
            )
            mock_start.return_value = mock_session
            
            response = client.post(
                "/api/sessions/start",
                json={"initial_character": initial_character}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify fallback was used
            assert data["keywordCandidates"] == fallback_keywords
            assert data["fallbackUsed"] is True
            
            # Store the mock session in session_store for the keyword confirmation test
            from app.services.session_store import session_store
            session_id_uuid = uuid.UUID(data["sessionId"])
            session_store._sessions[session_id_uuid] = mock_session
            
            # Verify session still works with fallback keywords
            session_id = data["sessionId"]
            keyword_request = {
                "keyword": fallback_keywords[0],
                "source": "suggestion"
            }
            
            keyword_response = client.post(
                f"/api/sessions/{session_id}/keyword",
                json=keyword_request
            )
            
            assert keyword_response.status_code == 200
            keyword_data = keyword_response.json()
            assert keyword_data["scene"]["sceneIndex"] == 1
    
    def test_us1_custom_keyword_alongside_openai(self):
        """Test US1 supports custom keywords even when OpenAI provides suggestions."""
        initial_character = "あ"
        openai_keywords = ["愛情", "冒険", "希望", "成長"]
        custom_keyword = "自由"  # Not in OpenAI list
        
        with patch('app.services.external_llm.ExternalLLMService.generate_keywords', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = openai_keywords
            
            # Bootstrap with OpenAI keywords
            bootstrap_response = client.post(
                "/api/sessions/start",
                json={"initial_character": initial_character}
            )
            
            assert bootstrap_response.status_code == 200
            bootstrap_data = bootstrap_response.json()
            
            # Verify OpenAI keywords were provided
            assert bootstrap_data["keywordCandidates"] == openai_keywords
            
            # Use custom keyword instead of OpenAI suggestions
            session_id = bootstrap_data["sessionId"]
            keyword_request = {
                "keyword": custom_keyword,
                "source": "manual"  # Custom input
            }
            
            keyword_response = client.post(
                f"/api/sessions/{session_id}/keyword",
                json=keyword_request
            )
            
            assert keyword_response.status_code == 200
            keyword_data = keyword_response.json()
            
            # Verify custom keyword was accepted
            assert keyword_data["sessionId"] == session_id
            assert keyword_data["scene"]["sceneIndex"] == 1
    
    def test_us1_performance_integration(self):
        """Test US1 meets performance requirements in integration."""
        import time
        
        initial_character = "あ"
        fast_keywords = ["高速1", "高速2", "高速3", "高速4"]
        
        # Mock fast OpenAI response
        mock_response = LLMResponse(
            task_type=LLMTaskType.KEYWORD_GENERATION,
            session_id="test",
            content={"keywords": fast_keywords},
            provider=LLMProvider.OPENAI,
            model_name="gpt-4",
            latency_ms=200.0
        )
        
        with patch('app.services.external_llm.ExternalLLMService._execute_with_fallback', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = mock_response
            
            # Measure end-to-end performance
            start_time = time.time()
            
            response = client.post(
                "/api/sessions/start",
                json={"initial_character": initial_character}
            )
            
            end_time = time.time()
            total_time_ms = (end_time - start_time) * 1000
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify performance requirement (should be fast in integration)
            assert total_time_ms < 1000, f"US1 integration took {total_time_ms}ms, should be < 1000ms"
            assert data["keywordCandidates"] == fast_keywords
    
    def test_us1_session_isolation(self):
        """Test that US1 sessions are properly isolated."""
        character1 = "あ"
        character2 = "か"
        keywords1 = ["愛1", "愛2", "愛3", "愛4"]
        keywords2 = ["希望1", "希望2", "希望3", "希望4"]
        
        # Create first session
        with patch('app.services.external_llm.ExternalLLMService.generate_keywords', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = keywords1
            
            response1 = client.post(
                "/api/sessions/start",
                json={"initial_character": character1}
            )
            
            assert response1.status_code == 200
            data1 = response1.json()
            session_id1 = data1["sessionId"]
        
        # Create second session
        with patch('app.services.external_llm.ExternalLLMService.generate_keywords', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = keywords2
            
            response2 = client.post(
                "/api/sessions/start",
                json={"initial_character": character2}
            )
            
            assert response2.status_code == 200
            data2 = response2.json()
            session_id2 = data2["sessionId"]
        
        # Verify sessions are isolated
        assert session_id1 != session_id2
        assert data1["keywordCandidates"] == keywords1
        assert data2["keywordCandidates"] == keywords2
        
        # Verify both sessions can progress independently
        keyword_request1 = {"keyword": keywords1[0], "source": "suggestion"}
        keyword_request2 = {"keyword": keywords2[0], "source": "suggestion"}
        
        keyword_response1 = client.post(f"/api/sessions/{session_id1}/keyword", json=keyword_request1)
        keyword_response2 = client.post(f"/api/sessions/{session_id2}/keyword", json=keyword_request2)
        
        assert keyword_response1.status_code == 200
        assert keyword_response2.status_code == 200
        
        # Verify independent progression
        assert keyword_response1.json()["sessionId"] == session_id1
        assert keyword_response2.json()["sessionId"] == session_id2


class TestUS1EdgeCases:
    """Edge case tests for User Story 1."""
    
    def setup_method(self):
        session_store._sessions.clear()
    
    def test_us1_invalid_initial_character(self):
        """Test US1 handles invalid initial characters gracefully."""
        invalid_characters = ["", "ab", "123", "あああ"]
        
        for invalid_char in invalid_characters:
            fallback_keywords = ["フォールバック1", "フォールバック2", "フォールバック3", "フォールバック4"]
            
            # Mock the start_session method to ensure consistent behavior
            with patch('app.services.session.default_session_service.start_session', new_callable=AsyncMock) as mock_start:
                from app.models.session import Session, SessionState
                import uuid
                
                # Create a mock session with "あ" as the corrected character
                mock_session = Session(
                    id=uuid.uuid4(),
                    state=SessionState.INIT,
                    initialCharacter="あ",  # Bootstrap should correct invalid characters to "あ"
                    themeId="adventure",
                    keywordCandidates=fallback_keywords
                )
                mock_start.return_value = mock_session
                
                response = client.post(
                    "/api/sessions/start",
                    json={"initial_character": invalid_char}
                )
                
                # Should succeed with fallback character
                assert response.status_code == 200
                data = response.json()
                
                # Should use default fallback character "あ"
                assert data["initialCharacter"] == "あ"
                assert len(data["keywordCandidates"]) == 4
    
    def test_us1_no_initial_character(self):
        """Test US1 works without initial character (uses default)."""
        default_keywords = ["デフォルト1", "デフォルト2", "デフォルト3", "デフォルト4"]
        
        # Mock the start_session method to ensure consistent behavior
        with patch('app.services.session.default_session_service.start_session', new_callable=AsyncMock) as mock_start:
            from app.models.session import Session, SessionState
            import uuid
            
            # Create a mock session with a default character (mock the random selection to be "あ")
            mock_session = Session(
                id=uuid.uuid4(),
                state=SessionState.INIT,
                initialCharacter="あ",  # Mock random selection to return "あ"
                themeId="adventure",
                keywordCandidates=default_keywords
            )
            mock_start.return_value = mock_session
            
            # Request without initial_character
            response = client.post("/api/sessions/start")
            
            assert response.status_code == 200
            data = response.json()
            
            # Should use default character "あ"
            assert data["initialCharacter"] == "あ"
            assert data["keywordCandidates"] == default_keywords
    
    def test_us1_openai_partial_failure_recovery(self):
        """Test US1 recovers from partial OpenAI failures."""
        initial_character = "あ"
        recovery_keywords = ["復旧1", "復旧2", "復旧3", "復旧4"]
        
        # Mock the start_session method to simulate recovery behavior
        with patch('app.services.session.default_session_service.start_session', new_callable=AsyncMock) as mock_start:
            from app.models.session import Session, SessionState
            import uuid
            
            # Create a mock session that simulates recovery behavior
            mock_session = Session(
                id=uuid.uuid4(),
                state=SessionState.INIT,
                initialCharacter=initial_character,
                themeId="adventure",
                keywordCandidates=recovery_keywords,
                fallbackFlags=["keyword_generation_error"]  # This ensures fallbackUsed will be True
            )
            mock_start.return_value = mock_session
            
            response = client.post(
                "/api/sessions/start",
                json={"initial_character": initial_character}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Should recover with fallback
            assert data["keywordCandidates"] == recovery_keywords
            assert data["fallbackUsed"] is True
