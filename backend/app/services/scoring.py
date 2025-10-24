"""
Scoring service for NightLoom MVP diagnosis evaluation.

Calculates axis scores from user choices and normalizes them for display.
Implements the scoring algorithm defined in data-model.md.
"""

from typing import Dict, List
from app.models.session import Session, Choice


class ScoringService:
    """Service for calculating and normalizing diagnosis scores."""
    
    def __init__(self):
        self.raw_score_range = (-5.0, 5.0)
        self.normalized_range = (0.0, 100.0)
    
    async def calculate_scores(self, session: Session) -> Dict[str, float]:
        """
        Calculate raw axis scores from user choices.
        
        Args:
            session: Completed session with all choices made
            
        Returns:
            Dictionary mapping axis_id -> raw_score (-5.0 to 5.0)
        """
        if len(session.choices) != 4:
            raise ValueError(f"Expected 4 choices, got {len(session.choices)}")
        
        # Initialize score accumulator
        scores: Dict[str, float] = {}
        
        # Process each choice
        for choice_record in session.choices:
            # Find the scene and choice
            scene = None
            for s in session.scenes:
                if s.sceneIndex == choice_record.sceneIndex:
                    scene = s
                    break
            
            if not scene:
                raise ValueError(f"Scene {choice_record.sceneIndex} not found")
            
            # Find the selected choice
            selected_choice = None
            for choice in scene.choices:
                if choice.id == choice_record.choiceId:
                    selected_choice = choice
                    break
            
            if not selected_choice:
                raise ValueError(f"Choice {choice_record.choiceId} not found in scene {choice_record.sceneIndex}")
            
            # Add weights to scores
            choice_weights = selected_choice.get_weights_dict()
            for axis_id, weight in choice_weights.items():
                if axis_id not in scores:
                    scores[axis_id] = 0.0
                scores[axis_id] += weight
        
        # Clamp scores to valid range
        for axis_id in scores:
            scores[axis_id] = max(
                self.raw_score_range[0], 
                min(self.raw_score_range[1], scores[axis_id])
            )
        
        return scores
    
    async def normalize_scores(self, raw_scores: Dict[str, float]) -> Dict[str, float]:
        """
        Normalize raw scores to 0-100 range for display.
        
        Args:
            raw_scores: Raw scores in -5.0 to 5.0 range
            
        Returns:
            Dictionary mapping axis_id -> normalized_score (0-100)
        """
        normalized = {}
        
        for axis_id, raw_score in raw_scores.items():
            # Linear transformation from [-5, 5] to [0, 100]
            # Formula: (raw_score - min_raw) / (max_raw - min_raw) * (max_norm - min_norm) + min_norm
            min_raw, max_raw = self.raw_score_range
            min_norm, max_norm = self.normalized_range
            
            normalized_score = ((raw_score - min_raw) / (max_raw - min_raw)) * (max_norm - min_norm) + min_norm
            
            # Round to 1 decimal place for display
            normalized[axis_id] = round(normalized_score, 1)
        
        return normalized
    
    def get_score_interpretation(self, axis_id: str, normalized_score: float) -> str:
        """
        Get human-readable interpretation of a normalized score.
        
        Args:
            axis_id: Axis identifier
            normalized_score: Score in 0-100 range
            
        Returns:
            Interpretation string
        """
        if normalized_score < 30:
            return "Low"
        elif normalized_score < 70:
            return "Moderate"
        else:
            return "High"
    
    def calculate_score_distribution(self, normalized_scores: Dict[str, float]) -> Dict[str, str]:
        """
        Calculate distribution of scores across all axes.
        
        Args:
            normalized_scores: Normalized scores for all axes
            
        Returns:
            Dictionary mapping axis_id -> interpretation
        """
        return {
            axis_id: self.get_score_interpretation(axis_id, score)
            for axis_id, score in normalized_scores.items()
        }
    
    def detect_extreme_scores(self, normalized_scores: Dict[str, float]) -> List[str]:
        """
        Detect axes with extreme scores (very high or very low).
        
        Args:
            normalized_scores: Normalized scores for all axes
            
        Returns:
            List of axis_ids with extreme scores
        """
        extreme_axes = []
        
        for axis_id, score in normalized_scores.items():
            if score <= 10 or score >= 90:
                extreme_axes.append(axis_id)
        
        return extreme_axes
    
    def calculate_balance_score(self, normalized_scores: Dict[str, float]) -> float:
        """
        Calculate overall balance score (how evenly distributed the scores are).
        
        Args:
            normalized_scores: Normalized scores for all axes
            
        Returns:
            Balance score (0 = perfectly balanced, higher = more imbalanced)
        """
        if not normalized_scores:
            return 0.0
        
        scores = list(normalized_scores.values())
        mean_score = sum(scores) / len(scores)
        
        # Calculate standard deviation as balance measure
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        balance_score = variance ** 0.5
        
        return round(balance_score, 2)


# Utility functions for easy access
async def calculate_session_scores(session: Session) -> Dict[str, float]:
    """Calculate raw scores for a session."""
    service = ScoringService()
    return await service.calculate_scores(session)


async def normalize_session_scores(raw_scores: Dict[str, float]) -> Dict[str, float]:
    """Normalize raw scores to display range."""
    service = ScoringService()
    return await service.normalize_scores(raw_scores)
