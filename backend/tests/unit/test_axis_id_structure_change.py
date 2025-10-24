"""
軸ID不整合修正 - Choice weightsの構造変更テスト

OpenAIが axis_1, axis_2 等の抽象的なIDを理解できない問題を解決するため、
weightsを配列形式に変更し、IDと名前の両方を提供する構造に変更する。

目標構造:
weights: [
  {"id": "axis_1", "name": "Logic vs Emotion", "score": 0.0},
  {"id": "axis_2", "name": "Speed vs Caution", "score": 0.0}
]
"""

import pytest
from pydantic import ValidationError
from app.models.session import Choice, WeightEntry


class TestAxisIdStructureChange:
    """軸ID構造変更のテスト"""
    
    def test_weight_entry_model_validation(self):
        """WeightEntryモデルのバリデーションテスト"""
        # 有効なWeightEntry
        valid_entry = WeightEntry(
            id="axis_1",
            name="Logic vs Emotion", 
            score=0.5
        )
        assert valid_entry.id == "axis_1"
        assert valid_entry.name == "Logic vs Emotion"
        assert valid_entry.score == 0.5
        
        # IDが空文字列の場合はエラー
        with pytest.raises(ValidationError):
            WeightEntry(id="", name="Logic vs Emotion", score=0.5)
        
        # nameが空文字列の場合はエラー  
        with pytest.raises(ValidationError):
            WeightEntry(id="axis_1", name="", score=0.5)
        
        # scoreが範囲外の場合はエラー
        with pytest.raises(ValidationError):
            WeightEntry(id="axis_1", name="Logic vs Emotion", score=1.5)
            
        with pytest.raises(ValidationError):
            WeightEntry(id="axis_1", name="Logic vs Emotion", score=-1.5)
    
    def test_choice_with_new_weights_structure(self):
        """新しいweights構造を持つChoiceのテスト"""
        # 新しい配列形式のweights
        new_format_choice = Choice(
            id="choice_1_1",
            text="論理的に分析する",
            weights=[
                WeightEntry(id="axis_1", name="Logic vs Emotion", score=0.8),
                WeightEntry(id="axis_2", name="Speed vs Caution", score=-0.3),
                WeightEntry(id="axis_3", name="Individual vs Group", score=0.1),
                WeightEntry(id="axis_4", name="Stability vs Change", score=0.0)
            ]
        )
        
        # weightsがリスト形式であることを確認
        assert isinstance(new_format_choice.weights, list)
        assert len(new_format_choice.weights) == 4
        
        # 各エントリーがWeightEntryであることを確認
        for weight in new_format_choice.weights:
            assert isinstance(weight, WeightEntry)
            assert weight.id.startswith("axis_")
            assert len(weight.name) > 0
            assert -1.0 <= weight.score <= 1.0
    
    def test_choice_get_weights_dict_compatibility(self):
        """後方互換性のためのget_weights_dictメソッドテスト"""
        # 新しい配列形式から辞書形式への変換
        array_choice = Choice(
            id="choice_1_1", 
            text="テスト選択肢",
            weights=[
                WeightEntry(id="axis_1", name="Logic vs Emotion", score=0.5),
                WeightEntry(id="axis_2", name="Speed vs Caution", score=-0.8)
            ]
        )
        
        weights_dict = array_choice.get_weights_dict()
        expected_dict = {"axis_1": 0.5, "axis_2": -0.8}
        
        assert weights_dict == expected_dict
        assert isinstance(weights_dict, dict)
        assert all(isinstance(v, (int, float)) for v in weights_dict.values())
    
    def test_choice_get_weights_array_method(self):
        """get_weights_arrayメソッドのテスト"""
        # 配列形式のweightsからの変換（そのまま返す）
        original_weights = [
            WeightEntry(id="axis_1", name="Logic vs Emotion", score=0.3),
            WeightEntry(id="axis_2", name="Speed vs Caution", score=-0.7)
        ]
        
        array_choice = Choice(
            id="choice_1_1",
            text="テスト選択肢", 
            weights=original_weights
        )
        
        weights_array = array_choice.get_weights_array()
        assert weights_array == original_weights
        assert isinstance(weights_array, list)
        assert all(isinstance(w, WeightEntry) for w in weights_array)
    
    def test_mixed_weights_format_handling(self):
        """新旧混合フォーマットの処理テスト"""
        # 辞書形式（レガシー）
        legacy_choice = Choice(
            id="choice_legacy",
            text="レガシー選択肢",
            weights={"axis_1": 0.4, "axis_2": -0.2}
        )
        
        # get_weights_arrayで配列形式に変換
        weights_array = legacy_choice.get_weights_array()
        assert isinstance(weights_array, list)
        assert len(weights_array) == 2
        
        # IDとスコアが正しく変換されている
        axis_1_entry = next(w for w in weights_array if w.id == "axis_1")
        axis_2_entry = next(w for w in weights_array if w.id == "axis_2")
        
        assert axis_1_entry.score == 0.4
        assert axis_2_entry.score == -0.2
        assert axis_1_entry.name == "Axis 1"  # フォールバック名
        assert axis_2_entry.name == "Axis 2"  # フォールバック名
    
    def test_openai_response_structure_validation(self):
        """OpenAI応答の新しい構造バリデーションテスト"""
        # OpenAIが生成すべき新しい構造
        openai_response_structure = {
            "scene": {
                "scene_index": 1,
                "narrative": "重要な決断を迫られています。あなたの価値観に最も近い選択肢を選んでください。",
                "choices": [
                    {
                        "id": "choice_1_1",
                        "text": "論理的に分析して決定する",
                        "weights": [
                            {"id": "axis_1", "name": "Logic vs Emotion", "score": 0.8},
                            {"id": "axis_2", "name": "Speed vs Caution", "score": -0.3},
                            {"id": "axis_3", "name": "Individual vs Group", "score": 0.1},
                            {"id": "axis_4", "name": "Stability vs Change", "score": 0.0}
                        ]
                    },
                    {
                        "id": "choice_1_2", 
                        "text": "直感を信じて即座に判断する",
                        "weights": [
                            {"id": "axis_1", "name": "Logic vs Emotion", "score": -0.7},
                            {"id": "axis_2", "name": "Speed vs Caution", "score": 0.9},
                            {"id": "axis_3", "name": "Individual vs Group", "score": 0.5},
                            {"id": "axis_4", "name": "Stability vs Change", "score": 0.2}
                        ]
                    },
                    {
                        "id": "choice_1_3",
                        "text": "チームメンバーと相談する", 
                        "weights": [
                            {"id": "axis_1", "name": "Logic vs Emotion", "score": 0.2},
                            {"id": "axis_2", "name": "Speed vs Caution", "score": -0.6},
                            {"id": "axis_3", "name": "Individual vs Group", "score": -0.8},
                            {"id": "axis_4", "name": "Stability vs Change", "score": -0.1}
                        ]
                    },
                    {
                        "id": "choice_1_4",
                        "text": "過去の経験を参考にする",
                        "weights": [
                            {"id": "axis_1", "name": "Logic vs Emotion", "score": 0.4},
                            {"id": "axis_2", "name": "Speed vs Caution", "score": -0.4},
                            {"id": "axis_3", "name": "Individual vs Group", "score": 0.0},
                            {"id": "axis_4", "name": "Stability vs Change", "score": -0.7}
                        ]
                    }
                ]
            }
        }
        
        # 各選択肢の構造を検証
        choices = openai_response_structure["scene"]["choices"]
        assert len(choices) == 4
        
        for choice_data in choices:
            # Choiceモデルで検証可能かテスト
            choice = Choice(
                id=choice_data["id"],
                text=choice_data["text"],
                weights=[
                    WeightEntry(**weight_data) 
                    for weight_data in choice_data["weights"]
                ]
            )
            
            # 基本的な構造検証
            assert choice.id.startswith("choice_")
            assert len(choice.text) > 0
            assert isinstance(choice.weights, list)
            assert len(choice.weights) == 4
            
            # 軸IDの一貫性検証
            weight_ids = {w.id for w in choice.weights}
            expected_ids = {"axis_1", "axis_2", "axis_3", "axis_4"}
            assert weight_ids == expected_ids, f"Expected {expected_ids}, got {weight_ids}"
            
            # 軸名の存在検証
            for weight in choice.weights:
                assert len(weight.name) > 0
                assert "vs" in weight.name or "⟷" in weight.name  # 軸名の形式
                assert -1.0 <= weight.score <= 1.0
    
    def test_backwards_compatibility_mixed_session(self):
        """新旧混合セッションでの後方互換性テスト"""
        # 一部は新形式、一部は旧形式の選択肢が混在するケース
        mixed_choices = [
            # 新形式
            Choice(
                id="choice_new",
                text="新形式選択肢",
                weights=[
                    WeightEntry(id="axis_1", name="Logic vs Emotion", score=0.5),
                    WeightEntry(id="axis_2", name="Speed vs Caution", score=-0.3)
                ]
            ),
            # 旧形式
            Choice(
                id="choice_legacy", 
                text="旧形式選択肢",
                weights={"axis_1": -0.2, "axis_2": 0.7}
            )
        ]
        
        # どちらもget_weights_dictで統一的に処理可能
        for choice in mixed_choices:
            weights_dict = choice.get_weights_dict()
            assert isinstance(weights_dict, dict)
            assert "axis_1" in weights_dict
            assert "axis_2" in weights_dict
            assert all(isinstance(v, (int, float)) for v in weights_dict.values())
            
        # どちらもget_weights_arrayで配列形式に変換可能
        for choice in mixed_choices:
            weights_array = choice.get_weights_array()
            assert isinstance(weights_array, list)
            assert all(isinstance(w, WeightEntry) for w in weights_array)
