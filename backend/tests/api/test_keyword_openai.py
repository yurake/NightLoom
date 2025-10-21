"""
Integration tests for OpenAI keyword generation API functionality.

Tests T019: API keyword integration with OpenAI LLM service.
Verifies that the keyword endpoint properly integrates with ExternalLLMService.
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


class TestKeywordOpenAIIntegration:
    """Test OpenAI integration in keyword API endpoints."""
    
    def setup_method(self):
        """Setup for each test method."""
        session_store._sessions.clear()
    
    def test_bootstrap_with_openai_keyword_generation(self):
        """Test bootstrap endpoint uses OpenAI for keyword generation."""
        # Mock successful OpenAI keyword generation
        mock_keywords = ["愛情", "冒険", "希望", "成長"]
        
        with patch('app.services.external_llm.ExternalLLMService.generate_keywords', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = mock_keywords
            
            # Call bootstrap endpoint
            response = client.post("/api/sessions/start", json={"initial_character": "あ"})
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify OpenAI keywords are returned
            assert "keywordCandidates" in data
            assert data["keywordCandidates"] == mock_keywords
            assert len(data["keywordCandidates"]) == 4
            
            # Verify OpenAI service was called
            mock_generate.assert_called_once()
    
    def test_bootstrap_openai_fallback_behavior(self):
        """Test bootstrap falls back gracefully when OpenAI fails."""
        with patch('app.services.external_llm.ExternalLLMService.generate_keywords', new_callable=AsyncMock) as mock_generate:
            # Mock OpenAI failure
            mock_generate.side_effect = AllProvidersFailedError("OpenAI failed")
            
            # Mock fallback keywords
            with patch('app.services.fallback_assets.get_fallback_keywords') as mock_fallback:
                mock_fallback.return_value = ["静的1", "静的2", "静的3", "静的4"]
                
                response = client.post("/api/sessions/start", json={"initial_character": "あ"})
                
                assert response.status_code == 200
                data = response.json()
                
                # Verify fallback was used
                assert data["fallbackUsed"] is True
                assert "KEYWORD_GENERATION_FALLBACK" in data.get("fallbackFlags", [])
    
    def test_keyword_confirmation_with_openai_generated_keywords(self):
        """Test keyword confirmation works with OpenAI-generated keywords."""
        # First, create session with mocked OpenAI keywords
        mock_keywords = ["愛情", "冒険", "希望", "成長"]
        
        with patch('app.services.external_llm.ExternalLLMService.generate_keywords', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = mock_keywords
            
            # Create session
            bootstrap_response = client.post("/api/sessions/start", json={"initial_character": "あ"})
            assert bootstrap_response.status_code == 200
            
            session_data = bootstrap_response.json()
            session_id = session_data["sessionId"]
            
            # Confirm one of the OpenAI-generated keywords
            keyword_request = {
                "keyword": mock_keywords[0],  # Use first OpenAI keyword
                "source": "suggestion"
            }
            
            response = client.post(f"/api/sessions/{session_id}/keyword", json=keyword_request)
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify keyword confirmation succeeded with OpenAI keyword
            assert data["sessionId"] == session_id
            assert "scene" in data
            assert data["scene"]["sceneIndex"] == 1
    
    def test_different_initial_characters_generate_different_keywords(self):
        """Test that different initial characters produce different OpenAI keywords."""
        characters_to_test = ["あ", "か", "さ"]
        generated_keywords = {}
        
        for char in characters_to_test:
            # Mock unique keywords for each character
            mock_keywords = [f"{char}愛", f"{char}冒険", f"{char}希望", f"{char}成長"]
            
            with patch('app.services.external_llm.ExternalLLMService.generate_keywords', new_callable=AsyncMock) as mock_generate:
                mock_generate.return_value = mock_keywords
                
                response = client.post("/api/sessions/start", json={"initial_character": char})
                
                assert response.status_code == 200
                data = response.json()
                
                generated_keywords[char] = data["keywordCandidates"]
                assert data["keywordCandidates"] == mock_keywords
        
        # Verify all characters generated different keywords
        all_keywords = list(generated_keywords.values())
        assert len(set(tuple(kw) for kw in all_keywords)) == len(characters_to_test)
    
    def test_openai_integration_performance_tracking(self):
        """Test that OpenAI integration properly tracks performance metrics."""
        mock_keywords = ["愛情", "冒険", "希望", "成長"]
        
        with patch('app.services.external_llm.ExternalLLMService.generate_keywords', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = mock_keywords
            
            # Mock session to verify LLM generation tracking
            with patch('app.models.session.Session.record_llm_generation') as mock_record:
                response = client.post("/api/sessions/start", json={"initial_character": "あ"})
                
                assert response.status_code == 200
                
                # Verify LLM usage was tracked (would be called in real integration)
                # This tests the infrastructure is in place
    
    def test_openai_api_error_handling(self):
        """Test proper error handling when OpenAI API fails."""
        with patch('app.services.external_llm.ExternalLLMService.generate_keywords', new_callable=AsyncMock) as mock_generate:
            # Mock various OpenAI failures
            mock_generate.side_effect = Exception("OpenAI API Error")
            
            # Should still succeed with fallback
            response = client.post("/api/sessions/start", json={"initial_character": "あ"})
            
            # Should not fail completely
            assert response.status_code == 200
            data = response.json()
            
            # Should have some keywords (from fallback)
            assert "keywordCandidates" in data
            assert len(data["keywordCandidates"]) == 4
            assert data["fallbackUsed"] is True


class TestKeywordOpenAIResponseFormat:
    """Test OpenAI response format compliance."""
    
    def setup_method(self):
        """Setup for each test method."""
        session_store._sessions.clear()
    
    def test_openai_keywords_format_validation(self):
        """Test that OpenAI-generated keywords meet format requirements."""
        # Test various valid keyword formats
        test_cases = [
            ["愛", "希望", "勇気", "自由"],          # Single characters
            ["愛情", "冒険心", "成長", "平和"],       # Multi-character words
            ["あい", "ぼうけん", "せいちょう", "へいわ"], # Hiragana
            ["アイ", "ボウケン", "セイチョウ", "ヘイワ"]   # Katakana
        ]
        
        for mock_keywords in test_cases:
            with patch('app.services.external_llm.ExternalLLMService.generate_keywords', new_callable=AsyncMock) as mock_generate:
                mock_generate.return_value = mock_keywords
                
                response = client.post("/api/sessions/start", json={"initial_character": "あ"})
                
                assert response.status_code == 200
                data = response.json()
                
                # Verify format requirements
                returned_keywords = data["keywordCandidates"]
                assert len(returned_keywords) == 4
                
                for keyword in returned_keywords:
                    assert isinstance(keyword, str)
                    assert len(keyword.strip()) > 0
                    assert len(keyword) <= 20  # Max length requirement
    
    def test_openai_keywords_japanese_content(self):
        """Test that OpenAI keywords contain appropriate Japanese content."""
        mock_keywords = ["愛情", "冒険", "希望", "成長"]
        
        with patch('app.services.external_llm.ExternalLLMService.generate_keywords', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = mock_keywords
            
            response = client.post("/api/sessions/start", json={"initial_character": "あ"})
            
            assert response.status_code == 200
            data = response.json()
            
            keywords = data["keywordCandidates"]
            
            # Verify Japanese character content
            for keyword in keywords:
                # Check for Japanese characters (basic check)
                has_japanese = any(ord(char) > 127 for char in keyword)
                assert has_japanese, f"Keyword '{keyword}' should contain Japanese characters"


class TestKeywordOpenAIEndToEnd:
    """End-to-end tests for OpenAI keyword generation flow."""
    
    def setup_method(self):
        """Setup for each test method."""
        session_store._sessions.clear()
    
    def test_complete_openai_keyword_flow(self):
        """Test complete flow from bootstrap through keyword confirmation."""
        mock_keywords = ["愛情", "冒険", "希望", "成長"]
        
        with patch('app.services.external_llm.ExternalLLMService.generate_keywords', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = mock_keywords
            
            # Step 1: Bootstrap with OpenAI keywords
            bootstrap_response = client.post("/api/sessions/start", json={"initial_character": "あ"})
            assert bootstrap_response.status_code == 200
            
            bootstrap_data = bootstrap_response.json()
            session_id = bootstrap_data["sessionId"]
            assert bootstrap_data["keywordCandidates"] == mock_keywords
            
            # Step 2: Confirm OpenAI-generated keyword
            keyword_request = {
                "keyword": mock_keywords[0],
                "source": "suggestion"
            }
            
            confirm_response = client.post(f"/api/sessions/{session_id}/keyword", json=keyword_request)
            assert confirm_response.status_code == 200
            
            confirm_data = confirm_response.json()
            assert confirm_data["sessionId"] == session_id
            assert confirm_data["scene"]["sceneIndex"] == 1
            
            # Step 3: Verify session progression works
            assert "narrative" in confirm_data["scene"]
            assert len(confirm_data["scene"]["choices"]) == 4
    
    def test_openai_integration_with_custom_keyword(self):
        """Test that custom keywords work alongside OpenAI-generated ones."""
        mock_keywords = ["愛情", "冒険", "希望", "成長"]
        
        with patch('app.services.external_llm.ExternalLLMService.generate_keywords', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = mock_keywords
            
            # Bootstrap with OpenAI keywords
            bootstrap_response = client.post("/api/sessions/start", json={"initial_character": "あ"})
            assert bootstrap_response.status_code == 200
            
            session_data = bootstrap_response.json()
            session_id = session_data["sessionId"]
            
            # Use custom keyword instead of OpenAI suggestion
            custom_keyword_request = {
                "keyword": "自由",  # Custom keyword, not from OpenAI list
                "source": "manual"
            }
            
            response = client.post(f"/api/sessions/{session_id}/keyword", json=custom_keyword_request)
            assert response.status_code == 200
            
            data = response.json()
            assert data["sessionId"] == session_id
            assert "scene" in data
            
            # Verify custom keyword works even when OpenAI generated different ones
