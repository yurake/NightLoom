"""
Abstract LLM client interface for NightLoom.

Defines the contract for all LLM providers (OpenAI, Anthropic, Mock) 
with standardized request/response formats and error handling.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum

from ..models.llm_config import LLMProvider, ProviderConfig


class LLMTaskType(str, Enum):
    """Types of LLM tasks supported by NightLoom."""
    KEYWORD_GENERATION = "keyword_generation"
    AXIS_GENERATION = "axis_generation"
    SCENARIO_GENERATION = "scenario_generation"
    RESULT_ANALYSIS = "result_analysis"


@dataclass
class LLMRequest:
    """Standardized request format for all LLM operations."""
    task_type: LLMTaskType
    session_id: str
    template_data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    
    def __post_init__(self):
        """Validate request data."""
        if not self.session_id:
            raise ValueError("session_id is required")
        if not self.template_data:
            raise ValueError("template_data is required")


@dataclass
class LLMResponse:
    """Standardized response format for all LLM operations."""
    task_type: LLMTaskType
    session_id: str
    content: Dict[str, Any]
    provider: LLMProvider
    model_name: str
    tokens_used: Optional[int] = None
    latency_ms: Optional[float] = None
    cost_estimate: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        """Set default timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


@dataclass
class LLMError:
    """Standardized error information for LLM failures."""
    provider: LLMProvider
    error_type: str
    error_message: str
    session_id: str
    task_type: LLMTaskType
    timestamp: datetime
    retry_count: int = 0
    is_retryable: bool = False


class LLMClientError(Exception):
    """Base exception for LLM client errors."""
    def __init__(self, message: str, error_info: Optional[LLMError] = None):
        super().__init__(message)
        self.error_info = error_info


class ValidationError(LLMClientError):
    """Raised when LLM response fails validation."""
    pass


class RateLimitError(LLMClientError):
    """Raised when rate limit is exceeded."""
    pass


class ProviderUnavailableError(LLMClientError):
    """Raised when LLM provider is unavailable."""
    pass


