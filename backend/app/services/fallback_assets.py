"""
Fallback asset definitions for NightLoom MVP.

Provides static axes, scenes, and types as backup when LLM services are unavailable.
All content follows the data model specifications and supports Japanese language.
"""

from typing import Dict, List
from app.models.session import Axis, Scene, Choice, TypeProfile


class FallbackAssets:
    """Static fallback content for diagnosis sessions."""
    
    @staticmethod
    def get_default_axes() -> List[Axis]:
        """Return default evaluation axes for fallback scenarios."""
        return [
            Axis(
                id="logic_emotion",
                name="Logic vs Emotion",
                description="Balance between analytical thinking and intuitive decision making",
                direction="論理的 ⟷ 感情的"
            ),
            Axis(
                id="speed_caution",
                name="Speed vs Caution",
                description="Preference for quick decisions versus careful deliberation",
                direction="迅速 ⟷ 慎重"
            ),
            Axis(
                id="individual_group",
                name="Individual vs Group",
                description="Tendency to act independently or seek group consensus",
                direction="個人 ⟷ 集団"
            ),
            Axis(
                id="stability_change",
                name="Stability vs Change",
                description="Preference for maintaining status quo or embracing change",
                direction="安定 ⟷ 変化"
            )
        ]
    
    @staticmethod
    def get_keyword_candidates(initial_character: str) -> List[str]:
        """Return fallback keyword candidates based on initial character."""
        # Fallback keywords organized by hiragana initial
        fallback_map = {
            "あ": ["愛", "冒険", "挑戦", "成長"],
            "か": ["希望", "感謝", "革新", "協力"],
            "さ": ["成功", "創造", "信念", "探求"],
            "た": ["挑戦", "達成", "団結", "努力"],
            "な": ["夢", "成長", "情熱", "発見"],
            "は": ["発見", "変化", "平和", "勇気"],
            "ま": ["魅力", "未来", "満足", "目標"],
            "や": ["優雅", "勇気", "喜び", "約束"],
            "ら": ["理想", "冒険", "良心", "連帯"],
            "わ": ["和", "笑顔", "輪", "若さ"]
        }
        
        # Return specific candidates or default set
        return fallback_map.get(initial_character, ["希望", "挑戦", "成長", "発見"])
    
    @staticmethod
    def get_fallback_scenes(theme_id: str, selected_keyword: str) -> List[Scene]:
        """Return fallback scenes for all 4 diagnosis stages."""
        
        scenes = [
            Scene(
                sceneIndex=1,
                themeId=theme_id,
                narrative=f"「{selected_keyword}」をテーマに、重要な決断を迫られました。あなたはどのようにアプローチしますか？",
                choices=[
                    Choice(
                        id="choice_1_1",
                        text="データと論理を重視して分析する",
                        weights={"logic_emotion": 1.0, "speed_caution": -0.5, "individual_group": 0.3, "stability_change": -0.2}
                    ),
                    Choice(
                        id="choice_1_2", 
                        text="直感と感情を大切にして判断する",
                        weights={"logic_emotion": -1.0, "speed_caution": 0.2, "individual_group": -0.3, "stability_change": 0.4}
                    ),
                    Choice(
                        id="choice_1_3",
                        text="迅速に決断して行動に移す",
                        weights={"logic_emotion": 0.2, "speed_caution": 1.0, "individual_group": 0.5, "stability_change": 0.6}
                    ),
                    Choice(
                        id="choice_1_4",
                        text="慎重に検討して安全な選択をする",
                        weights={"logic_emotion": 0.3, "speed_caution": -1.0, "individual_group": -0.2, "stability_change": -0.7}
                    )
                ]
            ),
            Scene(
                sceneIndex=2,
                themeId=theme_id,
                narrative=f"チームで「{selected_keyword}」に関するプロジェクトに取り組んでいます。意見が分かれた時、あなたはどうしますか？",
                choices=[
                    Choice(
                        id="choice_2_1",
                        text="自分の考えを貫いて独自路線で進む",
                        weights={"logic_emotion": 0.4, "speed_caution": 0.3, "individual_group": 1.0, "stability_change": 0.5}
                    ),
                    Choice(
                        id="choice_2_2",
                        text="チーム全体の合意を重視して調整する",
                        weights={"logic_emotion": -0.2, "speed_caution": -0.6, "individual_group": -1.0, "stability_change": -0.3}
                    ),
                    Choice(
                        id="choice_2_3",
                        text="リーダーシップを発揮して方向性を示す",
                        weights={"logic_emotion": 0.6, "speed_caution": 0.7, "individual_group": 0.5, "stability_change": 0.4}
                    ),
                    Choice(
                        id="choice_2_4",
                        text="メンバーの意見を聞いてサポートに回る",
                        weights={"logic_emotion": -0.4, "speed_caution": -0.5, "individual_group": -0.7, "stability_change": -0.1}
                    )
                ]
            ),
            Scene(
                sceneIndex=3,
                themeId=theme_id,
                narrative=f"「{selected_keyword}」を実現するため、新しい環境に挑戦する機会が訪れました。あなたの反応は？",
                choices=[
                    Choice(
                        id="choice_3_1",
                        text="リスクを承知で新しい挑戦を受け入れる",
                        weights={"logic_emotion": 0.3, "speed_caution": 0.8, "individual_group": 0.6, "stability_change": 1.0}
                    ),
                    Choice(
                        id="choice_3_2",
                        text="現在の安定した環境を維持する",
                        weights={"logic_emotion": 0.5, "speed_caution": -0.8, "individual_group": -0.2, "stability_change": -1.0}
                    ),
                    Choice(
                        id="choice_3_3",
                        text="段階的に変化を取り入れて適応する",
                        weights={"logic_emotion": 0.7, "speed_caution": -0.3, "individual_group": 0.1, "stability_change": 0.2}
                    ),
                    Choice(
                        id="choice_3_4",
                        text="周囲の意見を参考にして判断する",
                        weights={"logic_emotion": -0.2, "speed_caution": -0.4, "individual_group": -0.8, "stability_change": -0.3}
                    )
                ]
            ),
            Scene(
                sceneIndex=4,
                themeId=theme_id,
                narrative=f"「{selected_keyword}」の取り組みで予期しない困難に直面しました。最終的にどう対処しますか？",
                choices=[
                    Choice(
                        id="choice_4_1",
                        text="論理的に問題を分析して解決策を見つける",
                        weights={"logic_emotion": 1.0, "speed_caution": -0.2, "individual_group": 0.4, "stability_change": 0.1}
                    ),
                    Choice(
                        id="choice_4_2",
                        text="直感を信じて柔軟に対応する",
                        weights={"logic_emotion": -0.8, "speed_caution": 0.5, "individual_group": 0.2, "stability_change": 0.7}
                    ),
                    Choice(
                        id="choice_4_3",
                        text="迅速に決断して行動で解決する",
                        weights={"logic_emotion": 0.2, "speed_caution": 1.0, "individual_group": 0.7, "stability_change": 0.5}
                    ),
                    Choice(
                        id="choice_4_4",
                        text="慎重に検討して確実な方法を選ぶ",
                        weights={"logic_emotion": 0.6, "speed_caution": -1.0, "individual_group": -0.1, "stability_change": -0.6}
                    )
                ]
            )
        ]
        
        return scenes
    
    @staticmethod
    def get_fallback_type_profiles() -> List[TypeProfile]:
        """Return fallback type profiles for result generation."""
        return [
            TypeProfile(
                name="Logic Leader",
                description="論理的思考と迅速な判断力を兼ね備えたリーダータイプ。データに基づいて決断し、チームを率いる能力に長けています。",
                keywords=["systematic", "decisive", "goal-oriented", "leadership"],
                dominantAxes=["logic_emotion", "speed_caution"],
                polarity="Hi-Hi",
                meta={"cell": "A1", "isNeutral": False}
            ),
            TypeProfile(
                name="Wise Planner",
                description="慎重な計画性と論理的アプローチを重視するタイプ。安定性を求め、リスクを最小化した確実な成果を追求します。",
                keywords=["methodical", "careful", "reliable", "thorough"],
                dominantAxes=["logic_emotion", "speed_caution"],
                polarity="Hi-Lo",
                meta={"cell": "A2", "isNeutral": False}
            ),
            TypeProfile(
                name="Creative Spark",
                description="感情と直感を大切にし、変化を恐れず新しい可能性に挑戦するタイプ。創造性と適応力が特徴です。",
                keywords=["creative", "adaptable", "innovative", "empathetic"],
                dominantAxes=["logic_emotion", "stability_change"],
                polarity="Lo-Hi",
                meta={"cell": "B1", "isNeutral": False}
            ),
            TypeProfile(
                name="Team Supporter",
                description="感情を重視し、安定した環境で他者をサポートすることを得意とするタイプ。協調性と共感力に優れています。",
                keywords=["supportive", "empathetic", "collaborative", "stable"],
                dominantAxes=["logic_emotion", "individual_group"],
                polarity="Lo-Lo",
                meta={"cell": "B2", "isNeutral": False}
            ),
            TypeProfile(
                name="Fast Innovator",
                description="迅速な行動力と変化への適応力を持つタイプ。新しいアイデアを素早く実現し、チームを活性化させます。",
                keywords=["dynamic", "innovative", "energetic", "flexible"],
                dominantAxes=["speed_caution", "stability_change"],
                polarity="Hi-Hi",
                meta={"cell": "C1", "isNeutral": False}
            ),
            TypeProfile(
                name="Wise Mediator",
                description="バランス感覚に優れ、様々な観点を統合して最適解を見つけるタイプ。中庸を保ちながら調和を図ります。",
                keywords=["balanced", "diplomatic", "versatile", "integrative"],
                dominantAxes=["individual_group", "stability_change"],
                polarity="Neutral-Neutral",
                meta={"cell": "Center", "isNeutral": True}
            )
        ]
    
    @staticmethod
    def get_theme_fallback() -> str:
        """Return fallback theme ID when theme selection fails."""
        return "fallback"
    
    @staticmethod
    def get_initial_character_fallback() -> str:
        """Return fallback initial character."""
        return "あ"


