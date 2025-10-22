"""
Integration tests for keyword generation fallback behavior.

Tests that the system gracefully falls back to static keywords
when LLM services fail or are unavailable.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4

from app.services.external_llm import ExternalLLMService, AllProvidersFailedError
from app.services.fallback_assets import FallbackAssets
from app.models.session import Session, SessionState
from app.models.llm_config import LLMConfig, LLMProvider, ProviderConfig
from app.clients.llm_client import LLMClientError, ProviderUnavailableError, RateLimitError


class TestKeywordGenerationFallback:
    """Test keyword generation fallback functionality."""

    @pytest.fixture
    def sample_session(self):
        """Create sample session for testing."""
        return Session(
            id=uuid4(),
            state=SessionState.INIT,
            initialCharacter="さ",
            themeId="default"
        )

    @pytest.fixture
    def mock_llm_config(self):
        """Create mock LLM configuration with OpenAI as primary."""
        config = LLMConfig(
            primary_provider=LLMProvider.OPENAI,
            fallback_providers=[LLMProvider.ANTHROPIC, LLMProvider.MOCK],
            providers={
                LLMProvider.OPENAI: ProviderConfig(
                    provider=LLMProvider.OPENAI,
                    api_key="test-key",
                    model_name="gpt-4"
                ),
                LLMProvider.ANTHROPIC: ProviderConfig(
                    provider=LLMProvider.ANTHROPIC,
                    api_key="test-key",
                    model_name="claude-3-sonnet"
                ),
                LLMProvider.MOCK: ProviderConfig(
                    provider=LLMProvider.MOCK,
                    model_name="mock-model"
                )
            }
        )
        return config

    @pytest.fixture
    def fallback_keywords(self):
        """Sample fallback keywords for testing."""
        return ["成功", "創造", "信念", "探求"]

    @pytest.mark.asyncio
    async def test_fallback_when_all_providers_fail(self, sample_session, mock_llm_config, fallback_keywords):
        """Test fallback to static keywords when all LLM providers fail."""
        # Mock all providers to fail
        with patch('app.clients.openai_client.OpenAIClient') as mock_openai, \
             patch('app.clients.anthropic_client.AnthropicClient') as mock_anthropic, \
             patch('app.clients.mock_client.MockLLMClient') as mock_mock, \
             patch.object(FallbackAssets, 'get_keyword_candidates', return_value=fallback_keywords):
            
            # Make all clients fail health checks
            mock_openai_instance = AsyncMock()
            mock_openai_instance.health_check.return_value = False
            mock_openai.return_value = mock_openai_instance
            
            mock_anthropic_instance = AsyncMock()
            mock_anthropic_instance.health_check.return_value = False
            mock_anthropic.return_value = mock_anthropic_instance
            
            mock_mock_instance = AsyncMock()
            mock_mock_instance.health_check.return_value = False
            mock_mock.return_value = mock_mock_instance
            
            llm_service = ExternalLLMService(config=mock_llm_config)
            keywords = await llm_service.generate_keywords(sample_session)
            
            # Should use fallback keywords
            assert keywords == fallback_keywords
            assert "keyword_generation" in sample_session.fallbackFlags

    @pytest.mark.asyncio
    async def test_fallback_when_primary_provider_fails_but_secondary_succeeds(self, sample_session, mock_llm_config):
        """Test fallback to secondary provider when primary fails."""
        mock_anthropic_response = {
            "keywords": [
                {"word": "成功", "reading": "せいこう"},
                {"word": "創造", "reading": "そうぞう"},
                {"word": "信念", "reading": "しんねん"},
                {"word": "探求", "reading": "たんきゅう"}
            ]
        }
        
        with patch('app.clients.openai_client.OpenAIClient') as mock_openai, \
             patch('app.clients.anthropic_client.AnthropicClient') as mock_anthropic:
            
            # Primary provider (OpenAI) fails health check
            mock_openai_instance = AsyncMock()
            mock_openai_instance.health_check.return_value = False
            mock_openai.return_value = mock_openai_instance
            
            # Secondary provider (Anthropic) succeeds
            mock_anthropic_instance = AsyncMock()
            mock_anthropic_instance.health_check.return_value = True
            mock_anthropic_instance.generate_keywords.return_value = MagicMock(
                content=mock_anthropic_response,
                provider=LLMProvider.ANTHROPIC,
                model_name="claude-3-sonnet",
                tokens_used=120,
                latency_ms=800,
                cost_estimate=0.008
            )
            mock_anthropic.return_value = mock_anthropic_instance
            
            llm_service = ExternalLLMService(config=mock_llm_config)
            keywords = await llm_service.generate_keywords(sample_session)
            
            # Should use keywords from secondary provider
            expected_keywords = ["成功", "創造", "信念", "探求"]
            assert keywords == expected_keywords
            
            # Should have fallback flag indicating secondary provider was used
            assert any("fallback" in flag for flag in sample_session.fallbackFlags)

    @pytest.mark.asyncio
    async def test_fallback_on_openai_rate_limit_error(self, sample_session, mock_llm_config, fallback_keywords):
        """Test fallback when OpenAI returns rate limit error."""
        with patch('app.clients.openai_client.OpenAIClient') as mock_openai, \
             patch.object(FallbackAssets, 'get_keyword_candidates', return_value=fallback_keywords):
            
            # OpenAI client throws rate limit error
            mock_openai_instance = AsyncMock()
            mock_openai_instance.health_check.return_value = True
            mock_openai_instance.generate_keywords.side_effect = RateLimitError("Rate limit exceeded")
            mock_openai.return_value = mock_openai_instance
            
            llm_service = ExternalLLMService(config=mock_llm_config)
            keywords = await llm_service.generate_keywords(sample_session)
            
            # Should fall back to static keywords
            assert keywords == fallback_keywords
            assert "keyword_generation" in sample_session.fallbackFlags
            
            # Should have error recorded
            assert len(sample_session.llmErrors) > 0
            assert any(error["error_type"] == "RateLimitError" for error in sample_session.llmErrors)

    @pytest.mark.asyncio
    async def test_fallback_on_provider_unavailable_error(self, sample_session, mock_llm_config, fallback_keywords):
        """Test fallback when provider is unavailable."""
        with patch('app.clients.openai_client.OpenAIClient') as mock_openai, \
             patch.object(FallbackAssets, 'get_keyword_candidates', return_value=fallback_keywords):
            
            # OpenAI client throws unavailable error
            mock_openai_instance = AsyncMock()
            mock_openai_instance.health_check.return_value = True
            mock_openai_instance.generate_keywords.side_effect = ProviderUnavailableError("Service unavailable")
            mock_openai.return_value = mock_openai_instance
            
            llm_service = ExternalLLMService(config=mock_llm_config)
            keywords = await llm_service.generate_keywords(sample_session)
            
            # Should fall back to static keywords
            assert keywords == fallback_keywords
            assert "keyword_generation" in sample_session.fallbackFlags

    @pytest.mark.asyncio
    async def test_fallback_on_unexpected_error(self, sample_session, mock_llm_config, fallback_keywords):
        """Test fallback when unexpected error occurs."""
        with patch('app.clients.openai_client.OpenAIClient') as mock_openai, \
             patch.object(FallbackAssets, 'get_keyword_candidates', return_value=fallback_keywords):
            
            # OpenAI client throws unexpected error
            mock_openai_instance = AsyncMock()
            mock_openai_instance.health_check.return_value = True
            mock_openai_instance.generate_keywords.side_effect = Exception("Unexpected error")
            mock_openai.return_value = mock_openai_instance
            
            llm_service = ExternalLLMService(config=mock_llm_config)
            keywords = await llm_service.generate_keywords(sample_session)
            
            # Should fall back to static keywords
            assert keywords == fallback_keywords
            assert "keyword_generation_error" in sample_session.fallbackFlags

    @pytest.mark.asyncio
    async def test_fallback_preserves_session_state(self, sample_session, mock_llm_config, fallback_keywords):
        """Test that fallback preserves session state correctly."""
        original_state = sample_session.state
        original_id = sample_session.id
        original_character = sample_session.initialCharacter
        
        with patch('app.clients.openai_client.OpenAIClient') as mock_openai, \
             patch.object(FallbackAssets, 'get_keyword_candidates', return_value=fallback_keywords):
            
            # Make OpenAI fail
            mock_openai_instance = AsyncMock()
            mock_openai_instance.health_check.return_value = False
            mock_openai.return_value = mock_openai_instance
            
            llm_service = ExternalLLMService(config=mock_llm_config)
            keywords = await llm_service.generate_keywords(sample_session)
            
            # Session state should be preserved
            assert sample_session.state == original_state
            assert sample_session.id == original_id
            assert sample_session.initialCharacter == original_character
            
            # Should have fallback keywords
            assert keywords == fallback_keywords

    @pytest.mark.asyncio
    async def test_fallback_keywords_match_initial_character(self, sample_session, mock_llm_config):
        """Test that fallback keywords are appropriate for initial character."""
        # Use real fallback assets to test character matching
        llm_service = ExternalLLMService(config=mock_llm_config)
        
        # Mock all providers to fail to force fallback
        with patch('app.clients.openai_client.OpenAIClient') as mock_openai, \
             patch('app.clients.anthropic_client.AnthropicClient') as mock_anthropic, \
             patch('app.clients.mock_client.MockLLMClient') as mock_mock:
            
            # All providers fail health checks
            for mock_client_class in [mock_openai, mock_anthropic, mock_mock]:
                mock_instance = AsyncMock()
                mock_instance.health_check.return_value = False
                mock_client_class.return_value = mock_instance
            
            keywords = await llm_service.generate_keywords(sample_session)
            
            # Should get fallback keywords
            assert len(keywords) == 4
            assert all(isinstance(keyword, str) for keyword in keywords)
            assert "keyword_generation" in sample_session.fallbackFlags

    @pytest.mark.asyncio
    async def test_fallback_usage_tracking(self, sample_session, mock_llm_config, fallback_keywords):
        """Test that fallback usage is properly tracked."""
        with patch('app.clients.openai_client.OpenAIClient') as mock_openai, \
             patch.object(FallbackAssets, 'get_keyword_candidates', return_value=fallback_keywords):
            
            # Make OpenAI fail
            mock_openai_instance = AsyncMock()
            mock_openai_instance.health_check.return_value = False
            mock_openai.return_value = mock_openai_instance
            
            llm_service = ExternalLLMService(config=mock_llm_config)
            keywords = await llm_service.generate_keywords(sample_session)
            
            # Check that fallback flag is set
            assert "keyword_generation" in sample_session.fallbackFlags
            
            # Check that no LLM generation metadata is recorded for successful fallback
            assert len(sample_session.llmGenerations) == 0 or \
                   all(gen.fallback_used for gen in sample_session.llmGenerations.values())

    @pytest.mark.asyncio
    async def test_fallback_with_different_initial_characters(self, mock_llm_config):
        """Test fallback behavior with various initial characters."""
        test_characters = ["あ", "か", "さ", "た", "な", "は", "ま", "や", "ら", "わ"]
        
        with patch('app.clients.openai_client.OpenAIClient') as mock_openai:
            # Make OpenAI fail for all requests
            mock_openai_instance = AsyncMock()
            mock_openai_instance.health_check.return_value = False
            mock_openai.return_value = mock_openai_instance
            
            llm_service = ExternalLLMService(config=mock_llm_config)
            
            for char in test_characters:
                session = Session(
                    id=uuid4(),
                    state=SessionState.INIT,
                    initialCharacter=char,
                    themeId="default"
                )
                
                keywords = await llm_service.generate_keywords(session)
                
                # Should get 4 keywords for any character
                assert len(keywords) == 4
                assert all(isinstance(keyword, str) for keyword in keywords)
                assert "keyword_generation" in session.fallbackFlags

    def test_fallback_assets_availability(self):
        """Test that fallback assets are available for all supported characters."""
        fallback_manager = FallbackAssets()
        
        # Test common hiragana characters
        test_characters = ["あ", "か", "さ", "た", "な", "は", "ま", "や", "ら", "わ"]
        
        for char in test_characters:
            keywords = fallback_manager.get_keyword_candidates(char)
            
            # Should get at least 4 keywords
            assert len(keywords) >= 4
            assert all(isinstance(keyword, str) for keyword in keywords)
            assert all(len(keyword) > 0 for keyword in keywords)
