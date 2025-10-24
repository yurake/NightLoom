
"""
T034 [P] [US3] Choice weights validation test
"""

import pytest
from backend.app.services.external_llm import ExternalLLMService
from backend.app.models.session import Session, Axis
from uuid import uuid4


class TestChoiceWeightsValidation:
    """選択肢重みのバリデーションテスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.llm_service = ExternalLLMService()
        self.session = Session(
            id=uuid4(),
            selected_keyword="テスト",
            axes=[
                Axis(id="axis_1", name="軸1", description="テスト軸1", direction="低い⟷高い"),
                Axis(id="axis_2", name="軸2", description="テスト軸2", direction="内向⟷外向")
            ]
        )
    
    def test_validate_choice_weights_valid_format(self):
        """有効な選択肢重みフォーマットのテスト"""
        valid_choices = [
            {
                "id": "choice_1",
                "text": "選択肢1",
                "weights": {"axis_1": 1.0, "axis_2": 0.0}
            },
            {
                "id": "choice_2", 
                "text": "選択肢2",
                "weights": {"axis_1": 0.0, "axis_2": 1.0}
            },
            {
                "id": "choice_3",
                "text": "選択肢3",
                "weights": {"axis_1": -1.0, "axis_2": 0.0}
            },
            {
                "id": "choice_4",
                "text": "選択肢4",
                "weights": {"axis_1": 0.0, "axis_2": -1.0}
            }
        ]
        
        # Should not raise any exceptions
        for choice in valid_choices:
            self._validate_single_choice(choice)
    
    def test_validate_choice_weights_range_validation(self):
        """重み値の範囲バリデーションテスト"""
        # Valid ranges [-1.0, 1.0]
        valid_weights = [
            {"axis_1": -1.0, "axis_2": 1.0},
            {"axis_1": 0.0, "axis_2": 0.5},
            {"axis_1": 0.25, "axis_2": -0.75},
            {"axis_1": 1.0, "axis_2": -1.0}
        ]
        
        for weights in valid_weights:
            choice = {
                "id": "test_choice",
                "text": "テスト選択肢",
                "weights": weights
            }
            # Should not raise exceptions
            self._validate_single_choice(choice)
    
    def test_validate_choice_weights_invalid_range(self):
        """無効な重み値範囲のテスト"""
        invalid_weights = [
            {"axis_1": 1.1, "axis_2": 0.0},  # Over upper bound
            {"axis_1": 0.0, "axis_2": -1.1},  # Under lower bound
            {"axis_1": 2.0, "axis_2": 0.5},  # Way over upper bound
            {"axis_1": -2.0, "axis_2": 0.0}  # Way under lower bound
        ]
        
        for weights in invalid_weights:
            choice = {
                "id": "test_choice",
                "text": "テスト選択肢",
                "weights": weights
            }
            with pytest.raises(ValueError, match="Weight value must be between -1.0 and 1.0"):
                self._validate_single_choice(choice)
    
    def test_validate_choice_weights_missing_axes(self):
        """不足している軸の重みテスト"""
        # Missing axis_2
        incomplete_weights = {"axis_1": 0.5}
        
        choice = {
            "id": "test_choice",
            "text": "テスト選択肢", 
            "weights": incomplete_weights
        }
        
        with pytest.raises(ValueError, match="Missing weight for axis"):
            self._validate_single_choice(choice)
    
    def test_validate_choice_weights_extra_axes(self):
        """余分な軸の重みテスト"""
        # Extra axis not in session
        extra_weights = {
            "axis_1": 0.5,
            "axis_2": 0.0,
            "axis_3": 0.8  # Not in session axes
        }
        
        choice = {
            "id": "test_choice",
            "text": "テスト選択肢",
            "weights": extra_weights
        }
        
        # Should accept extra axes but warn (implementation dependent)
        self._validate_single_choice(choice)
    
    def test_validate_choice_weights_invalid_type(self):
        """無効な重み値タイプのテスト"""
        invalid_type_weights = [
            {"axis_1": "invalid", "axis_2": 0.0},  # String instead of number
            {"axis_1": 0.5, "axis_2": None},  # None instead of number
            {"axis_1": [], "axis_2": 0.0},  # List instead of number
            {"axis_1": 0.0, "axis_2": {}}  # Dict instead of number
        ]
        
        for weights in invalid_type_weights:
            choice = {
                "id": "test_choice",
                "text": "テスト選択肢",
                "weights": weights
            }
            with pytest.raises((ValueError, TypeError)):
                self._validate_single_choice(choice)
    
    def test_validate_choices_collection_count(self):
        """選択肢コレクションの数バリデーション"""
        # Valid: exactly 4 choices
        valid_choices = [
            {"id": f"choice_{i}", "text": f"選択肢{i}", "weights": {"axis_1": 0.0, "axis_2": 0.0}}
            for i in range(1, 5)
        ]
        self._validate_choices_collection(valid_choices)
        
        # Invalid: too few choices
        with pytest.raises(ValueError, match="Expected exactly 4 choices"):
            self._validate_choices_collection(valid_choices[:3])
        
        # Invalid: too many choices
        extra_choice = {"id": "choice_5", "text": "選択肢5", "weights": {"axis_1": 0.0, "axis_2": 0.0}}
        with pytest.raises(ValueError, match="Expected exactly 4 choices"):
            self._validate_choices_collection(valid_choices + [extra_choice])
    
    def test_validate_choices_unique_ids(self):
        """選択肢IDの一意性テスト"""
        # Duplicate IDs
        duplicate_choices = [
            {"id": "choice_1", "text": "選択肢1", "weights": {"axis_1": 1.0, "axis_2": 0.0}},
            {"id": "choice_1", "text": "選択肢1重複", "weights": {"axis_1": 0.0, "axis_2": 1.0}},  # Duplicate ID
            {"id": "choice_3", "text": "選択肢3", "weights": {"axis_1": -1.0, "axis_2": 0.0}},
            {"id": "choice_4", "text": "選択肢4", "weights": {"axis_1": 0.0, "axis_2": -1.0}}
        ]
        
        with pytest.raises(ValueError, match="Duplicate choice ID"):
            self._validate_choices_collection(duplicate_choices)
    
    def test_validate_choice_weights_balance(self):
        """選択肢重みのバランステスト"""
        # Well-balanced choices across axes
        balanced_choices = [
            {"id": "choice_1", "text": "高axis1低axis2", "weights": {"axis_1": 1.0, "axis_2": -1.0}},
            {"id": "choice_2", "text": "低axis1高axis2", "weights": {"axis_1": -1.0, "axis_2": 1.0}},
            {"id": "choice_3", "text": "高axis1高axis2", "weights": {"axis_1": 1.0, "axis_2": 1.0}},
            {"id": "choice_4", "text": "低axis1低axis2", "weights": {"axis_1": -1.0, "axis_2": -1.0}}
        ]
        
        balance_result = self._check_weight_balance(balanced_choices)
        assert balance_result["balanced"], "Choices should be well-balanced across axes"
        
        # Poorly balanced choices (all positive for axis_1)
        unbalanced_choices = [
            {"id": "choice_1", "text": "選択肢1", "weights": {"axis_1": 1.0, "axis_2": 0.0}},
            {"id": "choice_2", "text": "選択肢2", "weights": {"axis_1": 0.8, "axis_2": 0.5}},
            {"id": "choice_3", "text": "選択肢3", "weights": {"axis_1": 0.6, "axis_2": -0.3}},
            {"id": "choice_4", "text": "選択肢4", "weights": {"axis_1": 0.9, "axis_2": 0.2}}
        ]
        
        balance_result = self._check_weight_balance(unbalanced_choices)
        assert not balance_result["balanced"], "Choices should be detected as unbalanced"
    
    def _validate_single_choice(self, choice):
        """単一選択肢のバリデーション"""
        if "weights" not in choice:
            raise ValueError("Choice must have weights")
        
        weights = choice["weights"]
        
        # Check all required axes are present
        for axis in self.session.axes:
            if axis.id not in weights:
                raise ValueError(f"Missing weight for axis: {axis.id}")
        
        # Validate weight values
        for axis_id, weight in weights.items():
            if not isinstance(weight, (int, float)):
                raise TypeError(f"Weight for {axis_id} must be a number, got {type(weight)}")
            
            if not (-1.0 <= weight <= 1.0):
                raise ValueError(f"Weight value must be between -1.0 and 1.0, got {weight} for {axis_id}")
    
    def _validate_choices_collection(self, choices):
        """選択肢コレクション全体のバリデーション"""
        if len(choices) != 4:
            raise ValueError(f"Expected exactly 4 choices, got {len(choices)}")
        
        # Check for unique IDs
        choice_ids = [choice["id"] for choice in choices]
        if len(set(choice_ids)) != len(choice_ids):
            raise ValueError("Duplicate choice ID found")
        
        # Validate each choice
        for choice in choices:
            self._validate_single_choice(choice)
    
    def _check_weight_balance(self, choices):
        """選択肢重みのバランスをチェック"""
        axis_sums = {}
        
        # Calculate sum of weights for each axis
        for axis in self.session.axes:
            axis_sums[axis.id] = sum(choice["weights"].get(axis.id, 0.0) for choice in choices)
        
        # Check if sums are reasonably balanced (close to 0)
        threshold = 1.5  # Allow some imbalance
        balanced = all(abs(total) <= threshold for total in axis_sums.values())
        
        return {
            "balanced": balanced,
            "axis_sums": axis_sums,
            "threshold": threshold
        }


class TestChoiceWeightsIntegration:
    """選択肢重みの統合テスト"""
    
    @pytest.mark.asyncio
    async def test_llm_generated_weights_validation(self):
        """LLM生成重みの検証統合テスト"""
        # This test would use actual LLM service in a controlled manner
        # For now, we'll simulate the validation process
        
        session = Session(
            id=uuid4(),
            selected_keyword="統合テスト",
            axes=[
                Axis(id="axis_1", name="論理性", description="論理的思考の傾向", direction="感情⟷論理"),
                Axis(id="axis_2", name="迅速性", description="迅速な判断の傾向", direction="慎重⟷迅速")
            ]
        )
        
        # Simulate LLM-generated scenario response
        llm_response = {
            "scene": {
                "scene_index": 1,
                "narrative": "重要な決定を迫られています。",
                "choices": [
                    {"id": "choice_1_1", "text": "データを分析してから判断", "weights": {"axis_1": 1.0, "axis_2": -0.5}},
                    {"id": "choice_1_2", "text": "直感で即座に決定", "weights": {"axis_1": -0.8, "axis_2": 1.0}},
                    {"id": "choice_1_3", "text": "チームと相談", "weights": {"axis_1": 0.3, "axis_2": -0.3}},
                    {"id": "choice_1_4", "text": "過去の経験を参考", "weights": {"axis_1": 0.5, "axis_2": 0.0}}
                ]
            }
        }
        
        # Validate generated choices
        choices = llm_response["scene"]["choices"]
        
        # All validation checks should pass
        assert len(choices) == 4, "Should have exactly 4 choices"
        
        choice_ids = [choice["id"] for choice in choices]
        assert len(set(choice_ids)) == 4, "All choice IDs should be unique"
        
        for choice in choices:
            assert "weights" in choice, f"Choice {choice['id']} must have weights"
            weights = choice["weights"]
            
            # Check required axes
            assert "axis_1" in weights, f"Choice {choice['id']} missing axis_1 weight"
            assert "axis_2" in weights, f"Choice {choice['id']} missing axis_2 weight"
            
            # Check weight ranges
            for axis_id, weight in weights.items():
                assert isinstance(weight, (int, float)), f"Weight must be numeric for {axis_id}"
                assert -1.0 <= weight <= 1.0, f"Weight {weight} out of range for {axis_id}"
        
        # Check balance
        axis1_sum = sum(choice["weights"]["axis_1"] for choice in choices)
        axis2_sum = sum(choice["weights"]["axis_2"] for choice in choices)
        
        # Should be reasonably balanced
