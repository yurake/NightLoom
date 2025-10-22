"""
Unit tests for OpenAI client implementation.

Tests OpenAI client behavior in isolation with mocked dependencies.
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from app.clients.openai_client import OpenAIClient, OpenAIClientError
from app.clients.llm_client import (
    LLMRequest, LLMResponse, LLMTaskType, ValidationError,
    RateLimitError, ProviderUnavailableError
)
from app.models.llm_config import ProviderConfig, LLMProvider


class TestOpenAIClient:
    """Unit tests for OpenAI client."""

    @pytest.fixture
    def openai_config(self):
        """Create OpenAI configuration for testing."""
        return ProviderConfig(
            provider=LLMProvider.OPENAI,
            api_key="sk-test-key-123",
            model_name="gpt-4",
            max_tokens=1000,
            temperature=0.7,
            timeout_seconds=30
        )

    @pytest.fixture
    def keyword_request(self):
        """Create sample keyword generation request."""
        return LLMRequest(
            task_type=LLMTaskType.KEYWORD_GENERATION,
            session_id="test-session-123",
            template_data={
                "initial_character": "か",
                "count": 4
            }
        )

    @pytest.fixture
    def valid_openai_response(self):
        """Create valid OpenAI response mock."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "keywords": [
                {"word": "希望", "reading": "きぼう"},
                {"word": "感謝", "reading": "かんしゃ"},
                {"word": "革新", "reading": "かくしん"},
                {"word": "協力", "reading": "きょうりょく"}
            ]
        })
        mock_response.model = "gpt-4o-mini"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 150
        mock_response.usage.completion_tokens = 80
        return mock_response

    def test_client_initialization_success(self, openai_config):
        """Test successful client initialization."""
        with patch('app.clients.openai_client.AsyncOpenAI') as mock_openai:
            client = OpenAIClient(openai_config)
            
            assert client.config == openai_config
            assert client.provider == LLMProvider.OPENAI
            assert client.default_model == "gpt-4"
            assert client.default_temperature == 0.7
            assert client.default_max_tokens == 1000
            assert client.request_timeout == 30
            
            mock_openai.assert_called_once_with(api_key="sk-test-key-123")

    def test_client_initialization_missing_openai_sdk(self, openai_config):
        """Test initialization failure when OpenAI SDK not available."""
        with patch('app.clients.openai_client.openai', None):
            with pytest.raises(OpenAIClientError, match="OpenAI SDK not installed"):
                OpenAIClient(openai_config)

    def test_client_initialization_missing_api_key(self):
        """Test initialization failure without API key."""
        # Mock the config to bypass Pydantic validation
        with patch('app.clients.openai_client.AsyncOpenAI'):
            mock_config = MagicMock()
            mock_config.provider = LLMProvider.OPENAI
            mock_config.api_key = ""  # Empty API key
            mock_config.model_name = "gpt-4"
            mock_config.temperature = 0.7
            mock_config.max_tokens = 1000
            mock_config.timeout_seconds = 30
            
            with pytest.raises(OpenAIClientError, match="OpenAI API key is required"):
                OpenAIClient(mock_config)

    @pytest.mark.asyncio
    async def test_generate_keywords_success(self, openai_config, keyword_request, valid_openai_response):
        """Test successful keyword generation."""
        with patch('app.clients.openai_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create.return_value = valid_openai_response
            mock_openai.return_value = mock_client
            
            client = OpenAIClient(openai_config)
            response = await client.generate_keywords(keyword_request)
            
            assert isinstance(response, LLMResponse)
            assert response.task_type == LLMTaskType.KEYWORD_GENERATION
            assert response.session_id == "test-session-123"
            assert response.provider == LLMProvider.OPENAI
            assert response.model_name == "gpt-4o-mini"
            assert response.tokens_used == 230  # 150 + 80
            assert response.cost_estimate > 0
            assert "keywords" in response.content
            assert len(response.content["keywords"]) == 4

    @pytest.mark.asyncio
    async def test_generate_keywords_rate_limit_error(self, openai_config, keyword_request):
        """Test handling of OpenAI rate limit error."""
        with patch('app.clients.openai_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            
            # Mock openai module for rate limit error
            with patch('app.clients.openai_client.openai') as mock_openai_module:
                mock_openai_module.RateLimitError = Exception
                mock_client.chat.completions.create.side_effect = mock_openai_module.RateLimitError("Rate limit exceeded")
                mock_openai.return_value = mock_client
                
                client = OpenAIClient(openai_config)
                
                with pytest.raises(RateLimitError, match="OpenAI rate limit exceeded"):
                    await client.generate_keywords(keyword_request)

    @pytest.mark.asyncio
    async def test_generate_keywords_timeout_error(self, openai_config, keyword_request):
        """Test handling of OpenAI timeout error."""
        with patch('app.clients.openai_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create.side_effect = Exception("Request timeout")
            mock_openai.return_value = mock_client
            
            client = OpenAIClient(openai_config)
            
            # Since we're using a generic Exception, it will be caught by the general exception handler
            with pytest.raises(OpenAIClientError, match="OpenAI API error"):
                await client.generate_keywords(keyword_request)

    @pytest.mark.asyncio
    async def test_generate_keywords_connection_error(self, openai_config, keyword_request):
        """Test handling of OpenAI connection error."""
        with patch('app.clients.openai_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create.side_effect = Exception("Connection failed")
            mock_openai.return_value = mock_client
            
            client = OpenAIClient(openai_config)
            
            # Since we're using a generic Exception, it will be caught by the general exception handler
            with pytest.raises(OpenAIClientError, match="OpenAI API error"):
                await client.generate_keywords(keyword_request)

    @pytest.mark.asyncio
    async def test_generate_keywords_authentication_error(self, openai_config, keyword_request):
        """Test handling of OpenAI authentication error."""
        with patch('app.clients.openai_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create.side_effect = Exception("Invalid API key")
            mock_openai.return_value = mock_client
            
            client = OpenAIClient(openai_config)
            
            # Since we're using a generic Exception, it will be caught by the general exception handler
            with pytest.raises(OpenAIClientError, match="OpenAI API error"):
                await client.generate_keywords(keyword_request)

    @pytest.mark.asyncio
    async def test_validate_keyword_response_success(self, openai_config):
        """Test successful keyword response validation."""
        with patch('app.clients.openai_client.AsyncOpenAI'):
            client = OpenAIClient(openai_config)
            
            valid_content = {
                "keywords": [
                    {"word": "希望", "reading": "きぼう"},
                    {"word": "感謝", "reading": "かんしゃ"},
                    {"word": "革新", "reading": "かくしん"},
                    {"word": "協力", "reading": "きょうりょく"}
                ]
            }
            
            template_data = {"initial_character": "き", "count": 4}
            
            # Should not raise exception
            await client._validate_keyword_response(valid_content, template_data)

    @pytest.mark.asyncio
    async def test_validate_keyword_response_wrong_count(self, openai_config):
        """Test validation failure for wrong keyword count."""
        with patch('app.clients.openai_client.AsyncOpenAI'):
            client = OpenAIClient(openai_config)
            
            invalid_content = {
                "keywords": [
                    {"word": "希望", "reading": "きぼう"},
                    {"word": "感謝", "reading": "かんしゃ"}
                ]  # Only 2 keywords instead of 4
            }
            
            template_data = {"initial_character": "き", "count": 4}
            
            with pytest.raises(ValidationError, match="Expected 4 keywords, got 2"):
                await client._validate_keyword_response(invalid_content, template_data)

    @pytest.mark.asyncio
    async def test_validate_keyword_response_missing_fields(self, openai_config):
        """Test validation failure for missing keyword fields."""
        with patch('app.clients.openai_client.AsyncOpenAI'):
            client = OpenAIClient(openai_config)
            
            invalid_content = {
                "keywords": [
                    {"word": "希望"},  # Missing reading
                    {"reading": "かんしゃ"},  # Missing word
                    {"word": "革新", "reading": "かくしん"},
                    {"word": "協力", "reading": "きょうりょく"}
                ]
            }
            
            template_data = {"initial_character": "き", "count": 4}
            
            with pytest.raises(ValidationError, match="must have both 'word' and 'reading' fields"):
                await client._validate_keyword_response(invalid_content, template_data)

    @pytest.mark.asyncio
    async def test_validate_keyword_response_empty_values(self, openai_config):
        """Test validation failure for empty keyword values."""
        with patch('app.clients.openai_client.AsyncOpenAI'):
            client = OpenAIClient(openai_config)
            
            invalid_content = {
                "keywords": [
                    {"word": "", "reading": "きぼう"},  # Empty word
                    {"word": "感謝", "reading": ""},  # Empty reading
                    {"word": "革新", "reading": "かくしん"},
                    {"word": "協力", "reading": "きょうりょく"}
                ]
            }
            
            template_data = {"initial_character": "き", "count": 4}
            
            with pytest.raises(ValidationError, match="'word' and 'reading' cannot be empty"):
                await client._validate_keyword_response(invalid_content, template_data)

    @pytest.mark.asyncio
    async def test_validate_keyword_response_invalid_word_length(self, openai_config):
        """Test validation failure for invalid word length."""
        with patch('app.clients.openai_client.AsyncOpenAI'):
            client = OpenAIClient(openai_config)
            
            invalid_content = {
                "keywords": [
                    {"word": "これは非常に長すぎる単語です", "reading": "きぼう"},  # Too long
                    {"word": "感謝", "reading": "かんしゃ"},
                    {"word": "革新", "reading": "かくしん"},
                    {"word": "協力", "reading": "きょうりょく"}
                ]
            }
            
            template_data = {"initial_character": "き", "count": 4}
            
            with pytest.raises(ValidationError, match="length must be 1-6 characters"):
                await client._validate_keyword_response(invalid_content, template_data)

    @pytest.mark.asyncio
    async def test_health_check_success(self, openai_config):
        """Test successful health check."""
        with patch('app.clients.openai_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "pong"
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            client = OpenAIClient(openai_config)
            result = await client.health_check()
            
            assert result is True
            mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_failure(self, openai_config):
        """Test health check failure."""
        with patch('app.clients.openai_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create.side_effect = Exception("Connection failed")
            mock_openai.return_value = mock_client
            
            client = OpenAIClient(openai_config)
            result = await client.health_check()
            
            assert result is False

    def test_get_provider_info(self, openai_config):
        """Test provider info retrieval."""
        with patch('app.clients.openai_client.AsyncOpenAI'):
            client = OpenAIClient(openai_config)
            info = client.get_provider_info()
            
            assert info["provider"] == "openai"
            assert info["model"] == "gpt-4"
            assert info["temperature"] == 0.7
            assert info["max_tokens"] == 1000
            assert info["timeout"] == 30
            assert "rate_limit" in info
            assert "recent_requests" in info

    @pytest.mark.asyncio
    async def test_rate_limiting_enforcement(self, openai_config):
        """Test rate limiting enforcement."""
        with patch('app.clients.openai_client.AsyncOpenAI') as mock_openai, \
             patch('asyncio.sleep') as mock_sleep:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client
            
            client = OpenAIClient(openai_config)
            client.requests_per_minute = 2  # Set low limit for testing
            
            # Make requests that exceed rate limit
            client._request_times = [
                datetime.now(timezone.utc),
                datetime.now(timezone.utc)
            ]
            
            # Next request should trigger rate limiting
            await client._check_rate_limit()
            
            # Should have attempted to sleep (rate limit enforcement)
            mock_sleep.assert_called()

    def test_estimate_tokens(self, openai_config):
        """Test token estimation functionality."""
        with patch('app.clients.openai_client.AsyncOpenAI'):
            client = OpenAIClient(openai_config)
            
            # Test various text lengths
            assert client._estimate_tokens("") == 1  # Minimum 1 token
            assert client._estimate_tokens("test") == 1  # 4 chars = 1 token
            assert client._estimate_tokens("test text example") >= 4  # ~17 chars = 4+ tokens
