"""
Integration tests for LLM keyword generation.

Tests the complete keyword generation flow including OpenAI integration,
prompt template rendering, and response validation.
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from app.clients.llm_client import LLMRequest, LLMTaskType, ValidationError
from app.clients.openai_client import OpenAIClient, OpenAIClientError
from app.models.llm_config import ProviderConfig, LLMProvider
from app.services.external_llm import ExternalLLMService, get_llm_service
from app.models.session import Session, SessionState
from uuid import uuid4


class TestLLMKeywordGeneration:
    """Test LLM keyword generation functionality."""

    @pytest.fixture
    def mock_openai_config(self):
        """Create mock OpenAI configuration."""
        return ProviderConfig(
            provider=LLMProvider.OPENAI,
            api_key="test-api-key",
            model_name="gpt-4",
            max_tokens=1000,
            temperature=0.7,
            timeout_seconds=30
        )

    @pytest.fixture
    def sample_session(self):
        """Create sample session for testing."""
        return Session(
            id=uuid4(),
            state=SessionState.INIT,
            initialCharacter="あ",
            themeId="default"
        )

    @pytest.fixture
    def valid_openai_response(self):
        """Create valid OpenAI API response."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "keywords": [
                {"word": "愛情", "reading": "あいじょう"},
                {"word": "冒険", "reading": "ぼうけん"},
                {"word": "挑戦", "reading": "ちょうせん"},
                {"word": "成長", "reading": "せいちょう"}
            ]
        })
        mock_response.model = "gpt-4"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        return mock_response

    @pytest.fixture
    def valid_keyword_response_correct_reading(self):
        """Create valid response with correct reading starting with initial character."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "keywords": [
                {"word": "愛情", "reading": "あいじょう"},
                {"word": "新しい", "reading": "あたらしい"},
                {"word": "温かい", "reading": "あたたかい"},
                {"word": "明るい", "reading": "あかるい"}
            ]
        })
        mock_response.model = "gpt-4o-mini"
        mock_response.usage.prompt_tokens = 120
        mock_response.usage.completion_tokens = 60
        return mock_response

    @pytest.mark.asyncio
    async def test_openai_client_initialization(self, mock_openai_config):
        """Test OpenAI client initialization."""
        with patch('app.clients.openai_client.AsyncOpenAI') as mock_openai:
            client = OpenAIClient(mock_openai_config)
            assert client.config == mock_openai_config
            assert client.default_model == "gpt-4"
            assert client.default_temperature == 0.7
            mock_openai.assert_called_once_with(api_key="test-api-key")

    @pytest.mark.asyncio
    async def test_openai_client_initialization_missing_api_key(self):
        """Test OpenAI client initialization fails without API key."""
        # Mock the config validation to bypass Pydantic
        with patch('app.models.llm_config.ProviderConfig') as mock_config:
            mock_config_instance = MagicMock()
            mock_config_instance.provider = LLMProvider.OPENAI
            mock_config_instance.api_key = ""  # Empty API key
            mock_config_instance.model_name = "gpt-4"
            mock_config.return_value = mock_config_instance
            
            with pytest.raises(OpenAIClientError, match="OpenAI API key is required"):
                OpenAIClient(mock_config_instance)

    @pytest.mark.asyncio
    async def test_keyword_generation_success(self, mock_openai_config, valid_keyword_response_correct_reading):
        """Test successful keyword generation with correct reading."""
        with patch('app.clients.openai_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create.return_value = valid_keyword_response_correct_reading
            mock_openai.return_value = mock_client
            
            client = OpenAIClient(mock_openai_config)
            
            request = LLMRequest(
                task_type=LLMTaskType.KEYWORD_GENERATION,
                session_id="test-session",
                template_data={
                    "initial_character": "あ",
                    "count": 4
                }
            )
            
            response = await client.generate_keywords(request)
            
            assert response.task_type == LLMTaskType.KEYWORD_GENERATION
            assert response.session_id == "test-session"
            assert response.provider == LLMProvider.OPENAI
            assert response.model_name == "gpt-4o-mini"
            assert "keywords" in response.content
            assert len(response.content["keywords"]) == 4
            
            # Verify all keywords have proper format
            for keyword in response.content["keywords"]:
                assert "word" in keyword
                assert "reading" in keyword
                assert keyword["reading"].startswith("あ")

    @pytest.mark.asyncio
    async def test_keyword_generation_validation_error_wrong_count(self, mock_openai_config):
        """Test validation error when wrong number of keywords returned."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "keywords": [
                {"word": "愛情", "reading": "あいじょう"},
                {"word": "明るい", "reading": "あかるい"}
            ]  # Only 2 keywords instead of 4
        })
        mock_response.model = "gpt-4o-mini"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 30
        
        with patch('app.clients.openai_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            client = OpenAIClient(mock_openai_config)
            
            request = LLMRequest(
                task_type=LLMTaskType.KEYWORD_GENERATION,
                session_id="test-session",
                template_data={
                    "initial_character": "あ",
                    "count": 4
                }
            )
            
            with pytest.raises(ValidationError, match="Expected 4 keywords, got 2"):
                await client.generate_keywords(request)

    @pytest.mark.asyncio
    async def test_keyword_generation_validation_missing_fields(self, mock_openai_config):
        """Test validation error when keyword objects missing required fields."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "keywords": [
                {"word": "愛情"},  # Missing "reading" field
                {"reading": "あかるい"},  # Missing "word" field
                {"word": "温かい", "reading": "あたたかい"},
                {"word": "新しい", "reading": "あたらしい"}
            ]
        })
        mock_response.model = "gpt-4o-mini"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        
        with patch('app.clients.openai_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            client = OpenAIClient(mock_openai_config)
            
            request = LLMRequest(
                task_type=LLMTaskType.KEYWORD_GENERATION,
                session_id="test-session",
                template_data={
                    "initial_character": "あ",
                    "count": 4
                }
            )
            
            with pytest.raises(ValidationError, match="must have both 'word' and 'reading' fields"):
                await client.generate_keywords(request)

    @pytest.mark.asyncio
    async def test_keyword_generation_invalid_json(self, mock_openai_config):
        """Test handling of invalid JSON response."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Invalid JSON content"
        mock_response.model = "gpt-4o-mini"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 20
        
        with patch('app.clients.openai_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            client = OpenAIClient(mock_openai_config)
            
            request = LLMRequest(
                task_type=LLMTaskType.KEYWORD_GENERATION,
                session_id="test-session",
                template_data={
                    "initial_character": "あ",
                    "count": 4
                }
            )
            
            with pytest.raises(ValidationError, match="Invalid JSON response"):
                await client.generate_keywords(request)

    @pytest.mark.asyncio
    async def test_external_llm_service_keyword_generation_integration(self, sample_session, valid_keyword_response_correct_reading):
        """Test keyword generation through ExternalLLMService."""
        with patch('app.clients.openai_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create.return_value = valid_keyword_response_correct_reading
            mock_openai.return_value = mock_client
            
            # Mock health check to return True
            with patch.object(OpenAIClient, 'health_check', return_value=True):
                llm_service = get_llm_service()
                
                keywords = await llm_service.generate_keywords(sample_session)
                
                assert len(keywords) == 4
                assert all(isinstance(keyword, str) for keyword in keywords)
                
                # Verify the keywords are extracted correctly from the new format
                expected_keywords = ["愛情", "新しい", "温かい", "明るい"]
                assert keywords == expected_keywords

    @pytest.mark.asyncio
    async def test_external_llm_service_fallback_on_failure(self, sample_session):
        """Test fallback to static keywords when LLM fails."""
        with patch('app.clients.openai_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            mock_openai.return_value = mock_client
            
            # Mock health check to return False to trigger fallback
            with patch.object(OpenAIClient, 'health_check', return_value=False):
                llm_service = get_llm_service()
                
                # Should not raise exception, should use fallback
                keywords = await llm_service.generate_keywords(sample_session)
                
                assert len(keywords) == 4
                assert all(isinstance(keyword, str) for keyword in keywords)
                # Check for any fallback flag related to keyword generation
                assert any("keyword" in flag for flag in sample_session.fallbackFlags)

    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_openai_config):
        """Test successful health check."""
        mock_health_response = MagicMock()
        mock_health_response.choices = [MagicMock()]
        mock_health_response.choices[0].message.content = "pong"
        
        with patch('app.clients.openai_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create.return_value = mock_health_response
            mock_openai.return_value = mock_client
            
            client = OpenAIClient(mock_openai_config)
            is_healthy = await client.health_check()
            
            assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, mock_openai_config):
        """Test health check failure."""
        with patch('app.clients.openai_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create.side_effect = Exception("Connection failed")
            mock_openai.return_value = mock_client
            
            client = OpenAIClient(mock_openai_config)
            is_healthy = await client.health_check()
            
            assert is_healthy is False

    @pytest.mark.asyncio
    async def test_rate_limiting(self, mock_openai_config, valid_keyword_response_correct_reading):
        """Test rate limiting functionality."""
        with patch('app.clients.openai_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create.return_value = valid_keyword_response_correct_reading
            mock_openai.return_value = mock_client
            
            client = OpenAIClient(mock_openai_config)
            client.requests_per_minute = 2  # Set low limit for testing
            
            request = LLMRequest(
                task_type=LLMTaskType.KEYWORD_GENERATION,
                session_id="test-session",
                template_data={
                    "initial_character": "あ",
                    "count": 4
                }
            )
            
            # First two requests should succeed quickly
            start_time = datetime.now()
            await client.generate_keywords(request)
            await client.generate_keywords(request)
            
            # Third request should be rate limited (but won't wait in test)
            with patch('asyncio.sleep') as mock_sleep:
                await client.generate_keywords(request)
                # In a real scenario, this would sleep, but in test we just verify the call
                mock_sleep.assert_called()
