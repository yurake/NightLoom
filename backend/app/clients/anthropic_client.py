"""
Anthropic client implementation for NightLoom LLM integration.

Provides Anthropic-specific implementation of the BaseLLMClient interface
with support for Claude keyword generation, proper error handling, and monitoring.
"""

import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

try:
    import anthropic
    from anthropic import AsyncAnthropic
except ImportError:
    anthropic = None
    AsyncAnthropic = None

from .llm_client import (
    BaseLLMClient, LLMRequest, LLMResponse, LLMTaskType, LLMClientError,
    ValidationError, RateLimitError, ProviderUnavailableError
)
from ..models.llm_config import ProviderConfig, LLMProvider
from ..services.prompt_template import get_template_manager


class AnthropicClientError(LLMClientError):
    """Anthropic-specific client errors."""
    pass


class AnthropicCreditError(LLMClientError):
    """Raised when Anthropic account has insufficient credits."""
    pass


class AnthropicAccountError(LLMClientError):
    """Raised when there's an Anthropic account-related issue (auth, billing, etc)."""
    pass


class AnthropicClient(BaseLLMClient):
    """Anthropic client implementation for NightLoom."""
    
    def __init__(self, config: ProviderConfig):
        """
        Initialize Anthropic client.
        
        Args:
            config: Provider configuration with API key and settings
            
        Raises:
            AnthropicClientError: If Anthropic SDK is not available or config is invalid
        """
        super().__init__(config)
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        if anthropic is None:
            raise AnthropicClientError("Anthropic SDK not installed. Run: uv add anthropic")
        
        if not config.api_key:
            raise AnthropicClientError("Anthropic API key is required")
        
        # Initialize Anthropic client
        self.client = AsyncAnthropic(api_key=config.api_key)
        self.template_manager = get_template_manager()
        
        # Configuration
        self.default_model = config.model_name or "claude-3-haiku-20240307"
        self.default_temperature = config.temperature or 0.7
        self.default_max_tokens = config.max_tokens or 1000
        self.request_timeout = config.timeout_seconds or 30
        
        # Rate limiting (use default value since ProviderConfig doesn't have rate_limit field)
        self.requests_per_minute = 60  # Default rate limit
        self._request_times: List[datetime] = []
        
    async def generate_keywords(self, request: LLMRequest) -> LLMResponse:
        """
        Generate keyword candidates using Anthropic Claude.
        
        Args:
            request: LLM request with template data
            
        Returns:
            LLMResponse with generated keywords
            
        Raises:
            ValidationError: If request validation fails
            RateLimitError: If rate limit exceeded
            AnthropicClientError: If Anthropic API call fails
        """
        await self._check_rate_limit()
        
        try:
            # API呼び出し前の検証
            if not self.client:
                raise AnthropicClientError("Anthropic client not initialized")
            
            # Log request start
            initial_character = request.template_data.get("initial_character", "unknown")
            self.logger.info(f"[Anthropic] Starting keyword generation for initial_character: {initial_character}")
            
            # Render prompt template
            prompt = await self.template_manager.render_template(
                task_type=LLMTaskType.KEYWORD_GENERATION,
                template_data=request.template_data
            )
            
            # Log prompt content
            self.logger.debug(f"[Anthropic] Prompt content: {prompt}")
            
            # Prepare Anthropic request
            system_message = "あなたは日本語の心理診断ゲーム用キーワード生成エキスパートです。指定された条件に従って適切なキーワードを生成してください。"
            
            # Log API call preparation
            self.logger.info(f"[Anthropic] Sending request to model: {self.default_model}")
            
            # Execute Anthropic API call
            start_time = datetime.now(timezone.utc)
            
            response = await self.client.messages.create(
                model=self.default_model,
                max_tokens=self.default_max_tokens,
                temperature=self.default_temperature,
                system=system_message,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            end_time = datetime.now(timezone.utc)
            latency_ms = (end_time - start_time).total_seconds() * 1000
            
            # Log response received
            self.logger.info(f"[Anthropic] Response received in {latency_ms:.1f}ms")
            self.logger.debug(f"[Anthropic] Full response object: {response}")
            
            # Parse response
            content_text = response.content[0].text if response.content else None
            if not content_text:
                raise AnthropicClientError("Empty response from Anthropic")
            
            # Log response content
            self.logger.info(f"[Anthropic] Raw response content: {content_text}")
            
            try:
                content = json.loads(content_text)
                self.logger.info(f"[Anthropic] Parsed JSON content: {content}")
            except json.JSONDecodeError as e:
                self.logger.error(f"[Anthropic] JSON parsing failed: {e}")
                raise ValidationError(f"Invalid JSON response: {e}")
            
            # Validate new keyword format with reading information
            await self._validate_keyword_response(content, request.template_data)
            
            # Calculate cost estimate (rough Claude pricing)
            input_tokens = response.usage.input_tokens if response.usage else 0
            output_tokens = response.usage.output_tokens if response.usage else 0
            total_tokens = input_tokens + output_tokens
            cost_estimate = (input_tokens * 0.00025 + output_tokens * 0.00125) / 1000  # USD per 1K tokens for Haiku
            
            # Log usage information
            self.logger.info(f"[Anthropic] Token usage - Input: {input_tokens}, Output: {output_tokens}, Total: {total_tokens}")
            self.logger.info(f"[Anthropic] Estimated cost: ${cost_estimate:.4f}")
            
            # Create response object
            llm_response = LLMResponse(
                task_type=request.task_type,
                session_id=request.session_id,
                content=content,
                provider=LLMProvider.ANTHROPIC,
                model_name=response.model,
                tokens_used=total_tokens,
                latency_ms=latency_ms,
                cost_estimate=cost_estimate,
                timestamp=end_time
            )
            
            # Validate response (general validation)
            await self._validate_response(llm_response)
            
            # Update metrics
            self._update_metrics("generate_keywords", latency_ms=latency_ms, tokens_used=total_tokens)
            
            self.logger.info(f"[Anthropic] Keyword generation completed successfully")
            return llm_response
            
        except anthropic.RateLimitError as e:
            self.logger.error(f"[Anthropic] Rate limit exceeded: {type(e).__name__}: {str(e)}")
            self._update_metrics("generate_keywords", error=True)
            raise RateLimitError(f"Anthropic rate limit exceeded: {e}")
        except anthropic.APITimeoutError as e:
            self.logger.error(f"[Anthropic] API timeout: {type(e).__name__}: {str(e)}")
            self._update_metrics("generate_keywords", error=True)
            raise ProviderUnavailableError(f"Anthropic timeout: {e}")
        except anthropic.APIConnectionError as e:
            self.logger.error(f"[Anthropic] Connection error: {type(e).__name__}: {str(e)}")
            self._update_metrics("generate_keywords", error=True)
            raise ProviderUnavailableError(f"Anthropic connection error: {e}")
        except anthropic.AuthenticationError as e:
            self.logger.error(f"[Anthropic] Authentication error: {type(e).__name__}: {str(e)}")
            self._update_metrics("generate_keywords", error=True)
            raise AnthropicAccountError(f"Anthropic authentication error: {e}")
        except anthropic.BadRequestError as e:
            # Check if this is a credit/billing issue
            error_message = str(e).lower()
            if "credit balance is too low" in error_message or "billing" in error_message:
                self.logger.warning(f"[Anthropic] Credit insufficient - not a technical error: {str(e)}")
                self._update_metrics("generate_keywords", error=True)
                raise AnthropicCreditError(f"Anthropic credit insufficient: {e}")
            else:
                self.logger.error(f"[Anthropic] Bad request error: {type(e).__name__}: {str(e)}")
                self._update_metrics("generate_keywords", error=True)
                raise AnthropicClientError(f"Anthropic bad request: {e}")
        except ValidationError as e:
            self.logger.error(f"[Anthropic] Validation error: {type(e).__name__}: {str(e)}")
            self._update_metrics("generate_keywords", error=True)
            raise e  # Re-raise validation errors as-is
        except Exception as e:
            self.logger.error(f"[Anthropic] Unexpected error: {type(e).__name__}: {str(e)}")
            self.logger.debug(f"[Anthropic] Full exception details:", exc_info=True)
            self._update_metrics("generate_keywords", error=True)
            raise AnthropicClientError(f"Anthropic API error: {e}")
    
    async def generate_axes(self, request: LLMRequest) -> LLMResponse:
        """Generate evaluation axes (placeholder - will be implemented in Phase 4)."""
        raise NotImplementedError("Axis generation will be implemented in Phase 4 (US2)")
    
    async def generate_scenario(self, request: LLMRequest) -> LLMResponse:
        """Generate scenario (placeholder - will be implemented in Phase 5)."""
        raise NotImplementedError("Scenario generation will be implemented in Phase 5 (US3)")
    
    async def analyze_results(self, request: LLMRequest) -> LLMResponse:
        """Analyze results (placeholder - will be implemented in Phase 6)."""
        raise NotImplementedError("Result analysis will be implemented in Phase 6 (US4)")
    
    async def health_check(self) -> bool:
        """
        Check if Anthropic API is accessible and healthy.
        
        Returns:
            True if API is healthy and has sufficient credits, False otherwise
        """
        try:
            # Simple test call with minimal token usage and proper system parameter
            test_response = await self.client.messages.create(
                model="claude-3-haiku-20240307",  # Use faster model for health check
                max_tokens=1,
                system="Health check test.",  # Required system parameter
                messages=[{"role": "user", "content": "ok"}]
            )
            self.logger.debug(f"[Anthropic Health Check] ✓ Healthy")
            return test_response is not None
        except anthropic.BadRequestError as e:
            # Check if this is a credit/billing issue
            error_message = str(e).lower()
            if "credit balance is too low" in error_message or "billing" in error_message:
                self.logger.info(f"[Anthropic Health Check] Credit insufficient - provider unavailable: {str(e)}")
                return False  # Provider unavailable due to credits, not unhealthy
            else:
                self.logger.warning(f"[Anthropic Health Check] Bad request error: {str(e)}")
                return False
        except anthropic.AuthenticationError as e:
            self.logger.warning(f"[Anthropic Health Check] Authentication error: {str(e)}")
            return False
        except anthropic.RateLimitError as e:
            self.logger.info(f"[Anthropic Health Check] Rate limited: {str(e)}")
            return False  # Temporary unavailability
        except anthropic.APIConnectionError as e:
            self.logger.warning(f"[Anthropic Health Check] Connection error: {str(e)}")
            return False
        except anthropic.APITimeoutError as e:
            self.logger.warning(f"[Anthropic Health Check] Timeout error: {str(e)}")
            return False
        except Exception as e:
            # Log unexpected errors for debugging
            self.logger.debug(f"[Anthropic Health Check] Unexpected error: {type(e).__name__}: {e}")
            return False
    
    async def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting."""
        now = datetime.now(timezone.utc)
        
        # Remove requests older than 1 minute
        cutoff_time = now.timestamp() - 60
        self._request_times = [
            req_time for req_time in self._request_times 
            if req_time.timestamp() > cutoff_time
        ]
        
        # Check if we're at the limit
        if len(self._request_times) >= self.requests_per_minute:
            sleep_time = 60 - (now.timestamp() - self._request_times[0].timestamp())
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        # Record this request
        self._request_times.append(now)
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough estimation of token count (4 characters ≈ 1 token)."""
        return max(1, len(text) // 4)
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider-specific information."""
        return {
            "provider": "anthropic",
            "model": self.default_model,
            "temperature": self.default_temperature,
            "max_tokens": self.default_max_tokens,
            "timeout": self.request_timeout,
            "rate_limit": self.requests_per_minute,
            "recent_requests": len(self._request_times)
        }
    
    async def _validate_keyword_response(self, content: Dict[str, Any], template_data: Dict[str, Any]) -> None:
        """
        Validate keyword response with new format including reading information.
        
        Args:
            content: Parsed JSON response from Anthropic
            template_data: Original template data used for request
            
        Raises:
            ValidationError: If response format is invalid or reading doesn't match initial character
        """
        if not isinstance(content, dict):
            raise ValidationError("Response must be a JSON object")
        
        if "keywords" not in content:
            raise ValidationError("Response must contain 'keywords' field")
        
        keywords = content["keywords"]
        if not isinstance(keywords, list):
            raise ValidationError("'keywords' must be an array")
        
        expected_count = template_data.get("count", 4)
        if len(keywords) != expected_count:
            raise ValidationError(f"Expected {expected_count} keywords, got {len(keywords)}")
        
        initial_character = template_data.get("initial_character", "")
        if not initial_character:
            raise ValidationError("initial_character is required for validation")
        
        for i, keyword_obj in enumerate(keywords):
            if not isinstance(keyword_obj, dict):
                raise ValidationError(f"Keyword {i+1} must be an object with 'word' and 'reading' fields")
            
            if "word" not in keyword_obj or "reading" not in keyword_obj:
                raise ValidationError(f"Keyword {i+1} must have both 'word' and 'reading' fields")
            
            word = keyword_obj["word"]
            reading = keyword_obj["reading"]
            
            if not isinstance(word, str) or not isinstance(reading, str):
                raise ValidationError(f"Keyword {i+1}: both 'word' and 'reading' must be strings")
            
            if not word.strip() or not reading.strip():
                raise ValidationError(f"Keyword {i+1}: 'word' and 'reading' cannot be empty")
            
            # Check if reading starts with initial character
            if not reading.startswith(initial_character):
                raise ValidationError(
                    f"Keyword {i+1} '{word}' (reading: '{reading}') does not start with '{initial_character}'"
                )
            
            # Check word length (2-6 characters as specified)
            if len(word) < 1 or len(word) > 6:
                raise ValidationError(f"Keyword {i+1} '{word}' length must be 1-6 characters")
            
            # Check reading length (reasonable bounds)
            if len(reading) < 1 or len(reading) > 10:
                raise ValidationError(f"Keyword {i+1} reading '{reading}' length must be 1-10 characters")
