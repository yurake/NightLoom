"""
OpenAI client implementation for NightLoom LLM integration.

Provides OpenAI-specific implementation of the BaseLLMClient interface
with support for GPT-4 keyword generation, proper error handling, and monitoring.
"""

import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

try:
    import openai
    from openai import AsyncOpenAI
except ImportError:
    openai = None
    AsyncOpenAI = None

from .llm_client import (
    BaseLLMClient, LLMRequest, LLMResponse, LLMTaskType, LLMClientError,
    ValidationError, RateLimitError, ProviderUnavailableError
)
from ..models.llm_config import ProviderConfig, LLMProvider
from ..services.prompt_template import get_template_manager


class OpenAIClientError(LLMClientError):
    """OpenAI-specific client errors."""
    pass


class OpenAIClient(BaseLLMClient):
    """OpenAI client implementation for NightLoom."""
    
    def __init__(self, config: ProviderConfig):
        """
        Initialize OpenAI client.
        
        Args:
            config: Provider configuration with API key and settings
            
        Raises:
            OpenAIClientError: If OpenAI SDK is not available or config is invalid
        """
        super().__init__(config)
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        if openai is None:
            raise OpenAIClientError("OpenAI SDK not installed. Run: uv add openai")
        
        if not config.api_key:
            raise OpenAIClientError("OpenAI API key is required")
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(api_key=config.api_key)
        self.template_manager = get_template_manager()
        
        # Configuration
        self.default_model = config.model_name or "gpt-4"
        self.default_temperature = config.temperature or 0.7
        self.default_max_tokens = config.max_tokens or 1000
        self.request_timeout = config.timeout_seconds or 30
        
        # Rate limiting (use default value since ProviderConfig doesn't have rate_limit field)
        self.requests_per_minute = 60  # Default rate limit
        self._request_times: List[datetime] = []
        
    async def generate_keywords(self, request: LLMRequest) -> LLMResponse:
        """
        Generate keyword candidates using OpenAI GPT.
        
        Args:
            request: LLM request with template data
            
        Returns:
            LLMResponse with generated keywords
            
        Raises:
            ValidationError: If request validation fails
            RateLimitError: If rate limit exceeded
            OpenAIClientError: If OpenAI API call fails
        """
        await self._check_rate_limit()
        
        try:
            # API呼び出し前の検証
            if not self.client:
                raise OpenAIClientError("OpenAI client not initialized")
            
            # Log request start
            initial_character = request.template_data.get("initial_character", "unknown")
            self.logger.info(f"[OpenAI] Starting keyword generation for initial_character: {initial_character}")
            
            # Render prompt template
            prompt = await self.template_manager.render_template(
                task_type=LLMTaskType.KEYWORD_GENERATION,
                template_data=request.template_data
            )
            
            # Log prompt content
            self.logger.debug(f"[OpenAI] Prompt content: {prompt}")
            
            # Prepare OpenAI request
            messages = [
                {
                    "role": "system",
                    "content": "あなたは日本語の心理診断ゲーム用キーワード生成エキスパートです。指定された条件に従って適切なキーワードを生成してください。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            # Log API call preparation
            self.logger.info(f"[OpenAI] Sending request to model: {self.default_model}")
            
            # Execute OpenAI API call
            start_time = datetime.now(timezone.utc)
            
            # GPT-4 doesn't support response_format, so we use a model that does or remove the parameter
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini" if self.default_model == "gpt-4" else self.default_model,
                messages=messages,
                temperature=self.default_temperature,
                max_tokens=self.default_max_tokens,
                timeout=self.request_timeout,
                response_format={"type": "json_object"}
            )
            
            end_time = datetime.now(timezone.utc)
            latency_ms = (end_time - start_time).total_seconds() * 1000
            
            # Log response received
            self.logger.info(f"[OpenAI] Response received in {latency_ms:.1f}ms")
            self.logger.debug(f"[OpenAI] Full response object: {response}")
            
            # Parse response
            content_text = response.choices[0].message.content
            if not content_text:
                raise OpenAIClientError("Empty response from OpenAI")
            
            # Log response content
            self.logger.info(f"[OpenAI] Raw response content: {content_text}")
            
            try:
                content = json.loads(content_text)
                self.logger.info(f"[OpenAI] Parsed JSON content: {content}")
            except json.JSONDecodeError as e:
                self.logger.error(f"[OpenAI] JSON parsing failed: {e}")
                raise ValidationError(f"Invalid JSON response: {e}")
            
            # Validate new keyword format with reading information
            await self._validate_keyword_response(content, request.template_data)
            
            # Calculate cost estimate (rough GPT-4 pricing)
            prompt_tokens = response.usage.prompt_tokens if response.usage else 0
            completion_tokens = response.usage.completion_tokens if response.usage else 0
            total_tokens = prompt_tokens + completion_tokens
            cost_estimate = (prompt_tokens * 0.03 + completion_tokens * 0.06) / 1000  # USD per 1K tokens
            
            # Log usage information
            self.logger.info(f"[OpenAI] Token usage - Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}")
            self.logger.info(f"[OpenAI] Estimated cost: ${cost_estimate:.4f}")
            
            # Create response object
            llm_response = LLMResponse(
                task_type=request.task_type,
                session_id=request.session_id,
                content=content,
                provider=LLMProvider.OPENAI,
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
            
            self.logger.info(f"[OpenAI] Keyword generation completed successfully")
            return llm_response
            
        except openai.RateLimitError as e:
            self.logger.error(f"[OpenAI] Rate limit exceeded: {type(e).__name__}: {str(e)}")
            self._update_metrics("generate_keywords", error=True)
            raise RateLimitError(f"OpenAI rate limit exceeded: {e}")
        except openai.APITimeoutError as e:
            self.logger.error(f"[OpenAI] API timeout: {type(e).__name__}: {str(e)}")
            self._update_metrics("generate_keywords", error=True)
            raise ProviderUnavailableError(f"OpenAI timeout: {e}")
        except openai.APIConnectionError as e:
            self.logger.error(f"[OpenAI] Connection error: {type(e).__name__}: {str(e)}")
            self._update_metrics("generate_keywords", error=True)
            raise ProviderUnavailableError(f"OpenAI connection error: {e}")
        except openai.AuthenticationError as e:
            self.logger.error(f"[OpenAI] Authentication error: {type(e).__name__}: {str(e)}")
            self._update_metrics("generate_keywords", error=True)
            raise OpenAIClientError(f"OpenAI authentication error: {e}")
        except ValidationError as e:
            self.logger.error(f"[OpenAI] Validation error: {type(e).__name__}: {str(e)}")
            self._update_metrics("generate_keywords", error=True)
            raise e  # Re-raise validation errors as-is
        except Exception as e:
            self.logger.error(f"[OpenAI] Unexpected error: {type(e).__name__}: {str(e)}")
            self.logger.debug(f"[OpenAI] Full exception details:", exc_info=True)
            self._update_metrics("generate_keywords", error=True)
            raise OpenAIClientError(f"OpenAI API error: {e}")
    
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
        Check if OpenAI API is accessible and healthy.
        
        Returns:
            True if API is healthy, False otherwise
        """
        try:
            # Simple test call with minimal token usage
            test_response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Use cheaper model for health check
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
                timeout=10
            )
            return test_response is not None
        except Exception:
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
            "provider": "openai",
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
            content: Parsed JSON response from OpenAI
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
                self.logger.warning(
                    f"[OpenAI] Keyword {i+1} '{word}' (reading: '{reading}') does not start with '{initial_character}' - continuing anyway"
                )
            
            # Check word length (2-6 characters as specified)
            if len(word) < 1 or len(word) > 6:
                raise ValidationError(f"Keyword {i+1} '{word}' length must be 1-6 characters")
            
            # Check reading length (reasonable bounds)
            if len(reading) < 1 or len(reading) > 10:
                raise ValidationError(f"Keyword {i+1} reading '{reading}' length must be 1-10 characters")