# Convenience functions for easy access
def get_fallback_axes() -> List[Axis]:
    """Get default fallback axes."""
    return FallbackAssets.get_default_axes()


def get_fallback_keywords(initial_character: str) -> List[str]:
    """Get fallback keyword candidates."""
    return FallbackAssets.get_keyword_candidates(initial_character)


def get_fallback_scenes(theme_id: str, keyword: str) -> List[Scene]:
    """Get fallback scenes for all 4 stages."""
    return FallbackAssets.get_fallback_scenes(theme_id, keyword)


def get_fallback_types() -> List[TypeProfile]:
    """Get fallback type profiles."""
    return FallbackAssets.get_fallback_type_profiles()


def get_fallback_scene(scene_index: int, theme_id: str) -> Scene:
    """Get a single fallback scene by index."""
    # Create a generic fallback scene for any index
    return Scene(
        sceneIndex=scene_index,
        themeId=theme_id,
        narrative=f"診断シーン{scene_index}：重要な選択の場面です。あなたの価値観に最も近い選択肢を選んでください。",
        choices=[
            Choice(
                id=f"choice_{scene_index}_1",
                text="論理的に分析して決める",
                weights={"logic_emotion": 1.0, "speed_caution": -0.3, "individual_group": 0.2, "stability_change": 0.1}
            ),
            Choice(
                id=f"choice_{scene_index}_2",
                text="直感を信じて決める",
                weights={"logic_emotion": -1.0, "speed_caution": 0.4, "individual_group": -0.1, "stability_change": 0.3}
            ),
            Choice(
                id=f"choice_{scene_index}_3",
                text="迅速に行動する",
                weights={"logic_emotion": 0.2, "speed_caution": 1.0, "individual_group": 0.5, "stability_change": 0.6}
            ),
            Choice(
                id=f"choice_{scene_index}_4",
                text="慎重に検討する",
                weights={"logic_emotion": 0.3, "speed_caution": -1.0, "individual_group": -0.3, "stability_change": -0.5}
            )
        ]
    )
