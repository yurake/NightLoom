
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
from ..clients.anthropic_client import AnthropicCreditError, AnthropicAccountError
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

                # Add fallback flag if not using primary provider
                if attempt > 0:
                    fallback_flag = f"{operation_type}_fallback_provider"
                    if fallback_flag not in session.fallbackFlags:
                        session.fallbackFlags.append(fallback_flag)
                        self.logger.info(f"[Provider Chain] Added fallback flag: {fallback_flag}")

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

            except (AnthropicCreditError, AnthropicAccountError) as e:
                # Account-level errors (credit/auth) - try next provider immediately
                last_error = e
                self._client_health[provider] = False
                self.logger.info(f"[Provider Chain] ✗ {provider.value} account issue - switching to next provider: {type(e).__name__}: {e}")

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
            self.logger.info(f"[LLM Service] Starting scenario generation for scene {scene_index}")
            self.logger.debug(f"[LLM Service] Template  {template_data}")
            
            response = await self._execute_with_fallback(
                session=session,
                task_type=LLMTaskType.SCENARIO_GENERATION,
                template_data=template_data,
                operation_type=f"scenario_generation_scene_{scene_index}"
            )

            content = response.content
            self.logger.info(f"[LLM Service] Received scenario response: {content}")
            
            # Check if we have the expected scene structure
            if "scene" not in content:
                self.logger.error(f"[LLM Service] Missing 'scene' field in response: {content}")
                raise ValidationError("Response missing 'scene' field")
            
            scene_data = content["scene"]
            
            # Check narrative field specifically
            narrative = scene_data.get("narrative", "")
            if not narrative or not isinstance(narrative, str) or not narrative.strip():
                self.logger.error(f"[LLM Service] Invalid or empty narrative: '{narrative}'")
                self.logger.error(f"[LLM Service] Full scene data: {scene_data}")
                raise ValidationError("Scene narrative is empty or invalid")
            
            choices_data = scene_data.get("choices", [])

            # Validate and create choices
            if len(choices_data) != 4:
                self.logger.error(f"[LLM Service] Expected 4 choices, got {len(choices_data)}")
                raise ValidationError(
                    f"Expected 4 choices, got {len(choices_data)}")

            choices = [Choice(**choice_data) for choice_data in choices_data]

            # T039: Add choice weight validation and balancing
            validated_choices = await self._validate_and_balance_choice_weights(
                choices, session.axes, scene_index
            )

            # Create scene
            scene = Scene(
                sceneIndex=scene_index,
                themeId=session.themeId,
                narrative=narrative.strip(),
                choices=validated_choices
            )
            
            self.logger.info(f"[LLM Service] Successfully created scene {scene_index} with narrative length: {len(narrative)}")
            return scene

        except AllProvidersFailedError as e:
            # Use fallback scenario
            self.logger.error(f"[LLM Service] All providers failed for scenario generation scene {scene_index}: {e}")
            from ..services.fallback_assets import get_fallback_scene
            fallback_scene = get_fallback_scene(
                scene_index=scene_index,
                theme_id=session.themeId
            )

            # Record fallback usage
            session.fallbackFlags.append(
                f"scenario_generation_scene_{scene_index}")
            
            self.logger.info(f"[LLM Service] Using fallback scenario for scene {scene_index}")
            return fallback_scene
        
        except (ValidationError, ValueError) as e:
            # Validation errors - try fallback
            self.logger.error(f"[LLM Service] Scenario validation failed for scene {scene_index}: {e}")
            from ..services.fallback_assets import get_fallback_scene
            fallback_scene = get_fallback_scene(
                scene_index=scene_index,
                theme_id=session.themeId
            )

            # Record fallback usage with error info
            session.fallbackFlags.append(
                f"scenario_generation_scene_{scene_index}_validation_error")
            
            self.logger.info(f"[LLM Service] Using fallback scenario due to validation error for scene {scene_index}")
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
            
            # T049: Add personality type validation and formatting
            validated_profiles = []
            for i, profile_data in enumerate(profiles_data):
                try:
                    # Validate and format profile data
                    formatted_profile = await self._validate_and_format_type_profile(
                        profile_data, i + 1, session
                    )
                    validated_profiles.append(formatted_profile)
                except Exception as validation_error:
                    self.logger.warning(f"[Type Profile Validation] Profile {i+1} validation failed: {validation_error}")
                    # Skip invalid profiles but continue with others
                    continue
            
            if not validated_profiles:
                raise ValidationError("No valid type profiles generated after validation")

            return validated_profiles

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

    async def _validate_and_balance_choice_weights(
        self,
        choices: List[Choice],
        axes: List[Axis],
        scene_index: int
    ) -> List[Choice]:
       """
       T039: Validate and balance choice weights for optimal distribution.
       
       Args:
           choices: Generated choices with weights
           axes: Current session axes
           scene_index: Scene number for logging
           
       Returns:
           Validated and balanced choices
       """
       self.logger.info(f"[Choice Validation] Validating weights for scene {scene_index}")
       
       # Create axis ID set for validation
       axis_ids = {axis.id for axis in axes}
       validated_choices = []
       
       for i, choice in enumerate(choices):
           validated_choice = choice
           needs_rebalancing = False
           
           # Validate weight completeness
           missing_axes = axis_ids - set(choice.weights.keys())
           if missing_axes:
               self.logger.warning(f"[Choice Validation] Choice {i+1} missing weights for axes: {missing_axes}")
               # Add missing weights with neutral value
               for axis_id in missing_axes:
                   validated_choice.weights[axis_id] = 0.0
               needs_rebalancing = True
           
           # Validate weight ranges
           for axis_id, weight in validated_choice.weights.items():
               if not isinstance(weight, (int, float)):
                   self.logger.warning(f"[Choice Validation] Choice {i+1} weight for {axis_id} is not numeric: {weight}")
                   validated_choice.weights[axis_id] = 0.0
                   needs_rebalancing = True
               elif not (-1.0 <= weight <= 1.0):
                   self.logger.warning(f"[Choice Validation] Choice {i+1} weight for {axis_id} out of range: {weight}")
                   # Clamp to valid range
                   validated_choice.weights[axis_id] = max(-1.0, min(1.0, float(weight)))
                   needs_rebalancing = True
           
           if needs_rebalancing:
               self.logger.info(f"[Choice Validation] Rebalanced choice {i+1}")
           
           validated_choices.append(validated_choice)
       
       # Check overall balance across all choices
       balanced_choices = await self._balance_choice_distribution(validated_choices, axes, scene_index)
       
       self.logger.info(f"[Choice Validation] Completed validation for scene {scene_index}")
       return balanced_choices
   
    async def _balance_choice_distribution(
        self,
        choices: List[Choice],
        axes: List[Axis],
        scene_index: int
    ) -> List[Choice]:
       """
       Ensure choices provide good distribution across axis spectrum.
       
       Args:
           choices: Validated choices
           axes: Session axes
           scene_index: Scene number for logging
           
       Returns:
           Balanced choices with improved distribution
       """
       # Calculate current distribution
       axis_totals = {}
       for axis in axes:
           axis_totals[axis.id] = sum(choice.weights.get(axis.id, 0.0) for choice in choices)
       
       # Check if rebalancing is needed
       rebalance_needed = False
       for axis_id, total in axis_totals.items():
           # If all choices are heavily skewed in one direction, rebalance
           if abs(total) > 3.0:  # Threshold for extreme imbalance
               rebalance_needed = True
               self.logger.warning(f"[Choice Balance] Scene {scene_index} axis {axis_id} heavily imbalanced: {total}")
       
       if not rebalance_needed:
           return choices
       
       # Apply gentle rebalancing
       balanced_choices = []
       for i, choice in enumerate(choices):
           balanced_choice = Choice(
               id=choice.id,
               text=choice.text,
               weights=choice.weights.copy()
           )
           
           # Apply mild counter-balancing for extreme cases
           for axis_id, total in axis_totals.items():
               if abs(total) > 3.0:
                   current_weight = balanced_choice.weights.get(axis_id, 0.0)
                   # Slightly reduce extreme weights to improve balance
                   if total > 3.0 and current_weight > 0.5:
                       balanced_choice.weights[axis_id] = current_weight * 0.8
                   elif total < -3.0 and current_weight < -0.5:
                       balanced_choice.weights[axis_id] = current_weight * 0.8
           
           balanced_choices.append(balanced_choice)
       
       self.logger.info(f"[Choice Balance] Applied rebalancing for scene {scene_index}")
       return balanced_choices
   
    async def _validate_and_format_type_profile(
       self,
       profile_data: Dict[str, Any],
       profile_index: int,
       session: Session
   ) -> TypeProfile:
       """
       T049: Validate and format type profile data.
       
       Args:
           profile_ Raw profile data from LLM
           profile_index: Profile number for error reporting
           session: Current session for context
           
       Returns:
           Validated and formatted TypeProfile
           
       Raises:
           ValidationError: If profile data is invalid
       """
       self.logger.debug(f"[Type Profile Validation] Validating profile {profile_index}")
       
       # Create a copy for modification
       formatted_data = profile_data.copy()
       
       # Validate required fields (keywords is optional and will be auto-generated if missing)
       required_fields = ["typeName", "description", "dominantAxes", "polarity"]
       for field in required_fields:
           if field not in formatted_data:
               raise ValidationError(f"Profile {profile_index} missing required field: {field}")
       
       # Validate and format name
       name = str(formatted_data["typeName"]).strip()
       if not name:
           raise ValidationError(f"Profile {profile_index} name cannot be empty")
       if len(name) > 14:
           # Truncate name but keep it meaningful
           name = name[:11] + "..."
           self.logger.warning(f"[Type Profile Validation] Truncated profile {profile_index} name to: {name}")
       formatted_data["name"] = name
       # Also keep typeName for compatibility
       formatted_data["typeName"] = name
       
       # Validate and format description
       description = str(formatted_data["description"]).strip()
       if not description:
           raise ValidationError(f"Profile {profile_index} description cannot be empty")
       if len(description) < 10:
           # Enhance short descriptions
           keyword_context = session.selectedKeyword if session.selectedKeyword else "特性"
           description = f"{description} {keyword_context}を重視する傾向があります。"
           self.logger.info(f"[Type Profile Validation] Enhanced short description for profile {profile_index}")
       formatted_data["description"] = description
       
       # Validate and format keywords - handle missing keywords field
       keywords = formatted_data.get("keywords", [])
       if not isinstance(keywords, list):
           keywords = []
       keywords = [str(k).strip() for k in keywords if k and str(k).strip()]
       if len(keywords) < 2:
           # Add default keywords based on session context
           default_keywords = self._generate_default_keywords(session)
           keywords.extend(default_keywords[:2 - len(keywords)])
           self.logger.info(f"[Type Profile Validation] Added default keywords for profile {profile_index}")
       formatted_data["keywords"] = keywords[:5]  # Limit to 5 keywords
       
       # Validate and format dominant axes
       dominant_axes = formatted_data["dominantAxes"]
       if not isinstance(dominant_axes, list):
           dominant_axes = []
       
       # Validate axes exist in session
       session_axis_ids = {axis.id for axis in session.axes}
       valid_axes = [axis_id for axis_id in dominant_axes if axis_id in session_axis_ids]
       
       if len(valid_axes) < 2:
           # Auto-select dominant axes from scores
           if session.normalizedScores:
               sorted_axes = sorted(
                   session.normalizedScores.items(),
                   key=lambda x: abs(x[1] - 50.0),  # Distance from neutral
                   reverse=True
               )
               auto_axes = [axis_id for axis_id, _ in sorted_axes[:2]]
               valid_axes = auto_axes[:2]
               self.logger.info(f"[Type Profile Validation] Auto-selected dominant axes for profile {profile_index}: {valid_axes}")
       
       formatted_data["dominantAxes"] = valid_axes[:2]  # Exactly 2 axes
       
       # Validate and format polarity
       polarity = str(formatted_data["polarity"]).strip()
       valid_polarities = ["Hi-Hi", "Hi-Lo", "Lo-Hi", "Lo-Lo", "Mid-Mid", "Hi-Mid", "Mid-Hi", "Lo-Mid", "Mid-Lo"]
       if polarity not in valid_polarities:
           # Auto-determine polarity from scores
           if session.normalizedScores and len(valid_axes) >= 2:
               axis1_score = session.normalizedScores.get(valid_axes[0], 50.0)
               axis2_score = session.normalizedScores.get(valid_axes[1], 50.0)
               
               def score_to_level(score):
                   if score > 70:
                       return "Hi"
                   elif score < 30:
                       return "Lo"
                   else:
                       return "Mid"
               
               polarity = f"{score_to_level(axis1_score)}-{score_to_level(axis2_score)}"
               self.logger.info(f"[Type Profile Validation] Auto-determined polarity for profile {profile_index}: {polarity}")
           else:
               polarity = "Mid-Mid"  # Safe default
       
       formatted_data["polarity"] = polarity
       
       # Ensure meta field exists
       if "meta" not in formatted_data:
           formatted_data["meta"] = {}
       
       # Add validation metadata
       formatted_data["meta"]["validated"] = True
       formatted_data["meta"]["validation_timestamp"] = datetime.now(timezone.utc).isoformat()
       
       # Create and return TypeProfile
       try:
           validated_profile = TypeProfile(**formatted_data)
           self.logger.debug(f"[Type Profile Validation] Successfully validated profile {profile_index}")
           return validated_profile
       except Exception as e:
           raise ValidationError(f"Profile {profile_index} failed TypeProfile creation: {str(e)}")
   
    def _generate_default_keywords(self, session: Session) -> List[str]:
        """Generate default keywords based on session context."""
        keyword_mappings = {
            "愛": ["caring", "empathetic", "nurturing"],
            "冒険": ["adventurous", "bold", "exploratory"],
            "挑戦": ["challenging", "determined", "ambitious"],
            "成長": ["growth-oriented", "developing", "progressive"],
            "希望": ["optimistic", "hopeful", "positive"],
            "協力": ["collaborative", "team-oriented", "supportive"]
        }
        
        if session.selectedKeyword and session.selectedKeyword in keyword_mappings:
            return keyword_mappings[session.selectedKeyword]
        
        # Generic defaults based on score patterns
        if session.normalizedScores:
            logic_score = session.normalizedScores.get("logic_emotion", 50.0)
            speed_score = session.normalizedScores.get("speed_caution", 50.0)
            
            keywords = []
            if logic_score > 60:
                keywords.append("analytical")
            if logic_score < 40:
                keywords.append("intuitive")
            if speed_score > 60:
                keywords.append("decisive")
            if speed_score < 40:
                keywords.append("thoughtful")
            
            return keywords
        
        return ["balanced", "adaptable", "thoughtful"]


