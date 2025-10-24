"""
Fallback asset definitions for NightLoom MVP.

Provides static axes, scenes, and types as backup when LLM services are unavailable.
All content follows the data model specifications and supports Japanese language.
"""

from typing import Dict, List
from app.models.session import Axis, Scene, Choice, TypeProfile, WeightEntry


class FallbackAssets:
    """Static fallback content for diagnosis sessions."""
    
    @staticmethod
    def get_default_axes() -> List[Axis]:
        """Return default evaluation axes for fallback scenarios."""
        return [
            Axis(
                id="axis_1",
                name="Logic vs Emotion",
                description="Balance between analytical thinking and intuitive decision making",
                direction="論理的 ⟷ 感情的"
            ),
            Axis(
                id="axis_2",
                name="Speed vs Caution",
                description="Preference for quick decisions versus careful deliberation",
                direction="迅速 ⟷ 慎重"
            ),
            Axis(
                id="axis_3",
                name="Individual vs Group",
                description="Tendency to act independently or seek group consensus",
                direction="個人 ⟷ 集団"
            ),
            Axis(
                id="axis_4",
                name="Stability vs Change",
                description="Preference for maintaining status quo or embracing change",
                direction="安定 ⟷ 変化"
            )
        ]
    
    @staticmethod
    def get_keyword_candidates(initial_character: str) -> List[str]:
        """Return fallback keyword candidates based on initial character."""
        # Updated fallback keywords with natural Japanese expressions (2-4 characters)
        fallback_map = {
            "あ": ["愛情", "明るい", "新しい", "温かい"],
            "か": ["輝く", "感謝", "可愛い", "活気"],
            "く": ["輝く", "暮らし", "雲海", "工夫"],
            "さ": ["爽やか", "最高", "咲く", "才能"],  # Fixed: 幸せ→咲く (幸せ reads as しあわせ, not さ)
            "た": ["楽しい", "大切", "頼もしい", "確か"],
            "な": ["懐かしい", "仲良し", "内面", "納得"],
            "は": ["花咲く", "春らしい", "晴れやか", "博愛"],
            "ま": ["真心", "眩しい", "満足", "学び"],
            "や": ["優しい", "安らぎ", "柔らか", "約束"],
            "ら": ["楽観的", "らしさ", "らくらく", "らんらん"],  # Fixed: 立派→らしさ, 理想→らくらく, 凛とした→らんらん
            "わ": ["和やか", "輪になる", "若々しい", "忘れない"]
        }
        
        # Return specific candidates or default set
        return fallback_map.get(initial_character, ["輝く", "新しい", "明るい", "温かい"])
    
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
                        weights=[
                            WeightEntry(id="axis_1", name="Logic vs Emotion", score=1.0),
                            WeightEntry(id="axis_2", name="Speed vs Caution", score=-0.5),
                            WeightEntry(id="axis_3", name="Individual vs Group", score=0.3),
                            WeightEntry(id="axis_4", name="Stability vs Change", score=-0.2)
                        ]
                    ),
                    Choice(
                        id="choice_1_2",
                        text="直感と感情を大切にして判断する",
                        weights=[
                            WeightEntry(id="axis_1", name="Logic vs Emotion", score=-1.0),
                            WeightEntry(id="axis_2", name="Speed vs Caution", score=0.2),
                            WeightEntry(id="axis_3", name="Individual vs Group", score=-0.3),
                            WeightEntry(id="axis_4", name="Stability vs Change", score=0.4)
                        ]
                    ),
                    Choice(
                        id="choice_1_3",
                        text="迅速に決断して行動に移す",
                        weights=[
                            WeightEntry(id="axis_1", name="Logic vs Emotion", score=0.2),
                            WeightEntry(id="axis_2", name="Speed vs Caution", score=1.0),
                            WeightEntry(id="axis_3", name="Individual vs Group", score=0.5),
                            WeightEntry(id="axis_4", name="Stability vs Change", score=0.6)
                        ]
                    ),
                    Choice(
                        id="choice_1_4",
                        text="慎重に検討して安全な選択をする",
                        weights=[
                            WeightEntry(id="axis_1", name="Logic vs Emotion", score=0.3),
                            WeightEntry(id="axis_2", name="Speed vs Caution", score=-1.0),
                            WeightEntry(id="axis_3", name="Individual vs Group", score=-0.2),
                            WeightEntry(id="axis_4", name="Stability vs Change", score=-0.7)
                        ]
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
                        weights=[
                            WeightEntry(id="axis_1", name="Logic vs Emotion", score=0.4),
                            WeightEntry(id="axis_2", name="Speed vs Caution", score=0.3),
                            WeightEntry(id="axis_3", name="Individual vs Group", score=1.0),
                            WeightEntry(id="axis_4", name="Stability vs Change", score=0.5)
                        ]
                    ),
                    Choice(
                        id="choice_2_2",
                        text="チーム全体の合意を重視して調整する",
                        weights=[
                            WeightEntry(id="axis_1", name="Logic vs Emotion", score=-0.2),
                            WeightEntry(id="axis_2", name="Speed vs Caution", score=-0.6),
                            WeightEntry(id="axis_3", name="Individual vs Group", score=-1.0),
                            WeightEntry(id="axis_4", name="Stability vs Change", score=-0.3)
                        ]
                    ),
                    Choice(
                        id="choice_2_3",
                        text="リーダーシップを発揮して方向性を示す",
                        weights=[
                            WeightEntry(id="axis_1", name="Logic vs Emotion", score=0.6),
                            WeightEntry(id="axis_2", name="Speed vs Caution", score=0.7),
                            WeightEntry(id="axis_3", name="Individual vs Group", score=0.5),
                            WeightEntry(id="axis_4", name="Stability vs Change", score=0.4)
                        ]
                    ),
                    Choice(
                        id="choice_2_4",
                        text="メンバーの意見を聞いてサポートに回る",
                        weights=[
                            WeightEntry(id="axis_1", name="Logic vs Emotion", score=-0.4),
                            WeightEntry(id="axis_2", name="Speed vs Caution", score=-0.5),
                            WeightEntry(id="axis_3", name="Individual vs Group", score=-0.7),
                            WeightEntry(id="axis_4", name="Stability vs Change", score=-0.1)
                        ]
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
                        weights=[
                            WeightEntry(id="axis_1", name="Logic vs Emotion", score=0.3),
                            WeightEntry(id="axis_2", name="Speed vs Caution", score=0.8),
                            WeightEntry(id="axis_3", name="Individual vs Group", score=0.6),
                            WeightEntry(id="axis_4", name="Stability vs Change", score=1.0)
                        ]
                    ),
                    Choice(
                        id="choice_3_2",
                        text="現在の安定した環境を維持する",
                        weights=[
                            WeightEntry(id="axis_1", name="Logic vs Emotion", score=0.5),
                            WeightEntry(id="axis_2", name="Speed vs Caution", score=-0.8),
                            WeightEntry(id="axis_3", name="Individual vs Group", score=-0.2),
                            WeightEntry(id="axis_4", name="Stability vs Change", score=-1.0)
                        ]
                    ),
                    Choice(
                        id="choice_3_3",
                        text="段階的に変化を取り入れて適応する",
                        weights=[
                            WeightEntry(id="axis_1", name="Logic vs Emotion", score=0.7),
                            WeightEntry(id="axis_2", name="Speed vs Caution", score=-0.3),
                            WeightEntry(id="axis_3", name="Individual vs Group", score=0.1),
                            WeightEntry(id="axis_4", name="Stability vs Change", score=0.2)
                        ]
                    ),
                    Choice(
                        id="choice_3_4",
                        text="周囲の意見を参考にして判断する",
                        weights=[
                            WeightEntry(id="axis_1", name="Logic vs Emotion", score=-0.2),
                            WeightEntry(id="axis_2", name="Speed vs Caution", score=-0.4),
                            WeightEntry(id="axis_3", name="Individual vs Group", score=-0.8),
                            WeightEntry(id="axis_4", name="Stability vs Change", score=-0.3)
                        ]
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
                        weights=[
                            WeightEntry(id="axis_1", name="Logic vs Emotion", score=1.0),
                            WeightEntry(id="axis_2", name="Speed vs Caution", score=-0.2),
                            WeightEntry(id="axis_3", name="Individual vs Group", score=0.4),
                            WeightEntry(id="axis_4", name="Stability vs Change", score=0.1)
                        ]
                    ),
                    Choice(
                        id="choice_4_2",
                        text="直感を信じて柔軟に対応する",
                        weights=[
                            WeightEntry(id="axis_1", name="Logic vs Emotion", score=-0.8),
                            WeightEntry(id="axis_2", name="Speed vs Caution", score=0.5),
                            WeightEntry(id="axis_3", name="Individual vs Group", score=0.2),
                            WeightEntry(id="axis_4", name="Stability vs Change", score=0.7)
                        ]
                    ),
                    Choice(
                        id="choice_4_3",
                        text="迅速に決断して行動で解決する",
                        weights=[
                            WeightEntry(id="axis_1", name="Logic vs Emotion", score=0.2),
                            WeightEntry(id="axis_2", name="Speed vs Caution", score=1.0),
                            WeightEntry(id="axis_3", name="Individual vs Group", score=0.7),
                            WeightEntry(id="axis_4", name="Stability vs Change", score=0.5)
                        ]
                    ),
                    Choice(
                        id="choice_4_4",
                        text="慎重に検討して確実な方法を選ぶ",
                        weights=[
                            WeightEntry(id="axis_1", name="Logic vs Emotion", score=0.6),
                            WeightEntry(id="axis_2", name="Speed vs Caution", score=-1.0),
                            WeightEntry(id="axis_3", name="Individual vs Group", score=-0.1),
                            WeightEntry(id="axis_4", name="Stability vs Change", score=-0.6)
                        ]
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
                dominantAxes=["axis_1", "axis_2"],
                polarity="Hi-Hi",
                meta={"cell": "A1", "isNeutral": False}
            ),
            TypeProfile(
                name="Wise Planner",
                description="慎重な計画性と論理的アプローチを重視するタイプ。安定性を求め、リスクを最小化した確実な成果を追求します。",
                keywords=["methodical", "careful", "reliable", "thorough"],
                dominantAxes=["axis_1", "axis_2"],
                polarity="Hi-Lo",
                meta={"cell": "A2", "isNeutral": False}
            ),
            TypeProfile(
                name="Creative Spark",
                description="感情と直感を大切にし、変化を恐れず新しい可能性に挑戦するタイプ。創造性と適応力が特徴です。",
                keywords=["creative", "adaptable", "innovative", "empathetic"],
                dominantAxes=["axis_1", "axis_4"],
                polarity="Lo-Hi",
                meta={"cell": "B1", "isNeutral": False}
            ),
            TypeProfile(
                name="Team Supporter",
                description="感情を重視し、安定した環境で他者をサポートすることを得意とするタイプ。協調性と共感力に優れています。",
                keywords=["supportive", "empathetic", "collaborative", "stable"],
                dominantAxes=["axis_1", "axis_3"],
                polarity="Lo-Lo",
                meta={"cell": "B2", "isNeutral": False}
            ),
            TypeProfile(
                name="Fast Innovator",
                description="迅速な行動力と変化への適応力を持つタイプ。新しいアイデアを素早く実現し、チームを活性化させます。",
                keywords=["dynamic", "innovative", "energetic", "flexible"],
                dominantAxes=["axis_2", "axis_4"],
                polarity="Hi-Hi",
                meta={"cell": "C1", "isNeutral": False}
            ),
            TypeProfile(
                name="Wise Mediator",
                description="バランス感覚に優れ、様々な観点を統合して最適解を見つけるタイプ。中庸を保ちながら調和を図ります。",
                keywords=["balanced", "diplomatic", "versatile", "integrative"],
                dominantAxes=["axis_3", "axis_4"],
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
                weights=[
                    WeightEntry(id="axis_1", name="Logic vs Emotion", score=1.0),
                    WeightEntry(id="axis_2", name="Speed vs Caution", score=-0.3),
                    WeightEntry(id="axis_3", name="Individual vs Group", score=0.2),
                    WeightEntry(id="axis_4", name="Stability vs Change", score=0.1)
                ]
            ),
            Choice(
                id=f"choice_{scene_index}_2",
                text="直感を信じて決める",
                weights=[
                    WeightEntry(id="axis_1", name="Logic vs Emotion", score=-1.0),
                    WeightEntry(id="axis_2", name="Speed vs Caution", score=0.4),
                    WeightEntry(id="axis_3", name="Individual vs Group", score=-0.1),
                    WeightEntry(id="axis_4", name="Stability vs Change", score=0.3)
                ]
            ),
            Choice(
                id=f"choice_{scene_index}_3",
                text="迅速に行動する",
                weights=[
                    WeightEntry(id="axis_1", name="Logic vs Emotion", score=0.2),
                    WeightEntry(id="axis_2", name="Speed vs Caution", score=1.0),
                    WeightEntry(id="axis_3", name="Individual vs Group", score=0.5),
                    WeightEntry(id="axis_4", name="Stability vs Change", score=0.6)
                ]
            ),
            Choice(
                id=f"choice_{scene_index}_4",
                text="慎重に検討する",
                weights=[
                    WeightEntry(id="axis_1", name="Logic vs Emotion", score=0.3),
                    WeightEntry(id="axis_2", name="Speed vs Caution", score=-1.0),
                    WeightEntry(id="axis_3", name="Individual vs Group", score=-0.3),
                    WeightEntry(id="axis_4", name="Stability vs Change", score=-0.5)
                ]
            )
        ]
    )
