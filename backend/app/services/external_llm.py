
"""
External LLM service integration for NightLoom.

Provides the main service layer that orchestrates LLM operations,
manages provider fallbacks, and integrates with existing session management.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from ..clients.llm_client import (BaseLLMClient, LLMClientError, LLMRequest,
                                  LLMResponse, LLMTaskType,
                                  ProviderUnavailableError, RateLimitError,
                                  ValidationError)
from ..models.llm_config import LLMConfig, LLMProvider, get_llm_config
from ..models.session import (Axis, Choice, Scene, Session, SessionState,
                              TypeProfile)
from ..services.fallback_assets import FallbackAssets
from ..services.llm_metrics import (get_metrics_tracker, record_llm_error,
                                    record_llm_response)
from ..services.prompt_template import get_template_manager, render_prompt


class LLMServiceError(Exception):
    """Base exception for LLM service errors."""
    pass


class AllProvidersFailedError(LLMServiceError):
    """Raised when all configured LLM providers fail."""
    pass


class ExternalLLMService:
    """
    Main service for external LLM operations.

    Handles provider selection, fallback logic, prompt management,
    and integration with NightLoom session flow.
    """

    def __init__(
        self,
        config: Optional[LLMConfig] = None,
        fallback_manager: Optional[FallbackAssets] = None
    ):
        """
        Initialize LLM service.

        Args:
            config: LLM configuration. Uses global config if None.
            fallback_manager: Fallback asset manager. Creates default if None.
        """
        self.config = config or get_llm_config()
        self.fallback_manager = fallback_manager or FallbackAssets()
        self.template_manager = get_template_manager()
        self.metrics_tracker = get_metrics_tracker()
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)

        # Client registry
        self._clients: Dict[LLMProvider, BaseLLMClient] = {}
        self._client_health: Dict[LLMProvider, bool] = {}

    async def _get_client(self, provider: LLMProvider) -> BaseLLMClient:
        """Get or create client for provider."""
        if provider not in self._clients:
            provider_config = self.config.get_provider_config(provider)
            if not provider_config:
                raise LLMServiceError(
                    f"No configuration for provider: {provider}")

            # Import and create client based on provider
            if provider == LLMProvider.OPENAI:
                from ..clients.openai_client import OpenAIClient
                self._clients[provider] = OpenAIClient(provider_config)
            elif provider == LLMProvider.ANTHROPIC:
                from ..clients.anthropic_client import AnthropicClient
                self._clients[provider] = AnthropicClient(provider_config)
            elif provider == LLMProvider.MOCK:
                from ..clients.mock_client import MockLLMClient
                self._clients[provider] = MockLLMClient()
            else:
                raise LLMServiceError(f"Unsupported provider: {provider}")

        return self._clients[provider]

    async def _execute_with_fallback(
        self,
        session: Session,
        task_type: LLMTaskType,
        template_data: Dict[str, Any],
        operation_type: str
    ) -> LLMResponse:
        """
        Execute LLM request with provider fallback logic.

        Args:
            session: Current session
            task_type: Type of LLM task
            template_data: Data for template rendering
            operation_type: Human-readable operation name for tracking

        Returns:
            LLM response from successful provider

        Raises:
            AllProvidersFailedError: If all providers fail
        """
        fallback_chain = self.config.get_fallback_chain()
        last_error = None

        self.logger.info(f"[Provider Chain] Starting with {len(fallback_chain)} providers: {[p.value for p in fallback_chain]}")

        for attempt, provider in enumerate(fallback_chain):
            self.logger.info(f"[Provider Chain] Trying provider {provider.value} (attempt {attempt + 1}/{len(fallback_chain)})")
            try:
                # Check provider health
                self.logger.debug(f"[LLM Service] Checking health for provider {provider}")
                is_healthy = await self._check_provider_health(provider)
                if not is_healthy:
                    self.logger.warning(f"[Provider Chain] Provider {provider.value} failed health check, skipping")
                    continue

                self.logger.info(f"[Provider Chain] Provider {provider.value} passed health check")

                # Get client
                self.logger.debug(f"[LLM Service] Getting client for provider {provider}")
                client = await self._get_client(provider)
                self.logger.debug(f"[LLM Service] Client obtained for provider {provider}")

                # Prepare request
                request = LLMRequest(
                    task_type=task_type,
                    session_id=str(session.id),
                    template_data=template_data,
                    context={
                        "session_state": session.state.value,
                        "keyword": session.selectedKeyword,
                        "theme": session.themeId
                    }
                )

                # Execute request
                start_time = datetime.now(timezone.utc)
                self.logger.info(f"[Provider Chain] Executing {task_type.value} with {provider.value}")

                if task_type == LLMTaskType.KEYWORD_GENERATION:
                    response = await client.generate_keywords(request)
                elif task_type == LLMTaskType.AXIS_GENERATION:
                    response = await client.generate_axes(request)
                elif task_type == LLMTaskType.SCENARIO_GENERATION:
                    response = await client.generate_scenario(request)
                elif task_type == LLMTaskType.RESULT_ANALYSIS:
                    response = await client.analyze_results(request)
                else:
                    raise LLMServiceError(
                        f"Unsupported task type: {task_type}")

                end_time = datetime.now(timezone.utc)
                latency_ms = (end_time - start_time).total_seconds() * 1000

                # Update response with timing
                response.latency_ms = latency_ms

                # Record success metrics
                await record_llm_response(response)

                # Record in session
                session.record_llm_generation(
                    operation_type=operation_type,
                    provider=provider.value,
                    model_name=response.model_name,
                    tokens_used=response.tokens_used,
                    latency_ms=latency_ms,
                    cost_estimate=response.cost_estimate,
                    fallback_used=(attempt > 0),
                    retry_count=attempt
                )

                self.logger.info(f"[Provider Chain] ✓ Success with {provider.value} (attempt {attempt + 1})")
                return response

            except (RateLimitError, ProviderUnavailableError) as e:
                # Provider-level errors - try next provider
                last_error = e
                self._client_health[provider] = False
                self.logger.warning(f"[Provider Chain] ✗ {provider.value} failed: {type(e).__name__}: {e}")

                session.record_llm_error(
                    operation_type=operation_type,
                    provider=provider.value,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    retry_count=attempt
                )

                continue

            except (ValidationError, LLMClientError) as e:
                # Response validation or client errors - try next provider
                last_error = e
                self.logger.warning(f"[Provider Chain] ✗ {provider.value} failed: {type(e).__name__}: {e}")

                session.record_llm_error(
                    operation_type=operation_type,
                    provider=provider.value,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    retry_count=attempt
                )

                continue

            except Exception as e:
                # Unexpected errors - try next provider
                last_error = e
                self.logger.error(f"[Provider Chain] ✗ {provider.value} unexpected error: {type(e).__name__}: {e}")

                session.record_llm_error(
                    operation_type=operation_type,
                    provider=provider.value,
                    error_type="UnexpectedError",
                    error_message=str(e),
                    retry_count=attempt
                )

                continue

        # All providers failed
        self.logger.error(f"[Provider Chain] All {len(fallback_chain)} providers failed")
        raise AllProvidersFailedError(
            f"All LLM providers failed. Last error: {last_error}")

    async def _check_provider_health(self, provider: LLMProvider) -> bool:
        """Check if provider is healthy and available."""
        if provider == LLMProvider.MOCK:
            # Mockプロバイダーは常に利用可能
            self.logger.debug(f"[Health Check] Mock provider: always healthy")
            self._client_health[provider] = True
            return True
        
        elif provider == LLMProvider.OPENAI:
            try:
                # 軽量なOpenAI APIキー検証
                openai_config = self.config.get_provider_config(provider)
                if not openai_config or not openai_config.api_key:
                    self.logger.warning(f"[Health Check] OpenAI: API key not configured")
                    self._client_health[provider] = False
                    return False
                
                # 実際のAPI疎通確認（軽量）
                self.logger.debug(f"[Health Check] OpenAI: checking API connectivity")
                client = await self._get_client(provider)
                is_healthy = await client.health_check()
                self._client_health[provider] = is_healthy
                
                if is_healthy:
                    self.logger.debug(f"[Health Check] OpenAI: ✓ healthy")
                else:
                    self.logger.warning(f"[Health Check] OpenAI: ✗ unhealthy")
                
                return is_healthy
            except Exception as e:
                self.logger.error(f"[Health Check] OpenAI failed: {type(e).__name__}: {e}")
                self._client_health[provider] = False
                return False
        
        elif provider == LLMProvider.ANTHROPIC:
            try:
                # 軽量なAnthropic APIキー検証
                anthropic_config = self.config.get_provider_config(provider)
                if not anthropic_config or not anthropic_config.api_key:
                    self.logger.warning(f"[Health Check] Anthropic: API key not configured")
                    self._client_health[provider] = False
                    return False
                
                # 実際のAPI疎通確認（軽量）
                self.logger.debug(f"[Health Check] Anthropic: checking API connectivity")
                client = await self._get_client(provider)
                is_healthy = await client.health_check()
                self._client_health[provider] = is_healthy
                
                if is_healthy:
                    self.logger.debug(f"[Health Check] Anthropic: ✓ healthy")
                else:
                    self.logger.warning(f"[Health Check] Anthropic: ✗ unhealthy")
                
                return is_healthy
            except Exception as e:
                self.logger.error(f"[Health Check] Anthropic failed: {type(e).__name__}: {e}")
                self._client_health[provider] = False
                return False
        
        else:
            self.logger.error(f"[Health Check] Unknown provider: {provider}")
            return False

    async def generate_keywords(self, session: Session) -> List[str]:
        """
        Generate keyword candidates based on initial character.

        Args:
            session: Session with initialCharacter set

        Returns:
            List of 4 keyword candidates

        Raises:
            LLMServiceError: If generation fails
        """
        if not session.initialCharacter or session.initialCharacter.strip() == "":
            raise LLMServiceError("Session must have initialCharacter set")

        self.logger.info(f"[LLM Service] Starting keyword generation for: {session.initialCharacter}")
        
        # Debug: Log configuration state
        self.logger.debug(f"[LLM Service] Config providers: {list(self.config.providers.keys())}")
        self.logger.debug(f"[LLM Service] Primary provider: {self.config.primary_provider}")
        self.logger.debug(f"[LLM Service] Fallback chain: {self.config.get_fallback_chain()}")
        
        template_data = {
            "initial_character": session.initialCharacter,
            "count": 4
        }

        self.logger.debug(f"[LLM Service] Template data prepared: {template_data}")

        try:
            self.logger.debug(f"[LLM Service] About to call _execute_with_fallback")
            response = await self._execute_with_fallback(
                session=session,
                task_type=LLMTaskType.KEYWORD_GENERATION,
                template_data=template_data,
                operation_type="keyword_generation"
            )
            self.logger.debug(f"[LLM Service] _execute_with_fallback completed successfully")
            
            self.logger.info(f"[LLM Service] LLM keyword generation successful")

            keywords_data = response.content.get("keywords", [])
            if len(keywords_data) != 4:
                raise ValidationError(
                    f"Expected 4 keywords, got {len(keywords_data)}")

            # Extract word from new format: {"word": "愛情", "reading": "あいじょう"}
            keywords = []
            for keyword_obj in keywords_data:
                if isinstance(keyword_obj, dict) and "word" in keyword_obj:
                    keywords.append(keyword_obj["word"])
                elif isinstance(keyword_obj, str):
                    # Fallback for old format
                    keywords.append(keyword_obj)
                else:
                    raise ValidationError(
                        f"Invalid keyword format: {keyword_obj}")

            return keywords

        except AllProvidersFailedError as e:
            # Use fallback keywords
            self.logger.error(f"[LLM Service] All providers failed for keyword generation: {str(e)}")
            fallback_keywords = self.fallback_manager.get_keyword_candidates(
                session.initialCharacter
            )

            # Record fallback usage
            session.fallbackFlags.append("keyword_generation")
            self.logger.info(f"[LLM Service] Using fallback keywords: {fallback_keywords[:4]}")

            return fallback_keywords[:4]  # Ensure exactly 4 keywords
        except Exception as e:
            # Catch any other unexpected exceptions
            self.logger.error(f"[LLM Service] Unexpected error in keyword generation: {type(e).__name__}: {str(e)}")
            self.logger.debug(f"[LLM Service] Full exception details:", exc_info=True)
            
            # Use fallback keywords
            fallback_keywords = self.fallback_manager.get_keyword_candidates(
                session.initialCharacter
            )
            
            # Record fallback usage
            session.fallbackFlags.append("keyword_generation_error")
            self.logger.info(f"[LLM Service] Using fallback keywords due to error: {fallback_keywords[:4]}")
            
            return fallback_keywords[:4]

    async def generate_axes(self, session: Session) -> List[Axis]:
        """
        Generate evaluation axes based on selected keyword.

        Args:
            session: Session with selectedKeyword set

        Returns:
            List of 2-6 evaluation axes

        Raises:
            LLMServiceError: If generation fails
        """
        if not session.selectedKeyword:
            raise LLMServiceError("Session must have selectedKeyword set")

        template_data = {
            "keyword": session.selectedKeyword,
            "min_axes": 2,
            "max_axes": 6
        }

        try:
            response = await self._execute_with_fallback(
                session=session,
                task_type=LLMTaskType.AXIS_GENERATION,
                template_data=template_data,
                operation_type="axis_generation"
            )

            axes_data = response.content.get("axes", [])
            axes = [Axis(**axis_data) for axis_data in axes_data]

            if not (2 <= len(axes) <= 6):
                raise ValidationError(f"Expected 2-6 axes, got {len(axes)}")

            return axes

        except AllProvidersFailedError:
            # Use fallback axes
            fallback_axes = self.fallback_manager.get_default_axes()

            # Record fallback usage
            session.fallbackFlags.append("axis_generation")

            return fallback_axes[:4]  # Use max 4 fallback axes

    async def generate_scenario(
        self,
        session: Session,
        scene_index: int,
        previous_choices: Optional[List[Dict[str, Any]]] = None
    ) -> Scene:
        """
        Generate scenario and choices for specific scene.

        Args:
            session: Current session
            scene_index: Scene number (1-4)
            previous_choices: Previous user choices for continuity

        Returns:
            Generated scene with narrative and choices

        Raises:
            LLMServiceError: If generation fails
        """
        if not session.selectedKeyword:
            raise LLMServiceError("Session must have selectedKeyword set")

        if not session.axes:
            raise LLMServiceError("Session must have axes defined")

        template_data = {
            "keyword": session.selectedKeyword,
            "axes": [axis.dict() for axis in session.axes],
            "scene_index": scene_index,
            "theme": session.themeId,
            "previous_choices": previous_choices or []
        }

        try:
            response = await self._execute_with_fallback(
                session=session,
                task_type=LLMTaskType.SCENARIO_GENERATION,
                template_data=template_data,
                operation_type=f"scenario_generation_scene_{scene_index}"
            )

            content = response.content
            choices_data = content.get("choices", [])

            # Validate and create choices
            if len(choices_data) != 4:
                raise ValidationError(
                    f"Expected 4 choices, got {len(choices_data)}")

            choices = [Choice(**choice_data) for choice_data in choices_data]

            # Create scene
            scene = Scene(
                sceneIndex=scene_index,
                themeId=session.themeId,
                narrative=content.get("narrative", ""),
                choices=choices
            )

            return scene

        except AllProvidersFailedError:
            # Use fallback scenario
            fallback_scene = self.fallback_manager.get_fallback_scene(
                scene_index=scene_index,
                theme_id=session.themeId
            )

            # Record fallback usage
            session.fallbackFlags.append(
                f"scenario_generation_scene_{scene_index}")

            return fallback_scene

    async def analyze_results(self, session: Session) -> List[TypeProfile]:
        """
        Analyze user choices and generate personality insights.

        Args:
            session: Completed session with all choices

        Returns:
            List of type profiles

        Raises:
            LLMServiceError: If analysis fails
        """
        if session.state != SessionState.PLAY or len(session.choices) != 4:
            raise LLMServiceError(
                "Session must be in PLAY state with 4 choices completed")

        template_data = {
            "keyword": session.selectedKeyword,
            "axes": [axis.dict() for axis in session.axes],
            "scores": session.normalizedScores,
            "choices": [choice.dict() for choice in session.choices],
            "raw_scores": session.rawScores
        }

        try:
            response = await self._execute_with_fallback(
                session=session,
                task_type=LLMTaskType.RESULT_ANALYSIS,
                template_data=template_data,
                operation_type="result_analysis"
            )

            profiles_data = response.content.get("type_profiles", [])
            profiles = [TypeProfile(**profile_data)
                        for profile_data in profiles_data]

            if not profiles:
                raise ValidationError("No type profiles generated")

            return profiles

        except AllProvidersFailedError:
            # Use fallback analysis
            fallback_profiles = self.fallback_manager.get_fallback_type_profiles()

            # Record fallback usage
            session.fallbackFlags.append("result_analysis")

            return fallback_profiles

    async def get_service_status(self) -> Dict[str, Any]:
        """Get current service status and provider health."""
        provider_status = {}

        for provider in self.config.get_enabled_providers():
            try:
                is_healthy = await self._check_provider_health(provider)
                rate_limit_status = await self.metrics_tracker.get_provider_rate_limit_status(provider)

                provider_status[provider.value] = {
                    "healthy": is_healthy,
                    "rate_limit": rate_limit_status,
                    "configured": provider in self.config.providers
                }
            except Exception as e:
                provider_status[provider.value] = {
                    "healthy": False,
                    "error": str(e),
                    "configured": provider in self.config.providers
                }

        return {
            "primary_provider": self.config.primary_provider.value,
            "fallback_chain": [p.value for p in self.config.get_fallback_chain()],
            "provider_status": provider_status,
            "total_sessions": len(self.metrics_tracker._session_metrics),
            "service_healthy": any(
                status.get("healthy", False)
                for status in provider_status.values()
            )
        }


# Global service instance
_llm_service: Optional[ExternalLLMService] = None


def get_llm_service() -> ExternalLLMService:
    """Get global LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = ExternalLLMService()
    return _llm_service


async def initialize_llm_service(config: Optional[LLMConfig] = None) -> ExternalLLMService:
    """Initialize and return LLM service with optional custom config."""
    global _llm_service
    _llm_service = ExternalLLMService(config=config)
    return _llm_service
