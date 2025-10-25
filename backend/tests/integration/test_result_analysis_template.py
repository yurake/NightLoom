"""
Integration test module for result analysis template functionality.

Tests template rendering, variable access, and session integration 
for the result analysis workflow.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock

from app.services.external_llm import ExternalLLMService
from app.services.prompt_template import get_template_manager
from app.models.session import (
    Session, SessionState, Scene, Choice, ChoiceRecord, Axis, TypeProfile
)
from app.clients.llm_client import LLMResponse, LLMTaskType


class TestResultAnalysisTemplate:
    """Integration tests for result analysis template functionality."""

    @pytest.fixture
    def complete_session(self):
        """Create a complete session ready for result analysis."""
        session_id = uuid4()
        
        # Create evaluation axes
        axes = [
            Axis(
                id="axis_1",
                name="Logic vs Emotion",
                description="Balance between analytical and intuitive decision making",
                direction="論理的 ⟷ 感情的"
            ),
            Axis(
                id="axis_2", 
                name="Speed vs Caution",
                description="Decision making pace and thoroughness",
                direction="素早い ⟷ 慎重"
            ),
            Axis(
                id="axis_3",
                name="Individual vs Group",
                description="Preference for solo or collaborative work",
                direction="個人主義 ⟷ 協調性"
            )
        ]
        
        # Create scenes with realistic choices
        scenes = []
        for scene_idx in range(1, 5):
            choices = [
                Choice(
                    id=f"choice_{scene_idx}_1",
                    text=f"Scene {scene_idx} - 論理的な選択",
                    weights={"axis_1": 0.8, "axis_2": -0.3, "axis_3": 0.2}
                ),
                Choice(
                    id=f"choice_{scene_idx}_2", 
                    text=f"Scene {scene_idx} - 感情的な選択",
                    weights={"axis_1": -0.7, "axis_2": 0.4, "axis_3": -0.1}
                ),
                Choice(
                    id=f"choice_{scene_idx}_3",
                    text=f"Scene {scene_idx} - 慎重な選択", 
                    weights={"axis_1": 0.1, "axis_2": -0.8, "axis_3": 0.3}
                ),
                Choice(
                    id=f"choice_{scene_idx}_4",
                    text=f"Scene {scene_idx} - 協調的な選択",
                    weights={"axis_1": -0.2, "axis_2": 0.1, "axis_3": 0.9}
                )
            ]
            
            scene = Scene(
                sceneIndex=scene_idx,
                themeId="analytical",
                narrative=f"Scene {scene_idx}: 重要な決断の時です。",
                choices=choices
            )
            scenes.append(scene)
        
        # Create choice records
        choice_records = [
            ChoiceRecord(
                sceneIndex=1,
                choiceId="choice_1_1",
                timestamp=datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
            ),
            ChoiceRecord(
                sceneIndex=2,
                choiceId="choice_2_3", 
                timestamp=datetime(2025, 1, 15, 10, 35, 0, tzinfo=timezone.utc)
            ),
            ChoiceRecord(
                sceneIndex=3,
                choiceId="choice_3_2",
                timestamp=datetime(2025, 1, 15, 10, 40, 0, tzinfo=timezone.utc)
            ),
            ChoiceRecord(
                sceneIndex=4,
                choiceId="choice_4_4",
                timestamp=datetime(2025, 1, 15, 10, 45, 0, tzinfo=timezone.utc)
            )
        ]
        
        # Create session with calculated scores
        session = Session(
            id=session_id,
            state=SessionState.PLAY,
            initialCharacter="分",
            keywordCandidates=["分析", "分類", "分野", "分担"],
            selectedKeyword="分析",
            themeId="analytical",
            axes=axes,
            scenes=scenes,
            choices=choice_records,
            rawScores={
                "axis_1": 1.0,   # Logic-leaning
                "axis_2": -1.0,  # Caution-leaning  
                "axis_3": 1.4    # Group-leaning
            },
            normalizedScores={
                "axis_1": 60.0,  # Slightly logical
                "axis_2": 40.0,  # Slightly cautious
                "axis_3": 64.0   # Group-oriented
            }
        )
        
        return session

    @pytest.fixture
    def llm_service(self):
        """Create LLM service instance."""
        return ExternalLLMService()

    @pytest.fixture
    def mock_template_manager(self):
        """Create mock template manager."""
        mock_manager = Mock()
        mock_manager.render_template = Mock()
        return mock_manager

    def test_template_data_preparation(self, llm_service, complete_session):
        """Test that template data is correctly prepared for result analysis."""
        # Execute: Build enhanced choices data
        enhanced_choices = llm_service._build_enhanced_choices_data(complete_session)
        
        # Prepare template data (simulating analyze_results method preparation)
        template_data = {
            "session_id": str(complete_session.id),
            "keyword": complete_session.selectedKeyword,
            "axes": [axis.model_dump() for axis in complete_session.axes],
            "scores": complete_session.normalizedScores,
            "choices": enhanced_choices,
            "raw_scores": complete_session.rawScores
        }
        
        # Verify template data structure
        assert template_data["session_id"] == str(complete_session.id)
        assert template_data["keyword"] == "分析"
        assert len(template_data["axes"]) == 3
        assert template_data["scores"]["axis_1"] == 60.0
        assert template_data["raw_scores"]["axis_1"] == 1.0
        assert len(template_data["choices"]) == 4

    def test_session_id_variable_access(self, llm_service, complete_session):
        """Test that session_id variable is properly accessible in template."""
        enhanced_choices = llm_service._build_enhanced_choices_data(complete_session)
        
        template_data = {
            "session_id": str(complete_session.id),
            "keyword": complete_session.selectedKeyword,
            "axes": [axis.model_dump() for axis in complete_session.axes],
            "scores": complete_session.normalizedScores,
            "choices": enhanced_choices,
            "raw_scores": complete_session.rawScores
        }
        
        # Verify session_id is properly formatted
        assert "session_id" in template_data
        assert isinstance(template_data["session_id"], str)
        assert len(template_data["session_id"]) == 36  # UUID string length
        assert template_data["session_id"] == str(complete_session.id)

    def test_raw_scores_variable_access(self, llm_service, complete_session):
        """Test that raw_scores variable is accessible and correctly formatted."""
        enhanced_choices = llm_service._build_enhanced_choices_data(complete_session)
        
        template_data = {
            "session_id": str(complete_session.id),
            "keyword": complete_session.selectedKeyword,
            "axes": [axis.model_dump() for axis in complete_session.axes],
            "scores": complete_session.normalizedScores,
            "choices": enhanced_choices,
            "raw_scores": complete_session.rawScores
        }
        
        # Verify raw_scores structure and content
        assert "raw_scores" in template_data
        assert isinstance(template_data["raw_scores"], dict)
        assert template_data["raw_scores"]["axis_1"] == 1.0
        assert template_data["raw_scores"]["axis_2"] == -1.0
        assert template_data["raw_scores"]["axis_3"] == 1.4

    def test_enhanced_choices_data_format(self, llm_service, complete_session):
        """Test that enhanced choices data is in correct format for template."""
        enhanced_choices = llm_service._build_enhanced_choices_data(complete_session)
        
        # Verify enhanced choices structure
        assert len(enhanced_choices) == 4
        
        for choice_data in enhanced_choices:
            # Verify required fields
            assert "scene_index" in choice_data
            assert "choice_id" in choice_data  
            assert "text" in choice_data
            assert "timestamp" in choice_data
            
            # Verify field name conversion (not original field names)
            assert "sceneIndex" not in choice_data
            assert "choiceId" not in choice_data
            
            # Verify data types
            assert isinstance(choice_data["scene_index"], int)
            assert isinstance(choice_data["choice_id"], str)
            assert isinstance(choice_data["text"], str)

    def test_choice_text_display_integration(self, llm_service, complete_session):
        """Test that choice texts are properly retrieved for display."""
        enhanced_choices = llm_service._build_enhanced_choices_data(complete_session)
        
        # Verify choice texts match expected patterns
        choice_texts = [choice["text"] for choice in enhanced_choices]
        
        assert "Scene 1 - 論理的な選択" in choice_texts
        assert "Scene 2 - 慎重な選択" in choice_texts
        assert "Scene 3 - 感情的な選択" in choice_texts  
        assert "Scene 4 - 協調的な選択" in choice_texts

    def test_template_data_with_missing_raw_scores(self, llm_service, complete_session):
        """Test template data preparation when raw_scores is missing."""
        # Setup: Clear raw scores
        complete_session.rawScores = {}
        
        enhanced_choices = llm_service._build_enhanced_choices_data(complete_session)
        
        template_data = {
            "session_id": str(complete_session.id),
            "keyword": complete_session.selectedKeyword,
            "axes": [axis.model_dump() for axis in complete_session.axes],
            "scores": complete_session.normalizedScores,
            "choices": enhanced_choices,
            "raw_scores": complete_session.rawScores if complete_session.rawScores else {}
        }
        
        # Verify empty raw_scores is handled properly
        assert template_data["raw_scores"] == {}
        assert "raw_scores" in template_data  # Key should still exist

    def test_template_data_with_missing_normalized_scores(self, llm_service, complete_session):
        """Test template data preparation when normalized scores is missing."""
        # Setup: Clear normalized scores
        complete_session.normalizedScores = {}
        
        enhanced_choices = llm_service._build_enhanced_choices_data(complete_session)
        
        template_data = {
            "session_id": str(complete_session.id),
            "keyword": complete_session.selectedKeyword,
            "axes": [axis.model_dump() for axis in complete_session.axes],
            "scores": complete_session.normalizedScores if complete_session.normalizedScores else {},
            "choices": enhanced_choices,
            "raw_scores": complete_session.rawScores
        }
        
        # Verify empty scores is handled properly
        assert template_data["scores"] == {}
        assert "scores" in template_data

    @patch('app.services.external_llm.get_template_manager')
    def test_template_rendering_integration(self, mock_get_template_manager, llm_service, complete_session):
        """Test template rendering integration with template manager."""
        # Setup mock
        mock_manager = Mock()
        mock_get_template_manager.return_value = mock_manager
        
        # Create service with mocked template manager
        service = ExternalLLMService()
        
        # Prepare template data
        enhanced_choices = service._build_enhanced_choices_data(complete_session)
        template_data = {
            "session_id": str(complete_session.id),
            "keyword": complete_session.selectedKeyword,
            "axes": [axis.model_dump() for axis in complete_session.axes],
            "scores": complete_session.normalizedScores,
            "choices": enhanced_choices,
            "raw_scores": complete_session.rawScores
        }
        
        # Verify template manager is properly initialized
        assert service.template_manager == mock_manager

    def test_axes_data_structure_in_template(self, llm_service, complete_session):
        """Test that axes data maintains proper structure for template access."""
        template_data = {
            "axes": [axis.model_dump() for axis in complete_session.axes]
        }
        
        # Verify axes structure
        axes_data = template_data["axes"]
        assert len(axes_data) == 3
        
        for axis_data in axes_data:
            assert "id" in axis_data
            assert "name" in axis_data
            assert "description" in axis_data
            assert "direction" in axis_data
        
        # Verify specific axis data
        axis_ids = [axis["id"] for axis in axes_data]
        assert "axis_1" in axis_ids
        assert "axis_2" in axis_ids
        assert "axis_3" in axis_ids

    def test_keyword_context_integration(self, llm_service, complete_session):
        """Test keyword context is properly integrated for analysis."""
        template_data = {
            "keyword": complete_session.selectedKeyword
        }
        
        # Verify keyword context
        assert template_data["keyword"] == "分析"
        assert isinstance(template_data["keyword"], str)
        assert len(template_data["keyword"]) > 0

    @pytest.mark.asyncio
    async def test_full_template_integration_workflow(self, llm_service, complete_session):
        """Test full integration workflow from session to template data."""
        
        # Mock LLM client response
        mock_response = LLMResponse(
            task_type=LLMTaskType.RESULT_ANALYSIS,
            session_id=str(complete_session.id),
            content={
                "type_profiles": [
                    {
                        "typeName": "Analytical",
                        "name": "Analytical",
                        "description": "論理的思考を重視し、慎重に判断する傾向",
                        "keywords": ["logical", "analytical", "cautious"],
                        "dominantAxes": ["axis_1", "axis_2"],
                        "polarity": "Hi-Lo"
                    }
                ]
            },
            provider="openai",
            model_name="gpt-4",
            tokens_used=250,
            cost_estimate=0.005
        )
        
        with patch.object(llm_service, '_execute_with_fallback', return_value=mock_response):
            # Execute analyze_results which uses template integration
            result_profiles = await llm_service.analyze_results(complete_session)
            
            # Verify integration was successful
            assert len(result_profiles) == 1
            assert result_profiles[0].name == "Analytical"
            assert result_profiles[0].polarity == "Hi-Lo"