# Global service instance
_llm_service: Optional[ExternalLLMService] = None


def get_llm_service() -> ExternalLLMService:
    """Get global LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = ExternalLLMService()
    return _llm_service


class AxisValidator:
    """Axis validation utility class."""
    
    def validate_axis(self, axis: Dict[str, Any], index: int) -> None:
        """Validate single axis structure and content."""
        if not isinstance(axis, dict):
            raise ValidationError(f"Axis {index} must be an object")
        
        # Check required fields
        required_fields = ["id", "name", "description", "direction"]
        for field in required_fields:
            if field not in axis:
                raise ValidationError(f"Axis {index} missing required field: {field}")
            
            if not isinstance(axis[field], str):
                raise ValidationError(f"Axis {index} field '{field}' must be a string")
            
            if not axis[field].strip():
                raise ValidationError(f"Axis {index} field '{field}' cannot be empty")
        
        # Validate ID format (alphanumeric + underscore)
        axis_id = axis["id"]
        if not axis_id.replace("_", "").replace("-", "").isalnum():
            if not all(c.isalnum() or c == "_" for c in axis_id):
                raise ValidationError(f"Axis {index} ID contains invalid characters")
        
        # Validate direction format (must contain ⟷)
        direction = axis["direction"]
        if "⟷" not in direction:
            raise ValidationError(f"Axis {index} direction must contain '⟷' separator")
        
        # Validate length constraints
        if len(axis["name"]) > 50:
            raise ValidationError(f"Axis {index} name too long (max 50 characters)")
        
        if len(axis["description"]) > 200:
            raise ValidationError(f"Axis {index} description too long (max 200 characters)")
    
    def validate_axes_collection(self, axes: List[Dict[str, Any]]) -> None:
        """Validate collection of axes."""
        if not isinstance(axes, list):
            raise ValidationError("Axes must be a list")
        
        # Check count constraints
        if len(axes) < 2 or len(axes) > 6:
            raise ValidationError(f"Expected 2-6 axes, got {len(axes)}")
        
        # Validate each axis
        axis_ids = set()
        for i, axis in enumerate(axes):
            self.validate_axis(axis, i + 1)
            
            # Check for duplicate IDs
            axis_id = axis["id"]
            if axis_id in axis_ids:
                raise ValidationError(f"Duplicate axis ID: {axis_id}")
            axis_ids.add(axis_id)


async def initialize_llm_service(config: Optional[LLMConfig] = None) -> ExternalLLMService:
    """Initialize and return LLM service with optional custom config."""
    global _llm_service
    _llm_service = ExternalLLMService(config=config)
    return _llm_service
