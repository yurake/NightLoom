"""
Core Pydantic schemas for NightLoom MVP diagnosis session.

Covers Session, Scene, Choice, AxisScore, TypeProfile as defined in data-model.md.
All models follow the ephemeral session design with state transitions: INIT -> PLAY -> RESULT.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class SessionState(str, Enum):
    """Session state enum for tracking progression through diagnosis flow."""
    INIT = "INIT"
    PLAY = "PLAY"
    RESULT = "RESULT"


class WeightEntry(BaseModel):
    """Single weight entry with axis ID, name and score."""
    id: str = Field(..., min_length=1, description="Axis ID like axis_1, axis_2")
    name: str = Field(..., min_length=1, description="Human-readable axis name")
    score: float = Field(..., ge=-1.0, le=1.0, description="Weight score")


class Choice(BaseModel):
    """Individual choice option within a scene."""
    id: str = Field(..., description="Choice ID in format choice_{scene}_{index}")
    text: str = Field(..., max_length=80, description="Display text for the choice")
    weights: Union[Dict[str, float], List[WeightEntry]] = Field(
        ...,
        description="Evaluation axis weights - dict format (legacy) or array format (preferred)"
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "choice_1_1",
            "text": "慎重に検討して決める",
            "weights": [
                {"id": "axis_1", "name": "Logic vs Emotion", "score": 0.3},
                {"id": "axis_2", "name": "Speed vs Caution", "score": -0.5},
                {"id": "axis_3", "name": "Individual vs Group", "score": 0.1},
                {"id": "axis_4", "name": "Stability vs Change", "score": 0.0}
            ]
        }
    })
    
    def get_weights_dict(self) -> Dict[str, float]:
        """Convert weights to dict format for backward compatibility."""
        import logging
        logger = logging.getLogger(__name__)
        
        if isinstance(self.weights, dict):
            logger.debug(f"[Choice.get_weights_dict] Using dict format: {self.weights}")
            return self.weights
        elif isinstance(self.weights, list):
            weights_dict = {entry.id: entry.score for entry in self.weights}
            logger.debug(f"[Choice.get_weights_dict] Converted from list to dict: {weights_dict}")
            return weights_dict
        else:
            logger.warning(f"[Choice.get_weights_dict] Unexpected weights type: {type(self.weights)}, returning empty dict")
            return {}
    
    def get_weights_array(self) -> List[WeightEntry]:
        """Convert weights to array format."""
        if isinstance(self.weights, list):
            return self.weights
        elif isinstance(self.weights, dict):
            # Convert dict to array format - need axis names from context
            return [
                WeightEntry(id=axis_id, name=axis_id.replace('_', ' ').title(), score=score)
                for axis_id, score in self.weights.items()
            ]
        else:
            return []


class Scene(BaseModel):
    """Scene containing narrative and 4 choice options."""
    sceneIndex: int = Field(..., ge=1, le=4, description="Scene number 1-4")
    themeId: str = Field(..., description="UI theme identifier")
    narrative: str = Field(..., description="Short story text readable in 5 seconds")
    choices: List[Choice] = Field(..., min_length=4, max_length=4, description="4 choice options")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "sceneIndex": 1,
            "themeId": "serene",
            "narrative": "あなたは重要な決断を迫られています。どのようにアプローチしますか？",
            "choices": [
                {
                    "id": "choice_1_1",
                    "text": "慎重に検討する",
                    "weights": {"logic_emotion": 0.3}
                }
            ]
        }
    })


class ChoiceRecord(BaseModel):
    """Record of user's choice for a specific scene."""
    sceneIndex: int = Field(..., ge=1, le=4)
    choiceId: str
    timestamp: datetime

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "sceneIndex": 1,
            "choiceId": "choice_1_1",
            "timestamp": "2025-10-15T09:30:00Z"
        }
    })


class Axis(BaseModel):
    """Evaluation axis definition."""
    id: str = Field(..., description="Unique axis identifier")
    name: str = Field(..., max_length=20, description="Axis name in English Title Case")
    description: str = Field(..., description="Axis description")
    direction: str = Field(..., description="Display label like '論理的 ⟷ 感情的'")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "logic_emotion",
            "name": "Logic vs Emotion",
            "description": "Balance between analytical and intuitive decision making",
            "direction": "論理的 ⟷ 感情的"
        }
    })


