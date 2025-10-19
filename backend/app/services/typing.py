"""
Typing service for NightLoom MVP personality type classification.

Analyzes user scores to determine dominant axes and classify into
personality types with dynamic thresholding.
"""

from typing import Dict, List, Tuple
from app.models.session import TypeProfile


class TypingService:
    """Service for personality type classification and analysis."""
    
    def __init__(self):
        self.dominant_threshold = 60.0  # Scores above this are considered dominant
        self.neutral_threshold = 15.0   # Range around 50 considered neutral
    
    def get_dominant_axes(self, normalized_scores: Dict[str, float]) -> List[str]:
        """
        Identify the two most dominant axes from normalized scores.
        
        Args:
            normalized_scores: Scores in 0-100 range
            
        Returns:
            List of 2 axis IDs with highest scores
        """
        if len(normalized_scores) < 2:
            return list(normalized_scores.keys())
        
        # Sort axes by score (descending)
        sorted_axes = sorted(
            normalized_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [axis_id for axis_id, _ in sorted_axes[:2]]
    
    def classify_axis_polarity(self, axis_id: str, score: float) -> str:
        """
        Classify an axis score into polarity categories.
        
        Args:
            axis_id: Axis identifier
            score: Normalized score (0-100)
            
        Returns:
            Polarity classification ('Hi', 'Lo', 'Neutral')
        """
        center = 50.0
        
        if abs(score - center) <= self.neutral_threshold:
            return "Neutral"
        elif score > center:
            return "Hi"
        else:
            return "Lo"
    
    def generate_polarity_pattern(self, dominant_axes: List[str], normalized_scores: Dict[str, float]) -> str:
        """
        Generate polarity pattern for dominant axes.
        
        Args:
            dominant_axes: List of 2 dominant axis IDs
            normalized_scores: Normalized scores
            
        Returns:
            Polarity pattern like 'Hi-Lo', 'Neutral-Hi', etc.
        """
        if len(dominant_axes) != 2:
            return "Undefined"
        
        polarities = []
        for axis_id in dominant_axes:
            score = normalized_scores.get(axis_id, 50.0)
            polarity = self.classify_axis_polarity(axis_id, score)
            polarities.append(polarity)
        
        return f"{polarities[0]}-{polarities[1]}"
    
    def calculate_type_strength(self, normalized_scores: Dict[str, float], dominant_axes: List[str]) -> float:
        """
        Calculate how strongly the scores align with the identified type.
        
        Args:
            normalized_scores: Normalized scores
            dominant_axes: Dominant axes for the type
            
        Returns:
            Strength score (0-100)
        """
        if not dominant_axes:
            return 0.0
        
        # Calculate strength based on how far dominant axes are from neutral
        total_deviation = 0.0
        center = 50.0
        
        for axis_id in dominant_axes:
            score = normalized_scores.get(axis_id, center)
            deviation = abs(score - center)
            total_deviation += deviation
        
        # Average deviation, scaled to 0-100
        average_deviation = total_deviation / len(dominant_axes)
        strength = min(100.0, (average_deviation / 50.0) * 100.0)
        
        return round(strength, 1)
    
    def select_best_type_profiles(
        self, 
        available_profiles: List[TypeProfile], 
        normalized_scores: Dict[str, float],
        dominant_axes: List[str],
        target_count: int = 4
    ) -> List[TypeProfile]:
        """
        Select best matching type profiles from available options.
        
        Args:
            available_profiles: All available type profiles
            normalized_scores: User's normalized scores
            dominant_axes: User's dominant axes
            target_count: Target number of profiles to return
            
        Returns:
            List of best matching TypeProfile objects
        """
        if not available_profiles:
            return []
        
        # Score each profile based on fit
        scored_profiles = []
        
        for profile in available_profiles:
            fit_score = self._calculate_profile_fit(profile, normalized_scores, dominant_axes)
            scored_profiles.append((profile, fit_score))
        
        # Sort by fit score (descending) and take top profiles
        scored_profiles.sort(key=lambda x: x[1], reverse=True)
        
        return [profile for profile, _ in scored_profiles[:target_count]]
    
    def _calculate_profile_fit(
        self, 
        profile: TypeProfile, 
        normalized_scores: Dict[str, float], 
        user_dominant_axes: List[str]
    ) -> float:
        """
        Calculate how well a profile fits the user's scores.
        
        Args:
            profile: Type profile to evaluate
            normalized_scores: User's scores
            user_dominant_axes: User's dominant axes
            
        Returns:
            Fit score (higher = better fit)
        """
        fit_score = 0.0
        
        # Bonus for matching dominant axes
        matching_axes = set(profile.dominantAxes) & set(user_dominant_axes)
        fit_score += len(matching_axes) * 30.0
        
        # Bonus for polarity alignment
        user_polarity = self.generate_polarity_pattern(user_dominant_axes, normalized_scores)
        if profile.polarity == user_polarity:
            fit_score += 40.0
        elif "Neutral" in user_polarity or "Neutral" in profile.polarity:
            fit_score += 20.0  # Partial match for neutral types
        
        # Small bonus for type strength
        strength = self.calculate_type_strength(normalized_scores, profile.dominantAxes)
        fit_score += strength * 0.1
        
        return fit_score
    
    def create_custom_type_profile(
        self, 
        normalized_scores: Dict[str, float], 
        dominant_axes: List[str],
        keyword: str
    ) -> TypeProfile:
        """
        Create a custom type profile based on user's specific scores.
        
        Args:
            normalized_scores: User's normalized scores
            dominant_axes: User's dominant axes
            keyword: User's selected keyword for personalization
            
        Returns:
            Custom TypeProfile object
        """
        polarity = self.generate_polarity_pattern(dominant_axes, normalized_scores)
        strength = self.calculate_type_strength(normalized_scores, dominant_axes)
        
        # Generate name based on polarity and strength
        if strength > 80:
            intensity = "Strong"
        elif strength > 60:
            intensity = "Moderate"
        else:
            intensity = "Balanced"
        
        # Simple naming based on first dominant axis
        axis_names = {
            "logic_emotion": "Analytical" if normalized_scores.get("logic_emotion", 50) > 50 else "Intuitive",
            "speed_caution": "Dynamic" if normalized_scores.get("speed_caution", 50) > 50 else "Thoughtful",
            "individual_group": "Independent" if normalized_scores.get("individual_group", 50) > 50 else "Collaborative",
            "stability_change": "Innovative" if normalized_scores.get("stability_change", 50) > 50 else "Steady"
        }
        
        primary_trait = axis_names.get(dominant_axes[0], "Unique") if dominant_axes else "Balanced"
        name = f"{intensity} {primary_trait}"
        
        return TypeProfile(
            name=name,
            description=f"「{keyword}」を重視し、{polarity}パターンの意思決定スタイルを示すタイプ。",
            keywords=[keyword, primary_trait.lower(), intensity.lower()],
            dominantAxes=dominant_axes[:2],  # Ensure exactly 2 axes
            polarity=polarity,
            meta={
                "custom": True,
                "strength": strength,
                "keyword_based": True
            }
        )
    
    def analyze_type_diversity(self, type_profiles: List[TypeProfile]) -> Dict[str, any]:
        """
        Analyze diversity of selected type profiles.
        
        Args:
            type_profiles: List of type profiles
            
        Returns:
            Analysis results
        """
        if not type_profiles:
            return {"diversity_score": 0.0, "coverage": []}
        
        # Count unique polarities
        polarities = set(profile.polarity for profile in type_profiles)
        
        # Count unique dominant axes
        all_axes = set()
        for profile in type_profiles:
            all_axes.update(profile.dominantAxes)
        
        diversity_score = (len(polarities) + len(all_axes)) / (len(type_profiles) + 4) * 100
        
        return {
            "diversity_score": round(diversity_score, 1),
            "unique_polarities": len(polarities),
            "axis_coverage": len(all_axes),
            "polarities": list(polarities)
        }


# Utility functions
def classify_user_type(
    normalized_scores: Dict[str, float], 
    available_profiles: List[TypeProfile],
    keyword: str = ""
) -> Tuple[List[str], str, List[TypeProfile]]:
    """
    Complete type classification for a user.
    
    Returns:
        Tuple of (dominant_axes, polarity_pattern, selected_profiles)
    """
    service = TypingService()
    
    dominant_axes = service.get_dominant_axes(normalized_scores)
    polarity = service.generate_polarity_pattern(dominant_axes, normalized_scores)
    profiles = service.select_best_type_profiles(available_profiles, normalized_scores, dominant_axes)
    
    return dominant_axes, polarity, profiles
