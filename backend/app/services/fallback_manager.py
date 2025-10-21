
"""
Advanced fallback management for NightLoom LLM integration.

Extends existing fallback assets with dynamic fallback strategies,
intelligent content selection, and failure recovery mechanisms.
"""

import asyncio
import random
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone

from ..models.session import Session, Axis, Scene, Choice, TypeProfile
from ..services.fallback_assets import (
    FallbackAssets, get_fallback_axes, get_fallback_keywords,
    get_fallback_scenes, get_fallback_types, get_fallback_scene
)


class FallbackStrategy:
    """Defines different fallback strategies based on failure context."""
    
    STATIC = "static"           # Use predefined static content
    ADAPTIVE = "adaptive"       # Adapt content to session context  
    RANDOMIZED = "randomized"   # Add randomization to avoid repetition
    CONTEXTUAL = "contextual"   # Use session context for smarter fallbacks


class FallbackAssetManager:
    """
    Enhanced fallback asset manager with intelligent content selection.
    
    Provides context-aware fallbacks that maintain session coherence
    while ensuring diagnosis quality when LLM services fail.
    """
    
    def __init__(self, default_strategy: str = FallbackStrategy.ADAPTIVE):
        """
        Initialize fallback manager.
        
        Args:
            default_strategy: Default fallback strategy to use
        """
        self.default_strategy = default_strategy
        self.fallback_usage = {}  # Track fallback usage for optimization
        self._session_contexts = {}  # Cache session contexts
        
    async def get_keywords_for_character(
        self, 
        initial_character: str, 
        strategy: Optional[str] = None,
        session_context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Get keyword candidates with intelligent fallback selection.
        
        Args:
            initial_character: Hiragana character to generate keywords for
            strategy: Fallback strategy to use
            session_context: Additional session context
            
        Returns:
            List of 4 keyword candidates
        """
        strategy = strategy or self.default_strategy
        
        # Get base keywords
        base_keywords = FallbackAssets.get_keyword_candidates(initial_character)
        
        if strategy == FallbackStrategy.STATIC:
            return base_keywords
            
        elif strategy == FallbackStrategy.RANDOMIZED:
            # Add some randomization while keeping character alignment
            all_keywords = self._get_extended_keyword_pool(initial_character)
            selected = random.sample(all_keywords, min(4, len(all_keywords)))
            return selected
            
        elif strategy == FallbackStrategy.ADAPTIVE:
            # Adapt based on session context
            if session_context and "preferred_themes" in session_context:
                themed_keywords = self._get_themed_keywords(
                    initial_character, 
                    session_context["preferred_themes"]
                )
                if themed_keywords:
                    return themed_keywords[:4]
            
            return base_keywords
            
        elif strategy == FallbackStrategy.CONTEXTUAL:
            # Use session history to avoid repetition
            if session_context and "previous_sessions" in session_context:
                return await self._get_contextual_keywords(
                    initial_character, 
                    session_context["previous_sessions"]
                )
        
        return base_keywords
    
    async def get_default_axes(
        self, 
        keyword: Optional[str] = None,
        strategy: Optional[str] = None
    ) -> List[Axis]:
        """
        Get evaluation axes with keyword-aware selection.
        
        Args:
            keyword: Selected keyword for context
            strategy: Fallback strategy
            
        Returns:
            List of 2-6 evaluation axes
        """
        strategy = strategy or self.default_strategy
        base_axes = FallbackAssets.get_default_axes()
        
        if strategy == FallbackStrategy.STATIC:
            return base_axes[:4]  # Standard 4 axes
            
        elif strategy == FallbackStrategy.ADAPTIVE and keyword:
            # Select axes most relevant to keyword
            keyword_axis_mapping = {
                "愛": ["logic_emotion", "individual_group", "stability_change"],
                "冒険": ["speed_caution", "stability_change", "individual_group"],
                "挑戦": ["speed_caution", "logic_emotion", "stability_change"],
                "成長": ["stability_change", "logic_emotion", "individual_group"],
                "希望": ["stability_change", "individual_group", "logic_emotion"],
                "協力": ["individual_group", "logic_emotion", "stability_change"]
            }
            
            preferred_axis_ids = keyword_axis_mapping.get(keyword, [])
            if preferred_axis_ids:
                selected_axes = []
                
                # Add preferred axes first
                for axis_id in preferred_axis_ids[:3]:
                    axis = next((a for a in base_axes if a.id == axis_id), None)
                    if axis and axis not in selected_axes:
                        selected_axes.append(axis)
                
                # Fill remaining slots
                for axis in base_axes:
                    if axis not in selected_axes and len(selected_axes) < 4:
                        selected_axes.append(axis)
                
                return selected_axes
        
        elif strategy == FallbackStrategy.RANDOMIZED:
            # Random selection of 3-4 axes
            count = random.choice([3, 4])
            return random.sample(base_axes, count)
        
        return base_axes[:4]
    
    async def get_fallback_scene(
        self, 
        scene_index: int, 
        theme_id: str,
        axes: List[str],
        keyword: Optional[str] = None,
        strategy: Optional[str] = None
    ) -> Scene:
        """
        Get fallback scene with dynamic content adaptation.
        
        Args:
            scene_index: Scene number (1-4)
            theme_id: UI theme identifier
            axes: Available evaluation axes
            keyword: Session keyword for context
            strategy: Fallback strategy
            
        Returns:
            Generated fallback scene
        """
        strategy = strategy or self.default_strategy
        
        if strategy == FallbackStrategy.STATIC:
            return get_fallback_scene(scene_index, theme_id)
        
        # Dynamic scene generation
        scene_templates = self._get_scene_templates(scene_index, keyword)
        template = random.choice(scene_templates) if strategy == FallbackStrategy.RANDOMIZED else scene_templates[0]
        
        # Generate choices based on available axes
        choices = await self._generate_fallback_choices(scene_index, axes, strategy)
        
        return Scene(
            sceneIndex=scene_index,
            themeId=theme_id,
            narrative=template.format(keyword=keyword or "あなたの目標"),
            choices=choices
        )
    
    async def generate_fallback_profiles(
        self,
        scores: Dict[str, float],
        axes: List[str],
        keyword: Optional[str] = None,
        strategy: Optional[str] = None
    ) -> List[TypeProfile]:
        """
        Generate fallback type profiles based on scores.
        
        Args:
            scores: Normalized scores (0-100) for each axis
            axes: List of axis IDs used in session
            keyword: Session keyword for context
            strategy: Fallback strategy
            
        Returns:
            List of type profiles
        """
        strategy = strategy or self.default_strategy
        base_profiles = FallbackAssets.get_fallback_type_profiles()
        
        if strategy == FallbackStrategy.STATIC:
            return base_profiles[:1]  # Return single default profile
        
        # Score-based profile selection
        selected_profiles = []
        
        # Analyze score patterns
        high_scores = [axis for axis, score in scores.items() if score > 70]
        low_scores = [axis for axis, score in scores.items() if score < 30]
        
        # Select profiles based on dominant patterns
        for profile in base_profiles:
            if self._profile_matches_scores(profile, high_scores, low_scores):
                selected_profiles.append(profile)
        
        # Ensure at least one profile
        if not selected_profiles:
            selected_profiles = [base_profiles[0]]
        
        # Adapt profile descriptions if keyword available
        if keyword and strategy == FallbackStrategy.ADAPTIVE:
            selected_profiles = await self._adapt_profiles_to_keyword(
                selected_profiles, keyword
            )
        
        return selected_profiles
    
    def _get_extended_keyword_pool(self, initial_character: str) -> List[str]:
        """Get extended keyword pool for randomization."""
        extended_pools = {
            "あ": ["愛", "冒険", "挑戦", "成長", "安心", "明日", "歩み", "新しさ"],
            "か": ["希望", "感謝", "革新", "協力", "可能性", "輝き", "価値", "覚悟"],
            "さ": ["成功", "創造", "信念", "探求", "誠実", "成就", "最善", "才能"],
            "た": ["挑戦", "達成", "団結", "努力", "大切", "確信", "体験", "多様"],
            "な": ["夢", "成長", "情熱", "発見", "仲間", "内面", "願い", "流れ"],
            "は": ["発見", "変化", "平和", "勇気", "始まり", "晴れ", "繁栄", "飛躍"],
            "ま": ["魅力", "未来", "満足", "目標", "真心", "守り", "学び", "豊か"],
            "や": ["優雅", "勇気", "喜び", "約束", "やりがい", "優しさ", "躍動", "安らぎ"],
            "ら": ["理想", "冒険", "良心", "連帯", "楽しみ", "理解", "流儀", "力強さ"],
            "わ": ["和", "笑顔", "輪", "若さ", "分かち合い", "忘れない", "我が道", "湧き出る"]
        }
        return extended_pools.get(initial_character, ["希望", "挑戦", "成長", "発見", "創造", "調和", "前進", "実現"])
    
    def _get_themed_keywords(self, initial_character: str, themes: List[str]) -> List[str]:
        """Get keywords aligned with preferred themes."""
        theme_keywords = {
            "adventure": ["冒険", "挑戦", "探求", "発見"],
            "growth": ["成長", "発展", "進歩", "向上"],
            "harmony": ["和", "調和", "平和", "協力"],
            "creativity": ["創造", "革新", "独創", "表現"]
        }
        
        result = []
        for theme in themes:
            if theme in theme_keywords:
                result.extend(theme_keywords[theme])
        
        # Filter by initial character and deduplicate
        filtered = [kw for kw in result if kw.startswith(initial_character)]
        if len(filtered) < 4:
            # Fill with base keywords
            base = FallbackAssets.get_keyword_candidates(initial_character)
            filtered.extend([kw for kw in base if kw not in filtered])
        
        return filtered[:4]
    
    async def _get_contextual_keywords(
        self, 
        initial_character: str, 
        previous_sessions: List[Dict[str, Any]]
    ) -> List[str]:
        """Get keywords avoiding previous session repetition."""
        used_keywords = set()
        for session in previous_sessions[-5:]:  # Last 5 sessions
            if "keyword" in session:
                used_keywords.add(session["keyword"])
        
        pool = self._get_extended_keyword_pool(initial_character)
        available = [kw for kw in pool if kw not in used_keywords]
        
        if len(available) >= 4:
            return random.sample(available, 4)
        else:
            # Mix available with some used ones
            result = available[:]
            remaining = [kw for kw in pool if kw in used_keywords]
            result.extend(random.sample(remaining, 4 - len(available)))
            return result
    
    def _get_scene_templates(self, scene_index: int, keyword: Optional[str]) -> List[str]:
        """Get narrative templates for scene generation."""
        templates = {
            1: [
                "「{keyword}」を大切にしているあなたに、重要な選択の場面が訪れました。どのようにアプローチしますか？",
                "人生において「{keyword}」をテーマとした決断を迫られています。あなたならどう行動しますか？",
                "「{keyword}」の実現に向けて、方向性を決める必要があります。どの道を選びますか？"
            ],
            2: [
                "チームで「{keyword}」に関するプロジェクトに取り組んでいます。意見が分かれた時、あなたはどうしますか？",
                "「{keyword}」について仲間と議論している最中です。あなたはどのような役割を果たしますか？",
                "グループで「{keyword}」の目標に向かって進んでいます。困難な局面であなたの取る行動は？"
            ],
            3: [
                "「{keyword}」を実現するため、新しい環境に挑戦する機会が訪れました。あなたの反応は？",
                "「{keyword}」のために変化が必要な状況です。どのように対応しますか？",
                "「{keyword}」を追求する過程で、大きな変革の波が到来しました。あなたはどう動きますか？"
            ],
            4: [
                "「{keyword}」の取り組みで予期しない困難に直面しました。最終的にどう対処しますか？",
                "「{keyword}」への道のりで最後の障壁が現れました。どのように乗り越えますか？",
                "「{keyword}」の実現まであと一歩です。最後の難しい選択をどう決断しますか？"
            ]
        }
        return templates.get(scene_index, [f"シーン{scene_index}での重要な選択場面です。"])
    
    async def _generate_fallback_choices(
        self,
        scene_index: int,
        axes: List[str],
        strategy: str
    ) -> List[Choice]:
        """Generate choices based on available axes."""
        base_choices = [
            {"text": "論理的に分析して決める", "primary_axis": "logic_emotion", "value": 1.0},
            {"text": "直感を信じて決める", "primary_axis": "logic_emotion", "value": -1.0},
            {"text": "迅速に行動する", "primary_axis": "speed_caution", "value": 1.0},
            {"text": "慎重に検討する", "primary_axis": "speed_caution", "value": -1.0},
            {"text": "独自に判断する", "primary_axis": "individual_group", "value": 1.0},
            {"text": "周囲と協調する", "primary_axis": "individual_group", "value": -1.0},
            {"text": "変化を受け入れる", "primary_axis": "stability_change", "value": 1.0},
            {"text": "安定を維持する", "primary_axis": "stability_change", "value": -1.0}
        ]
        
        # Filter choices based on available axes
        available_choices = [
            choice for choice in base_choices
            if choice["primary_axis"] in axes
        ]
        
        # Select 4 choices
        if len(available_choices) >= 4:
            selected = available_choices[:4]
        else:
            # Fill with default choices if not enough axis-specific ones
            selected = available_choices[:]
            default_choices = base_choices[:4]
            for choice in default_choices:
                if len(selected) < 4 and choice not in selected:
                    selected.append(choice)
        
        # Convert to Choice objects
        choices = []
        for i, choice_data in enumerate(selected):
            weights = {}
            for axis in axes:
                if axis == choice_data["primary_axis"]:
                    weights[axis] = choice_data["value"]
                else:
                    # Add small random weights for other axes
                    weights[axis] = random.uniform(-0.3, 0.3)
            
            choices.append(Choice(
                id=f"choice_{scene_index}_{i+1}",
                text=choice_data["text"],
                weights=weights
            ))
        
        return choices
    
    def _profile_matches_scores(
        self,
        profile: TypeProfile,
        high_scores: List[str],
        low_scores: List[str]
    ) -> bool:
        """Check if profile matches score pattern."""
        if not profile.dominantAxes:
            return False
        
        # Check if profile's dominant axes align with score patterns
        matches = 0
        for axis in profile.dominantAxes:
            if axis in high_scores:
                matches += 1
        
        # Profile matches if at least one dominant axis has high score
        return matches > 0
    
    async def _adapt_profiles_to_keyword(
        self,
        profiles: List[TypeProfile],
        keyword: str
    ) -> List[TypeProfile]:
        """Adapt profile descriptions to include keyword context."""
        keyword_adaptations = {
            "愛": "愛情と思いやりを大切にする",
            "冒険": "新しい体験と挑戦を求める",
            "挑戦": "困難に立ち向かう勇気を持つ",
            "成長": "継続的な発展と学びを重視する",
            "希望": "前向きな未来への信念を抱く",
            "協力": "チームワークと連携を重んじる"
        }
        
        adaptation = keyword_adaptations.get(keyword, f"「{keyword}」を大切にする")
        
        adapted_profiles = []
        for profile in profiles:
            adapted_profile = TypeProfile(
                name=profile.name,
                description=f"{profile.description} {adaptation}価値観を持っています。",
                keywords=profile.keywords,
                dominantAxes=profile.dominantAxes,
                polarity=profile.polarity,
                meta=profile.meta
            )
            adapted_profiles.append(adapted_profile)
        
        return adapted_profiles
    
    def record_fallback_usage(
        self,
        operation_type: str,
        strategy: str,
        session_id: str
    ) -> None:
        """Record fallback usage for analytics."""
        if operation_type not in self.fallback_usage:
            self.fallback_usage[operation_type] = {
                "count": 0,
                "strategies": {},
                "sessions": set()
            }
        
        usage = self.fallback_usage[operation_type]
        usage["count"] += 1
        usage["sessions"].add(session_id)
        
        if strategy not in usage["strategies"]:
            usage["strategies"][strategy] = 0
        usage["strategies"][strategy] += 1
    
    def get_fallback_statistics(self) -> Dict[str, Any]:
        """Get fallback usage statistics."""
        return {
            "total_operations": sum(
                stats["count"] for stats in self.fallback_usage.values()
            ),
            "unique_sessions": len(set().union(
                *[stats["sessions"] for stats in self.fallback_usage.values()]
            )) if self.fallback_usage else 0,
            "operation_breakdown": {
                op: {
                    "count": stats["count"],
                    "unique_sessions": len(stats["sessions"]),
                    "strategies": stats["strategies"]
                }
                for op, stats in self.fallback_usage.items()
            }
        }


# Global fallback manager instance
_fallback_manager: Optional[FallbackAssetManager] = None

def get_fallback_manager() -> FallbackAssetManager:
    """Get global fallback manager instance."""
    global _fallback_manager
    if _fallback_manager is None:
        _fallback_manager = FallbackAssetManager()
    return _fallback_manager