class AxisScore(BaseModel):
    """Score result for a specific axis."""
    axisId: str = Field(..., description="Reference to Axis.id")
    score: float = Field(..., ge=0, le=100, description="Normalized score 0-100")
    rawScore: float = Field(..., ge=-5.0, le=5.0, description="Raw weighted score")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "axisId": "logic_emotion",
            "score": 72.5,
            "rawScore": 2.3
        }
    })


class LLMGeneration(BaseModel):
    """LLM generation metadata and tracking."""
    provider: str = Field(..., description="LLM provider used (openai, anthropic, mock)")
    model_name: str = Field(..., description="Specific model used")
    tokens_used: Optional[int] = Field(None, description="Tokens consumed for generation")
    latency_ms: Optional[float] = Field(None, description="Generation latency in milliseconds")
    cost_estimate: Optional[float] = Field(None, description="Estimated cost in USD")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    fallback_used: bool = Field(default=False, description="Whether fallback was triggered")
    retry_count: int = Field(default=0, description="Number of retries before success")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "provider": "openai",
            "model_name": "gpt-4",
            "tokens_used": 150,
            "latency_ms": 1200.5,
            "cost_estimate": 0.0045,
            "generated_at": "2025-10-20T17:30:00Z",
            "fallback_used": False,
            "retry_count": 0
        }
    })


class TypeProfile(BaseModel):
    """Generated type profile for user's decision-making pattern."""
    name: str = Field(..., max_length=14, description="Type name in 1-2 English words")
    description: str = Field(..., description="Type description")
    keywords: List[str] = Field(default_factory=list, description="Related behavior keywords")
    dominantAxes: List[str] = Field(..., min_length=2, max_length=2, description="Two primary axis IDs")
    polarity: str = Field(..., description="Polarity pattern like 'Hi-Lo'")
    meta: Optional[Dict] = Field(default_factory=dict, description="Additional metadata")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "Analytical Leader",
            "description": "決断力があり論理的思考を重視する傾向",
            "keywords": ["systematic", "decisive", "goal-oriented"],
            "dominantAxes": ["logic_emotion", "speed_caution"],
            "polarity": "Hi-Hi",
            "meta": {"cell": "A1", "isNeutral": False}
        }
    })


class ThemeDescriptor(BaseModel):
    """UI theme configuration."""
    themeId: str = Field(..., description="Theme identifier")
    palette: Dict = Field(..., description="Color palette configuration")
    typography: Dict = Field(..., description="Font settings")
    assets: List[str] = Field(default_factory=list, description="Background/illustration assets")