class BaseLLMClient(ABC):
    """Abstract base class for all LLM clients."""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.provider = config.provider
        self._metrics = {}
    
    @abstractmethod
    async def generate_keywords(self, request: LLMRequest) -> LLMResponse:
        """
        Generate keyword candidates based on initial character.
        
        Args:
            request: LLMRequest with template_data containing:
                - initial_character: str (hiragana character)
                - count: int (number of keywords to generate, default 4)
        
        Returns:
            LLMResponse with content containing:
                - keywords: List[str] (generated keywords)
        """
        pass
    
    @abstractmethod
    async def generate_axes(self, request: LLMRequest) -> LLMResponse:
        """
        Generate evaluation axes based on selected keyword.
        
        Args:
            request: LLMRequest with template_data containing:
                - keyword: str (selected keyword)
                - min_axes: int (minimum axes count, default 2)
                - max_axes: int (maximum axes count, default 6)
        
        Returns:
            LLMResponse with content containing:
                - axes: List[Dict] with id, name, description, direction
        """
        pass
    
    @abstractmethod
    async def generate_scenario(self, request: LLMRequest) -> LLMResponse:
        """
        Generate scenario and choices for a specific scene.
        
        Args:
            request: LLMRequest with template_data containing:
                - keyword: str (session keyword)
                - axes: List[Dict] (evaluation axes)
                - scene_index: int (1-4)
                - previous_choices: List[Dict] (optional, for continuity)
        
        Returns:
            LLMResponse with content containing:
                - narrative: str (scenario text)
                - choices: List[Dict] with id, text, weights
        """
        pass
    
    @abstractmethod
    async def analyze_results(self, request: LLMRequest) -> LLMResponse:
        """
        Analyze user choices and generate personality insights.
        
        Args:
            request: LLMRequest with template_data containing:
                - keyword: str (session keyword)
                - axes: List[Dict] (evaluation axes)
                - scores: Dict[str, float] (axis scores)
                - choices: List[Dict] (user choice history)
        
        Returns:
            LLMResponse with content containing:
                - type_profiles: List[Dict] with name, description, keywords, etc.
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if provider is available and healthy.
        
        Returns:
            bool: True if provider is healthy, False otherwise
        """
        pass
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics for monitoring."""
        return self._metrics.copy()
    
    def reset_metrics(self) -> None:
        """Reset client metrics."""
        self._metrics.clear()
    
    async def _validate_response(self, response: LLMResponse) -> bool:
        """
        Validate LLM response format and content.
        
        Args:
            response: LLMResponse to validate
            
        Returns:
            bool: True if response is valid
            
        Raises:
            ValidationError: If response fails validation
        """
        if not response.content:
            raise ValidationError("Empty response content")
        
        # Task-specific validation
        if response.task_type == LLMTaskType.KEYWORD_GENERATION:
            return await self._validate_keywords(response.content)
        elif response.task_type == LLMTaskType.AXIS_GENERATION:
            return await self._validate_axes(response.content)
        elif response.task_type == LLMTaskType.SCENARIO_GENERATION:
            return await self._validate_scenario(response.content)
        elif response.task_type == LLMTaskType.RESULT_ANALYSIS:
            return await self._validate_results(response.content)
        
        return True
    
    async def _validate_keywords(self, content: Dict[str, Any]) -> bool:
        """Validate keyword generation response."""
        keywords = content.get("keywords", [])
        if not isinstance(keywords, list) or len(keywords) != 4:
            raise ValidationError("Must generate exactly 4 keywords")
        
        for i, keyword in enumerate(keywords):
            # Support both old format (strings) and new format (objects with word/reading)
            if isinstance(keyword, str):
                if len(keyword.strip()) == 0:
                    raise ValidationError(f"Keyword {i+1} must be non-empty string")
            elif isinstance(keyword, dict):
                if "word" not in keyword or "reading" not in keyword:
                    raise ValidationError(f"Keyword {i+1} must have 'word' and 'reading' fields")
                if not isinstance(keyword["word"], str) or len(keyword["word"].strip()) == 0:
                    raise ValidationError(f"Keyword {i+1} 'word' must be non-empty string")
                if not isinstance(keyword["reading"], str) or len(keyword["reading"].strip()) == 0:
                    raise ValidationError(f"Keyword {i+1} 'reading' must be non-empty string")
            else:
                raise ValidationError(f"Keyword {i+1} must be string or object with 'word'/'reading' fields")
        
        return True
    
    async def _validate_axes(self, content: Dict[str, Any]) -> bool:
        """Validate axis generation response."""
        axes = content.get("axes", [])
        if not isinstance(axes, list) or not (2 <= len(axes) <= 6):
            raise ValidationError("Must generate 2-6 evaluation axes")
        
        for axis in axes:
            required_fields = ["id", "name", "description", "direction"]
            if not all(field in axis for field in required_fields):
                raise ValidationError(f"Axis missing required fields: {required_fields}")
        
        return True
    
    async def _validate_scenario(self, content: Dict[str, Any]) -> bool:
        """Validate scenario generation response."""
        # Handle both old format (direct narrative) and new format (scene.narrative)
        narrative = None
        choices = None
        
        if "scene" in content:
            # New format: content.scene.narrative
            scene = content["scene"]
            if isinstance(scene, dict):
                narrative = scene.get("narrative", "")
                choices = scene.get("choices", [])
        else:
            # Old format: content.narrative (fallback compatibility)
            narrative = content.get("narrative", "")
            choices = content.get("choices", [])
        
        if not narrative or not isinstance(narrative, str) or not narrative.strip():
            raise ValidationError("Scenario must have non-empty narrative")
        
        if not isinstance(choices, list) or len(choices) != 4:
            raise ValidationError("Must generate exactly 4 choices")
        
        for choice in choices:
            required_fields = ["id", "text", "weights"]
            if not all(field in choice for field in required_fields):
                raise ValidationError(f"Choice missing required fields: {required_fields}")
        
        return True
    
    async def _validate_results(self, content: Dict[str, Any]) -> bool:
        """Validate result analysis response."""
        type_profiles = content.get("type_profiles", [])
        if not isinstance(type_profiles, list) or len(type_profiles) == 0:
            raise ValidationError("Must generate at least one type profile")
        
        for profile in type_profiles:
            required_fields = ["name", "description"]
            if not all(field in profile for field in required_fields):
                raise ValidationError(f"Type profile missing required fields: {required_fields}")
        
        return True
    
    def _update_metrics(self, operation: str, **kwargs) -> None:
        """Update client metrics."""
        if operation not in self._metrics:
            self._metrics[operation] = {
                "count": 0,
                "total_latency_ms": 0,
                "total_tokens": 0,
                "errors": 0
            }
        
        metrics = self._metrics[operation]
        metrics["count"] += 1
        
        if "latency_ms" in kwargs:
            metrics["total_latency_ms"] += kwargs["latency_ms"]
        if "tokens_used" in kwargs:
            metrics["total_tokens"] += kwargs["tokens_used"]
        if "error" in kwargs:
            metrics["errors"] += 1
