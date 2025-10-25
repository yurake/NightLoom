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
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"[Scoring] Starting score calculation for session {session.id}")
        logger.info(f"[Scoring] Session has {len(session.choices)} choices")
        logger.info(f"[Scoring] Session has {len(session.scenes)} scenes")
        logger.info(f"[Scoring] Session has {len(session.axes)} axes")
        
        if len(session.choices) != 4:
            raise ValueError(f"Expected 4 choices, got {len(session.choices)}")
        
        # Initialize score accumulator with all axis IDs from session.axes
        scores: Dict[str, float] = {}
        expected_axis_ids = set()
        for axis in session.axes:
            scores[axis.id] = 0.0
            expected_axis_ids.add(axis.id)
            logger.info(f"[Scoring] Initialized axis {axis.id} with score 0.0")
        
        logger.info(f"[Scoring] Expected axis IDs: {expected_axis_ids}")
        
        # Process each choice
        for i, choice_record in enumerate(session.choices):
            logger.info(f"[Scoring] Processing choice {i+1}: scene {choice_record.sceneIndex}, choice {choice_record.choiceId}")
            
            # Find the scene and choice
            scene = None
            for s in session.scenes:
                if s.sceneIndex == choice_record.sceneIndex:
                    scene = s
                    break
            
            if not scene:
                logger.error(f"[Scoring] Scene {choice_record.sceneIndex} not found")
                raise ValueError(f"Scene {choice_record.sceneIndex} not found")
            
            # Find the selected choice
            selected_choice = None
            for choice in scene.choices:
                if choice.id == choice_record.choiceId:
                    selected_choice = choice
                    break
            
            if not selected_choice:
                logger.error(f"[Scoring] Choice {choice_record.choiceId} not found in scene {choice_record.sceneIndex}")
                raise ValueError(f"Choice {choice_record.choiceId} not found in scene {choice_record.sceneIndex}")
            
            # Debug: Log choice text and weights
            logger.info(f"[Scoring] Selected choice text: '{selected_choice.text}'")
            choice_weights = selected_choice.get_weights_dict()
            logger.info(f"[Scoring] Choice weights: {choice_weights}")
            logger.info(f"[Scoring] Choice weights type: {type(selected_choice.weights)}")
            
            # Add weights to scores
            choice_axis_ids = set(choice_weights.keys())
            logger.info(f"[Scoring] Choice {i+1} axis IDs: {choice_axis_ids}")
            
            # Check for axis ID mismatches
            unknown_axes = choice_axis_ids - expected_axis_ids
            missing_axes = expected_axis_ids - choice_axis_ids
            
            if unknown_axes:
                logger.warning(f"[Scoring] Choice {i+1} contains unknown axis IDs: {unknown_axes}")
            if missing_axes:
                logger.warning(f"[Scoring] Choice {i+1} missing weights for expected axes: {missing_axes}")
                # Add missing weights as 0.0
                for missing_axis in missing_axes:
                    choice_weights[missing_axis] = 0.0
                    logger.info(f"[Scoring] Added missing weight {missing_axis}: 0.0")
            
            for axis_id, weight in choice_weights.items():
                if axis_id not in scores:
                    logger.warning(f"[Scoring] Found unknown axis ID in choice weights: {axis_id}, adding to scores")
                    scores[axis_id] = 0.0
                
                old_score = scores[axis_id]
                scores[axis_id] += weight
                logger.info(f"[Scoring] Updated axis {axis_id}: {old_score} + {weight} = {scores[axis_id]}")
        
        # Log final scores before clamping
        logger.info(f"[Scoring] Raw scores before clamping: {scores}")
        
        # Clamp scores to valid range
        for axis_id in scores:
            old_score = scores[axis_id]
            scores[axis_id] = max(
                self.raw_score_range[0],
                min(self.raw_score_range[1], scores[axis_id])
            )
            if old_score != scores[axis_id]:
                logger.info(f"[Scoring] Clamped axis {axis_id}: {old_score} -> {scores[axis_id]}")
        
        logger.info(f"[Scoring] Final raw scores: {scores}")
        return scores
    
    async def normalize_scores(self, raw_scores: Dict[str, float]) -> Dict[str, float]:
        """
        Normalize raw scores to 0-100 range for display.
        
        Args:
            raw_scores: Raw scores in -5.0 to 5.0 range
            
        Returns:
            Dictionary mapping axis_id -> normalized_score (0-100)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"[Scoring] Normalizing scores: input={raw_scores}")
        normalized = {}
        
        for axis_id, raw_score in raw_scores.items():
            # Linear transformation from [-5, 5] to [0, 100]
            # Formula: (raw_score - min_raw) / (max_raw - min_raw) * (max_norm - min_norm) + min_norm
            min_raw, max_raw = self.raw_score_range
            min_norm, max_norm = self.normalized_range
            
            normalized_score = ((raw_score - min_raw) / (max_raw - min_raw)) * (max_norm - min_norm) + min_norm
            
            # Round to 1 decimal place for display
            normalized[axis_id] = round(normalized_score, 1)
            logger.info(f"[Scoring] Normalized {axis_id}: {raw_score} -> {normalized[axis_id]}")
        
        logger.info(f"[Scoring] Final normalized scores: {normalized}")
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