class Session(BaseModel):
    """Core session model managing the entire diagnosis flow."""
    id: UUID = Field(..., description="Session UUID v4 identifier")
    state: SessionState = Field(default=SessionState.INIT, description="Current session state")
    
    # Bootstrap phase
    initialCharacter: str = Field(..., max_length=1, description="Initial hiragana character")
    keywordCandidates: List[str] = Field(default_factory=list, min_length=4, max_length=4, description="4 keyword suggestions")
    selectedKeyword: Optional[str] = Field(None, max_length=20, description="User-confirmed keyword")
    themeId: str = Field(..., description="UI theme for entire session")
    axes: List[Axis] = Field(default_factory=list, description="Evaluation axes for this session")
    
    # Play phase  
    scenes: List[Scene] = Field(default_factory=list, description="Scene data (1-4)")
    choices: List[ChoiceRecord] = Field(default_factory=list, description="User choice history")
    
    # Result phase
    rawScores: Dict[str, float] = Field(default_factory=dict, description="Cumulative raw scores")
    normalizedScores: Dict[str, float] = Field(default_factory=dict, description="Normalized 0-100 scores")
    typeProfiles: List[TypeProfile] = Field(default_factory=list, description="Generated type profiles")
    fallbackFlags: List[str] = Field(default_factory=list, description="Activated fallback types")
    
    # LLM Integration fields
    llmProvider: Optional[str] = Field(None, description="Primary LLM provider for this session")
    llmGenerations: Dict[str, LLMGeneration] = Field(
        default_factory=dict,
        description="LLM generation metadata keyed by operation type"
    )
    totalTokensUsed: int = Field(default=0, description="Total tokens used across all LLM calls")
    totalCostEstimate: float = Field(default=0.0, description="Total estimated cost in USD")
    llmErrors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Record of LLM errors and fallbacks"
    )
    
    # Timestamps
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completedAt: Optional[datetime] = Field(None, description="Result completion timestamp")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "state": "INIT",
            "initialCharacter": "あ",
            "keywordCandidates": ["愛", "冒険", "挑戦", "成長"],
            "selectedKeyword": None,
            "themeId": "serene",
            "scenes": [],
            "choices": [],
            "rawScores": {},
            "normalizedScores": {},
            "typeProfiles": [],
            "fallbackFlags": [],
            "createdAt": "2025-10-15T09:30:00Z",
            "completedAt": None
        }
    })

    def can_transition_to_play(self) -> bool:
        """Check if session can transition from INIT to PLAY state."""
        return self.state == SessionState.INIT and self.selectedKeyword is not None

    def can_transition_to_result(self) -> bool:
        """Check if session can transition from PLAY to RESULT state."""
        return self.state == SessionState.PLAY and len(self.choices) == 4

    def is_completed(self) -> bool:
        """Check if session has been completed with results generated."""
        return self.state == SessionState.RESULT and self.completedAt is not None
    
    def record_llm_generation(
        self,
        operation_type: str,
        provider: str,
        model_name: str,
        tokens_used: Optional[int] = None,
        latency_ms: Optional[float] = None,
        cost_estimate: Optional[float] = None,
        fallback_used: bool = False,
        retry_count: int = 0
    ) -> None:
        """Record LLM generation metadata for tracking."""
        generation = LLMGeneration(
            provider=provider,
            model_name=model_name,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            cost_estimate=cost_estimate,
            fallback_used=fallback_used,
            retry_count=retry_count
        )
        
        self.llmGenerations[operation_type] = generation
        
        # Update session totals
        if tokens_used:
            self.totalTokensUsed += tokens_used
        if cost_estimate:
            self.totalCostEstimate += cost_estimate
        
        # Set primary provider if not set
        if not self.llmProvider:
            self.llmProvider = provider
    
    def record_llm_error(
        self,
        operation_type: str,
        provider: str,
        error_type: str,
        error_message: str,
        retry_count: int = 0
    ) -> None:
        """Record LLM error for monitoring and debugging."""
        error_record = {
            "operation_type": operation_type,
            "provider": provider,
            "error_type": error_type,
            "error_message": error_message,
            "retry_count": retry_count,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self.llmErrors.append(error_record)
    
    def get_llm_usage_summary(self) -> Dict[str, Any]:
        """Get summary of LLM usage for this session."""
        provider_breakdown = {}
        operation_breakdown = {}
        
        for operation, generation in self.llmGenerations.items():
            # Provider breakdown
            if generation.provider not in provider_breakdown:
                provider_breakdown[generation.provider] = {
                    "tokens": 0, "cost": 0.0, "operations": 0, "fallbacks": 0
                }
            
            provider_stats = provider_breakdown[generation.provider]
            provider_stats["operations"] += 1
            if generation.tokens_used:
                provider_stats["tokens"] += generation.tokens_used
            if generation.cost_estimate:
                provider_stats["cost"] += generation.cost_estimate
            if generation.fallback_used:
                provider_stats["fallbacks"] += 1
            
            # Operation breakdown
            operation_breakdown[operation] = {
                "provider": generation.provider,
                "model": generation.model_name,
                "tokens": generation.tokens_used or 0,
                "cost": generation.cost_estimate or 0.0,
                "latency_ms": generation.latency_ms,
                "fallback_used": generation.fallback_used,
                "retry_count": generation.retry_count,
                "generated_at": generation.generated_at.isoformat()
            }
        
        return {
            "primary_provider": self.llmProvider,
            "total_tokens": self.totalTokensUsed,
            "total_cost": self.totalCostEstimate,
            "total_operations": len(self.llmGenerations),
            "total_errors": len(self.llmErrors),
            "provider_breakdown": provider_breakdown,
            "operation_breakdown": operation_breakdown,
            "has_fallbacks": any(g.fallback_used for g in self.llmGenerations.values()),
            "session_duration": (
                (self.completedAt - self.createdAt).total_seconds()
                if self.completedAt else
                (datetime.now(timezone.utc) - self.createdAt).total_seconds()
            )
        }
