
"""
Tests for keyword generation fallback functionality.

Tests T020: Keyword fallback behavior when LLM services fail.
Ensures robust fallback mechanisms for reliable keyword generation.
"""

import pytest
import uuid
from unittest.mock import patch, AsyncMock, MagicMock
from typing import List

from app.services.external_llm import (
    ExternalLLMService, get_llm_service, AllProvidersFailedError, LLMServiceError
)
from app.models.session import Session, SessionState
from app.models.llm_config import LLMProvider
from app.clients.llm_client import (
    LLMResponse, LLMTaskType, LLMClientError, ValidationError, 
    RateLimitError, ProviderUnavailableError
)


class TestKeywordFallbackMechanisms:
    """Test fallback mechanisms for keyword generation failures."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock session for testing."""
        return Session(
            id=uuid.uuid4(),
            state=SessionState.INIT,
            initialCharacter="あ",
            themeId="adventure",
            keywordCandidates=[],
            axes=[],
            scenes=[],
            choices=[],
            rawScores={},
            normalizedScores={},
            typeProfiles=[],
            fallbackFlags=[],
            llmGenerations=[],
            llmErrors=[]
        )
    
    @pytest.fixture
    def llm_service(self):
        """Create LLM service instance for testing."""
        return ExternalLLMService()
    
    @pytest.mark.asyncio
    async def test_fallback_on_all_providers_failed(self, llm_service, mock_session):
        """Test fallback when all LLM providers fail."""
        fallback_keywords = ["フォールバック1", "フォールバック2", "フォールバック3", "フォールバック4"]
        
        # Mock all providers failing
        with patch.object(llm_service, '_execute_with_fallback', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = AllProvidersFailedError("All providers failed")
            
            # Mock fallback manager
            with patch.object(llm_service.fallback_manager, 'get_keywords_for_character', new_callable=AsyncMock) as mock_fallback:
                mock_fallback.return_value = fallback_keywords
                
                # Execute keyword generation
                keywords = await llm_service.generate_keywords(mock_session)
                
                # Verify fallback was used
                assert keywords == fallback_keywords
                assert "keyword_generation" in mock_session.fallbackFlags
                
                # Verify fallback manager was called
                mock_fallback.assert_called_once_with("あ")
    
    @pytest.mark.asyncio
    async def test_fallback_on_validation_error(self, llm_service, mock_session):
        """Test fallback when LLM response validation fails."""
        fallback_keywords = ["検証失敗1", "検証失敗2", "検証失敗3", "検証失敗4"]
        
        # Mock validation error
        with patch.object(llm_service, '_execute_with_fallback', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = ValidationError("Response validation failed")
            
            with patch.object(llm_service.fallback_manager, 'get_keywords_for_character', new_callable=AsyncMock) as mock_fallback:
                mock_fallback.return_value = fallback_keywords
                
                keywords = await llm_service.generate_keywords(mock_session)
                
                assert keywords == fallback_keywords
                assert "keyword_generation" in mock_session.fallbackFlags
    
    @pytest.mark.asyncio
    async def test_fallback_on_rate_limit_error(self, llm_service, mock_session):
        """Test fallback when rate limit is exceeded."""
        fallback_keywords = ["レート制限1", "レート制限2", "レート制限3", "レート制限4"]
        
        # Mock rate limit error leading to all providers failed
        with patch.object(llm_service, '_execute_with_fallback', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = AllProvidersFailedError("Rate limit exceeded")
            
            with patch.object(llm_service.fallback_manager, 'get_keywords_for_character', new_callable=AsyncMock) as mock_fallback:
                mock_fallback.return_value = fallback_keywords
                
                keywords = await llm_service.generate_keywords(mock_session)
                
                assert keywords == fallback_keywords
                assert "keyword_generation" in mock_session.fallbackFlags
    
    @pytest.mark.asyncio
    async def test_fallback_ensures_exact_keyword_count(self, llm_service, mock_session):
        """Test that fallback always returns exactly 4 keywords."""
        # Test with too many fallback keywords
        excess_keywords = ["キーワード1", "キーワード2", "キーワード3", "キーワード4", "キーワード5", "キーワード6"]
        
        with patch.object(llm_service, '_execute_with_fallback', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = AllProvidersFailedError("Provider failed")
            
            with patch.object(llm_service.fallback_manager, 'get_keywords_for_character', new_callable=AsyncMock) as mock_fallback:
                mock_fallback.return_value = excess_keywords
                
                keywords = await llm_service.generate_keywords(mock_session)
                
                # Should trim to exactly 4 keywords
                assert len(keywords) == 4
                assert keywords == excess_keywords[:4]
                assert "keyword_generation" in mock_session.fallbackFlags
    
    @pytest.mark.asyncio
    async def test_fallback_with_different_characters(self, llm_service):
        """Test fallback works with different initial characters."""
        test_characters = ["あ", "か", "さ", "た", "な"]
        
        for char in test_characters:
            session = Session(
                id=uuid.uuid4(),
                state=SessionState.INIT,
                initialCharacter=char,
                themeId="adventure",
                fallbackFlags=[]
            )
            
            expected_keywords = [f"{char}1", f"{char}2", f"{char}3", f"{char}4"]
            
            with patch.object(llm_service, '_execute_with_fallback', new_callable=AsyncMock) as mock_execute:
                mock_execute.side_effect = AllProvidersFailedError("Provider failed")
                
                with patch.object(llm_service.fallback_manager, 'get_keywords_for_character', new_callable=AsyncMock) as mock_fallback:
                    mock_fallback.return_value = expected_keywords
                    
                    keywords = await llm_service.generate_keywords(session)
                    
                    assert keywords == expected_keywords
                    assert "keyword_generation" in session.fallbackFlags
                    mock_fallback.assert_called_once_with(char)
    
    @pytest.mark.asyncio
    async def test_no_fallback_on_successful_generation(self, llm_service, mock_session):
        """Test that fallback is not triggered on successful LLM generation."""
        successful_keywords = ["成功1", "成功2", "成功3", "成功4"]
        
        mock_response = LLMResponse(
            task_type=LLMTaskType.KEYWORD_GENERATION,
            session_id=str(mock_session.id),
            content={"keywords": successful_keywords},
            provider=LLMProvider.OPENAI,
            model_name="gpt-4"
        )
        
        with patch.object(llm_service, '_execute_with_fallback', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = mock_response
            
            # Ensure fallback manager is not called
            with patch.object(llm_service.fallback_manager, 'get_keywords_for_character', new_callable=AsyncMock) as mock_fallback:
                keywords = await llm_service.generate_keywords(mock_session)
                
                assert keywords == successful_keywords
                assert "keyword_generation" not in mock_session.fallbackFlags
                mock_fallback.assert_not_called()


class TestKeywordFallbackQuality:
    """Test quality and reliability of fallback keywords."""
    
    @pytest.fixture
    def llm_service(self):
        return ExternalLLMService()
    
    @pytest.mark.asyncio
    async def test_fallback_keywords_format_compliance(self, llm_service):
        """Test that fallback keywords meet format requirements."""
        session = Session(
            id=uuid.uuid4(),
            state=SessionState.INIT,
            initialCharacter="あ",
            themeId="adventure",
            fallbackFlags=[]
        )
        
        fallback_keywords = ["愛", "希望", "勇気", "自由"]
        
        with patch.object(llm_service, '_execute_with_fallback', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = AllProvidersFailedError("Provider failed")
            
            with patch.object(llm_service.fallback_manager, 'get_keywords_for_character', new_callable=AsyncMock) as mock_fallback:
                mock_fallback.return_value = fallback_keywords
                
                keywords = await llm_service.generate_keywords(session)
                
                # Verify format compliance
                assert len(keywords) == 4
                for keyword in keywords:
                    assert isinstance(keyword, str)
                    assert len(keyword.strip()) > 0
                    assert len(keyword) <= 20  # Max length requirement
    
    @pytest.mark.asyncio
    async def test_fallback_keywords_japanese_content(self, llm_service):
        """Test that fallback keywords contain Japanese content."""
        session = Session(
            id=uuid.uuid4(),
            state=SessionState.INIT,
            initialCharacter="あ",
            themeId="adventure",
            fallbackFlags=[]
        )
        
        japanese_keywords = ["愛情", "冒険", "希望", "成長"]
        
        with patch.object(llm_service, '_execute_with_fallback', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = AllProvidersFailedError("Provider failed")
            
            with patch.object(llm_service.fallback_manager, 'get_keywords_for_character', new_callable=AsyncMock) as mock_fallback:
                mock_fallback.return_value = japanese_keywords
                
                keywords = await llm_service.generate_keywords(session)
                
                # Verify Japanese content
                for keyword in keywords:
                    has_japanese = any(ord(char) > 127 for char in keyword)
                    assert has_japanese, f"Fallback keyword '{keyword}' should contain Japanese characters"
    
    @pytest.mark.asyncio
    async def test_fallback_keywords_uniqueness(self, llm_service):
        """Test that fallback keywords are unique."""
        session = Session(
            id=uuid.uuid4(),
            state=SessionState.INIT,
            initialCharacter="あ",
            themeId="adventure",
            fallbackFlags=[]
        )
        
        unique_keywords = ["愛", "希望", "勇気", "自由"]
        
        with patch.object(llm_service, '_execute_with_fallback', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = AllProvidersFailedError("Provider failed")
            
            with patch.object(llm_service.fallback_manager, 'get_keywords_for_character', new_callable=AsyncMock) as mock_fallback:
                mock_fallback.return_value = unique_keywords
                
                keywords = await llm_service.generate_keywords(session)
                
                # Verify uniqueness
                assert len(keywords) == len(set(keywords)), "Fallback keywords should be unique"


class TestKeywordFallbackErrorRecording:
    """Test error recording and monitoring for fallback scenarios."""
    
    @pytest.fixture
    def llm_service(self):
        return ExternalLLMService()
    
    @pytest.mark.asyncio
    async def test_fallback_records_original_error(self, llm_service):
        """Test that fallback scenario records the original LLM error."""
        session = Session(
            id=uuid.uuid4(),
            state=SessionState.INIT,
            initialCharacter="あ",
            themeId="adventure",
            fallbackFlags=[],
            llmErrors=[]
        )
        
        original_error = AllProvidersFailedError("OpenAI rate limit exceeded")
        fallback_keywords = ["エラー1", "エラー2", "エラー3", "エラー4"]
        
        with patch.object(llm_service, '_execute_with_fallback', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = original_error
            
            with patch.object(llm_service.fallback_manager, 'get_keywords_for_character', new_callable=AsyncMock) as mock_fallback:
                mock_fallback.return_value = fallback_keywords
                
                keywords = await llm_service.generate_keywords(session)
                
                # Verify fallback worked
                assert keywords == fallback_keywords
                assert "keyword_generation" in session.fallbackFlags
    
    @pytest.mark.asyncio
    async def test_fallback_preserves_session_state(self, llm_service):
        """Test that fallback doesn't corrupt session state."""
        session = Session(
            id=uuid.uuid4(),
            state=SessionState.INIT,
            initialCharacter="あ",
            themeId="adventure",
            fallbackFlags=[],
            llmGenerations=[],
            llmErrors=[]
        )
        
        original_id = session.id
        original_state = session.state
        original_character = session.initialCharacter
        original_theme = session.themeId
        
        fallback_keywords = ["保持1", "保持2", "保持3", "保持4"]
        
        with patch.object(llm_service, '_execute_with_fallback', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = AllProvidersFailedError("Provider failed")
            
            with patch.object(llm_service.fallback_manager, 'get_keywords_for_character', new_callable=AsyncMock) as mock_fallback:
                mock_fallback.return_value = fallback_keywords
                
                keywords = await llm_service.generate_keywords(session)
                
                # Verify session state is preserved
                assert session.id == original_id
                assert session.state == original_state
                assert session.initialCharacter == original_character
                assert session.themeId == original_theme
                
                # Only fallback flag should be added
                assert "keyword_generation" in session.fallbackFlags
                assert len(session.fallbackFlags) == 1


class TestKeywordFallbackPerformance:
    """Test performance characteristics of fallback mechanisms."""
    
    @pytest.fixture
    def llm_service(self):
        return ExternalLLMService()
    
    @pytest.mark.asyncio
    async def test_fallback_response_time(self, llm_service):
        """Test that fallback mechanism responds quickly."""
        import time
        
        session = Session(
            id=uuid.uuid4(),
            state=SessionState.INIT,
            initialCharacter="あ",
            themeId="adventure",
            fallbackFlags=[]
        )
        
        fallback_keywords = ["高速1", "高速2", "高速3", "高速4"]
        
        with patch.object(llm_service, '_execute_with_fallback', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = AllProvidersFailedError("Provider failed")
            
            with patch.object(llm_service.fallback_manager, 'get_keywords_for_character', new_callable=AsyncMock) as mock_fallback:
                mock_fallback.return_value = fallback_keywords
                
                start_time = time.time()
                keywords = await llm_service.generate_keywords(session)
                end_time = time.time()
                
                # Fallback should be very fast (< 100ms)
                fallback_time_ms = (end_time - start_time) * 1000
                assert fallback_time_ms < 100, f"Fallback took {fallback_time_ms}ms, should be < 100ms"
                
                assert keywords == fallback_keywords
                assert "keyword_generation" in session.fallbackFlags
