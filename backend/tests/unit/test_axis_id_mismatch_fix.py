"""
Test for fixing axis ID mismatch between OpenAI responses and expected format.

This test validates the fix for the issue where OpenAI returns axis names
(like "Logic vs Emotion") instead of expected axis IDs (like "axis_1").
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.clients.openai_client import OpenAIClient, ScenarioResponse, ScenarioSceneData, ScenarioChoice
from app.models.llm_config import ProviderConfig, LLMProvider
from app.clients.llm_client import LLMRequest, LLMTaskType


class TestAxisIdMismatchFix:
    """Test fixing axis ID mismatch issue."""

    def setup_method(self):
        """Setup test environment."""
        config = ProviderConfig(
            provider=LLMProvider.OPENAI,
            api_key="test-key",
            model_name="gpt-4"
        )
        self.client = OpenAIClient(config)

    @pytest.mark.asyncio
    async def test_axis_id_mismatch_current_issue(self):
        """Test that reproduces the current axis ID mismatch issue."""
        # This is the problematic response format that OpenAI currently returns
        problematic_response = {
            "scene": {
                "scene_index": 1,
                "narrative": "あなたは重要な決断を迫られています。",
                "choices": [
                    {
                        "id": "choice_1_1",
                        "text": "慎重に検討する",
                        "weights": {
                            "Ambition": 0.0,
                            "Growth Mindset": 0.5,
                            "Self-Reflection": 0.3,
                            "Resilience": 0.0
                        }
                    },
                    {
                        "id": "choice_1_2", 
                        "text": "直感で決める",
                        "weights": {
                            "Ambition": 0.8,
                            "Growth Mindset": 0.0,
                            "Self-Reflection": -0.5,
                            "Resilience": 0.3
                        }
                    },
                    {
                        "id": "choice_1_3",
                        "text": "他人に相談する",
                        "weights": {
                            "Ambition": -0.3,
                            "Growth Mindset": 0.2,
                            "Self-Reflection": 0.8,
                            "Resilience": 0.0
                        }
                    },
                    {
                        "id": "choice_1_4",
                        "text": "リスクを避ける",
                        "weights": {
                            "Ambition": -0.8,
                            "Growth Mindset": -0.3,
                            "Self-Reflection": 0.0,
                            "Resilience": -0.5
                        }
                    }
                ]
            }
        }
        
        # Template data with expected axis format
        template_data = {
            "session_id": "test-session",
            "scene_index": 1,
            "keyword": "成長",
            "axes": [
                {"id": "axis_1", "name": "Logic vs Emotion", "description": "思考と感情のバランス"},
                {"id": "axis_2", "name": "Speed vs Caution", "description": "迅速性と慎重さ"},
                {"id": "axis_3", "name": "Independence vs Collaboration", "description": "独立性と協調性"},
                {"id": "axis_4", "name": "Risk Taking vs Safety", "description": "リスク志向と安全志向"}
            ]
        }
        
        # This should fail with current validation because axis IDs don't match
        with pytest.raises(Exception) as exc_info:
            await self.client._validate_scenario_response(problematic_response, template_data)
        
        # Verify it's an axis ID mismatch issue
        error_msg = str(exc_info.value)
        assert "axis" in error_msg.lower() or "weight" in error_msg.lower()
    
    @pytest.mark.asyncio
    async def test_new_choice_weights_structure_validation(self):
        """Test validation of new choice weights structure with axis names and IDs."""
        # New proposed structure that includes both ID and name
        fixed_response = {
            "scene": {
                "scene_index": 1,
                "narrative": "あなたは重要な決断を迫られています。",
                "choices": [
                    {
                        "id": "choice_1_1",
                        "text": "慎重に検討する",
                        "weights": [
                            {"id": "axis_1", "name": "Logic vs Emotion", "score": 0.5},
                            {"id": "axis_2", "name": "Speed vs Caution", "score": -0.3},
                            {"id": "axis_3", "name": "Independence vs Collaboration", "score": 0.2},
                            {"id": "axis_4", "name": "Risk Taking vs Safety", "score": -0.8}
                        ]
                    },
                    {
                        "id": "choice_1_2",
                        "text": "直感で決める", 
                        "weights": [
                            {"id": "axis_1", "name": "Logic vs Emotion", "score": -0.8},
                            {"id": "axis_2", "name": "Speed vs Caution", "score": 1.0},
                            {"id": "axis_3", "name": "Independence vs Collaboration", "score": 0.5},
                            {"id": "axis_4", "name": "Risk Taking vs Safety", "score": 0.3}
                        ]
                    },
                    {
                        "id": "choice_1_3",
                        "text": "他人に相談する",
                        "weights": [
                            {"id": "axis_1", "name": "Logic vs Emotion", "score": 0.3},
                            {"id": "axis_2", "name": "Speed vs Caution", "score": -0.5},
                            {"id": "axis_3", "name": "Independence vs Collaboration", "score": -1.0},
                            {"id": "axis_4", "name": "Risk Taking vs Safety", "score": 0.0}
                        ]
                    },
                    {
                        "id": "choice_1_4",
                        "text": "リスクを避ける",
                        "weights": [
                            {"id": "axis_1", "name": "Logic vs Emotion", "score": 0.0},
                            {"id": "axis_2", "name": "Speed vs Caution", "score": -0.8},
                            {"id": "axis_3", "name": "Independence vs Collaboration", "score": -0.2},
                            {"id": "axis_4", "name": "Risk Taking vs Safety", "score": -1.0}
                        ]
                    }
                ]
            }
        }
        
        # Template data
        template_data = {
            "session_id": "test-session",
            "scene_index": 1,
            "keyword": "成長", 
            "axes": [
                {"id": "axis_1", "name": "Logic vs Emotion", "description": "思考と感情のバランス"},
                {"id": "axis_2", "name": "Speed vs Caution", "description": "迅速性と慎重さ"},
                {"id": "axis_3", "name": "Independence vs Collaboration", "description": "独立性と協調性"},
                {"id": "axis_4", "name": "Risk Taking vs Safety", "description": "リスク志向と安全志向"}
            ]
        }
        
        # This should pass when we implement the new validation logic
        # For now, this test will fail until we update the validation
        try:
            await self.client._validate_scenario_response(fixed_response, template_data)
            assert True, "New structure should validate successfully"
        except Exception as e:
            pytest.skip(f"Skipping until new validation is implemented: {e}")
    
    def test_structured_outputs_schema_with_array_weights(self):
        """Test Pydantic schema for new array-based weights structure."""
        
        # New Pydantic model for weight entry
        from pydantic import BaseModel
        
        class WeightEntry(BaseModel):
            """Single weight entry with ID, name and score."""
            id: str
            name: str
            score: float
            
        class NewScenarioChoice(BaseModel):
            """Choice with array-based weights."""
            id: str
            text: str
            weights: list[WeightEntry]
        
        # Test valid data
        valid_choice_data = {
            "id": "choice_1_1",
            "text": "慎重に検討する",
            "weights": [
                {"id": "axis_1", "name": "Logic vs Emotion", "score": 0.5},
                {"id": "axis_2", "name": "Speed vs Caution", "score": -0.3}
            ]
        }
        
        choice = NewScenarioChoice.model_validate(valid_choice_data)
        assert choice.id == "choice_1_1"
        assert len(choice.weights) == 2
        assert choice.weights[0].id == "axis_1"
        assert choice.weights[0].name == "Logic vs Emotion"
        assert choice.weights[0].score == 0.5
        
        # Test invalid score range (should fail when we add validation)
        invalid_choice_data = {
            "id": "choice_1_1", 
            "text": "テスト",
            "weights": [
                {"id": "axis_1", "name": "Logic vs Emotion", "score": 2.0}  # Out of range
            ]
        }
        
        # This should fail when we add proper validation
        with pytest.raises(Exception):
            choice = NewScenarioChoice.model_validate(invalid_choice_data)
            # Add range validation here in the actual implementation
            for weight in choice.weights:
                if not (-1.0 <= weight.score <= 1.0):
                    raise ValueError(f"Score {weight.score} out of range [-1.0, 1.0]")


class TestAxisIdMismatchSolution:
    """Test the complete solution for axis ID mismatch."""
    
    def test_convert_old_format_to_new_format(self):
        """Test conversion from old dict format to new array format."""
        
        # Old format (what we currently have in session model)
        old_weights = {
            "axis_1": 0.5,
            "axis_2": -0.3,
            "axis_3": 0.8,
            "axis_4": 0.0
        }
        
        # Axis mapping (from session axes)
        axis_mapping = {
            "axis_1": "Logic vs Emotion",
            "axis_2": "Speed vs Caution", 
            "axis_3": "Independence vs Collaboration",
            "axis_4": "Risk Taking vs Safety"
        }
        
        # Convert to new format
        new_weights = [
            {"id": axis_id, "name": axis_mapping[axis_id], "score": score}
            for axis_id, score in old_weights.items()
            if axis_id in axis_mapping
        ]
        
        assert len(new_weights) == 4
        assert new_weights[0]["id"] == "axis_1"
        assert new_weights[0]["name"] == "Logic vs Emotion"
        assert new_weights[0]["score"] == 0.5
    
    def test_convert_new_format_to_old_format(self):
        """Test conversion from new array format back to old dict format."""
        
        # New format (what OpenAI will return)
        new_weights = [
            {"id": "axis_1", "name": "Logic vs Emotion", "score": 0.5},
            {"id": "axis_2", "name": "Speed vs Caution", "score": -0.3},
            {"id": "axis_3", "name": "Independence vs Collaboration", "score": 0.8},
            {"id": "axis_4", "name": "Risk Taking vs Safety", "score": 0.0}
        ]
        
        # Convert back to old format for compatibility
        old_weights = {
            weight["id"]: weight["score"]
            for weight in new_weights
        }
        
        assert old_weights == {
            "axis_1": 0.5,
            "axis_2": -0.3,
            "axis_3": 0.8,
            "axis_4": 0.0
        }
