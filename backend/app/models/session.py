"""
Core Pydantic schemas for NightLoom MVP diagnosis session.

Covers Session, Scene, Choice, AxisScore, TypeProfile as defined in data-model.md.
All models follow the ephemeral session design with state transitions: INIT -> PLAY -> RESULT.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SessionState(str, Enum):
    """Session state enum for tracking progression through diagnosis flow."""
    INIT = "INIT"
    PLAY = "PLAY"
    RESULT = "RESULT"


class Choice(BaseModel):
    """Individual choice option within a scene."""
    id: str = Field(..., description="Choice ID in format choice_{scene}_{index}")
    text: str = Field(..., max_length=80, description="Display text for the choice")
    weights: Dict[str, float] = Field(
        ..., 
        description="Evaluation axis weights, range -1.0 to 1.0"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "choice_1_1",
                "text": "慎重に検討して決める",
                "weights": {
                    "logic_emotion": 0.3,
                    "speed_caution": -0.5
                }
            }
        }


class Scene(BaseModel):
    """Scene containing narrative and 4 choice options."""
    sceneIndex: int = Field(..., ge=1, le=4, description="Scene number 1-4")
    themeId: str = Field(..., description="UI theme identifier")
    narrative: str = Field(..., description="Short story text readable in 5 seconds")
    choices: List[Choice] = Field(..., min_length=4, max_length=4, description="4 choice options")

    class Config:
        json_schema_extra = {
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
        }


class ChoiceRecord(BaseModel):
    """Record of user's choice for a specific scene."""
    sceneIndex: int = Field(..., ge=1, le=4)
    choiceId: str
    timestamp: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "sceneIndex": 1,
                "choiceId": "choice_1_1",
                "timestamp": "2025-10-15T09:30:00Z"
            }
        }


class Axis(BaseModel):
    """Evaluation axis definition."""
    id: str = Field(..., description="Unique axis identifier")
    name: str = Field(..., max_length=20, description="Axis name in English Title Case")
    description: str = Field(..., description="Axis description")
    direction: str = Field(..., description="Display label like '論理的 ⟷ 感情的'")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "logic_emotion",
                "name": "Logic vs Emotion",
                "description": "Balance between analytical and intuitive decision making",
                "direction": "論理的 ⟷ 感情的"
            }
        }


class AxisScore(BaseModel):
    """Score result for a specific axis."""
    axisId: str = Field(..., description="Reference to Axis.id")
    score: float = Field(..., ge=0, le=100, description="Normalized score 0-100")
    rawScore: float = Field(..., ge=-5.0, le=5.0, description="Raw weighted score")

    class Config:
        json_schema_extra = {
            "example": {
                "axisId": "logic_emotion",
                "score": 72.5,
                "rawScore": 2.3
            }
        }


class TypeProfile(BaseModel):
    """Generated type profile for user's decision-making pattern."""
    name: str = Field(..., max_length=14, description="Type name in 1-2 English words")
    description: str = Field(..., description="Type description")
    keywords: List[str] = Field(default_factory=list, description="Related behavior keywords")
    dominantAxes: List[str] = Field(..., min_length=2, max_length=2, description="Two primary axis IDs")
    polarity: str = Field(..., description="Polarity pattern like 'Hi-Lo'")
    meta: Optional[Dict] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Analytical Leader",
                "description": "決断力があり論理的思考を重視する傾向",
                "keywords": ["systematic", "decisive", "goal-oriented"],
                "dominantAxes": ["logic_emotion", "speed_caution"],
                "polarity": "Hi-Hi",
                "meta": {"cell": "A1", "isNeutral": False}
            }
        }


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
    keywordCandidates: List[str] = Field(..., min_length=4, max_length=4, description="4 keyword suggestions")
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
    
    # Timestamps
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    completedAt: Optional[datetime] = Field(None, description="Result completion timestamp")

    class Config:
        json_schema_extra = {
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
        }

    def can_transition_to_play(self) -> bool:
        """Check if session can transition from INIT to PLAY state."""
        return self.state == SessionState.INIT and self.selectedKeyword is not None

    def can_transition_to_result(self) -> bool:
        """Check if session can transition from PLAY to RESULT state."""
        return self.state == SessionState.PLAY and len(self.choices) == 4

    def is_completed(self) -> bool:
        """Check if session has been completed with results generated."""
        return self.state == SessionState.RESULT and self.completedAt is not None
