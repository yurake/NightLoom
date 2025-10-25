"""
Test module for _build_enhanced_choices_data() function in external_llm.py

This test validates the field name conversion, choice text retrieval,
and error handling for the enhanced choices data building process.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import Mock, patch

from app.services.external_llm import ExternalLLMService
from app.models.session import (
    Session, SessionState, Scene, Choice, ChoiceRecord, Axis
)


class TestBuildEnhancedChoicesData:
    """Test cases for _build_enhanced_choices_data() function."""

    @pytest.fixture
    def sample_session(self):
        """Create a sample session with complete scenes and choices."""
        session_id = uuid4()
        
        # Create sample axes
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
            )
        ]
        
        # Create sample scenes with choices
        scenes = [
            Scene(
                sceneIndex=1,
                themeId="focus",
                narrative="重要な決断の時です。どうしますか？",
                choices=[
                    Choice(id="choice_1_1", text="すぐに決める", weights={"axis_1": 0.5, "axis_2": 0.8}),
                    Choice(id="choice_1_2", text="じっくり考える", weights={"axis_1": 0.3, "axis_2": -0.6}),
                    Choice(id="choice_1_3", text="相談する", weights={"axis_1": -0.2, "axis_2": 0.1}),
                    Choice(id="choice_1_4", text="直感で決める", weights={"axis_1": -0.7, "axis_2": 0.4})
                ]
            ),
            Scene(
                sceneIndex=2,
                themeId="focus",
                narrative="チームでの作業が始まります。",
                choices=[
                    Choice(id="choice_2_1", text="リーダーシップを取る", weights={"axis_1": 0.6, "axis_2": 0.3}),
                    Choice(id="choice_2_2", text="サポートに回る", weights={"axis_1": 0.2, "axis_2": -0.4}),
                    Choice(id="choice_2_3", text="様子を見る", weights={"axis_1": -0.1, "axis_2": -0.5}),
                    Choice(id="choice_2_4", text="積極的に参加", weights={"axis_1": 0.4, "axis_2": 0.7})
                ]
            )
        ]
        
        # Create choice records
        choice_records = [
            ChoiceRecord(
                sceneIndex=1,
                choiceId="choice_1_2",
                timestamp=datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
            ),
            ChoiceRecord(
                sceneIndex=2,
                choiceId="choice_2_1",
                timestamp=datetime(2025, 1, 15, 10, 35, 0, tzinfo=timezone.utc)
            )
        ]
        
        # Create session
        session = Session(
            id=session_id,
            state=SessionState.PLAY,
            initialCharacter="重",
            keywordCandidates=["重要", "重視", "重大", "重点"],
            selectedKeyword="重要",
            themeId="focus",
            axes=axes,
            scenes=scenes,
            choices=choice_records
        )
        
        return session

    @pytest.fixture
    def llm_service(self):
        """Create LLM service instance for testing."""
        return ExternalLLMService()

    def test_build_enhanced_choices_data_normal_case(self, llm_service, sample_session):
        """Test normal case with complete data."""
        # Execute
        result = llm_service._build_enhanced_choices_data(sample_session)
        
        # Verify
        assert len(result) == 2
        
        # Check first choice
        first_choice = result[0]
        assert first_choice["scene_index"] == 1
        assert first_choice["choice_id"] == "choice_1_2"
        assert first_choice["text"] == "じっくり考える"
        assert first_choice["timestamp"] == "2025-01-15T10:30:00+00:00"
        
        # Check second choice
        second_choice = result[1]
        assert second_choice["scene_index"] == 2
        assert second_choice["choice_id"] == "choice_2_1"
        assert second_choice["text"] == "リーダーシップを取る"
        assert second_choice["timestamp"] == "2025-01-15T10:35:00+00:00"

    def test_build_enhanced_choices_data_field_name_conversion(self, llm_service, sample_session):
        """Test field name conversion from sceneIndex/choiceId to scene_index/choice_id."""
        # Execute
        result = llm_service._build_enhanced_choices_data(sample_session)
        
        # Verify field names are converted correctly
        for choice_data in result:
            assert "scene_index" in choice_data
            assert "choice_id" in choice_data
            assert "sceneIndex" not in choice_data
            assert "choiceId" not in choice_data
            
            # Verify values are correctly transferred
            assert isinstance(choice_data["scene_index"], int)
            assert isinstance(choice_data["choice_id"], str)

    def test_build_enhanced_choices_data_choice_text_lookup(self, llm_service, sample_session):
        """Test choice text lookup from scenes."""
        # Execute
        result = llm_service._build_enhanced_choices_data(sample_session)
        
        # Verify text is correctly retrieved from scenes
        for choice_data in result:
            assert choice_data["text"] != ""
            assert isinstance(choice_data["text"], str)
            
        # Verify specific text matches
        choice_texts = {choice["choice_id"]: choice["text"] for choice in result}
        assert choice_texts["choice_1_2"] == "じっくり考える"
        assert choice_texts["choice_2_1"] == "リーダーシップを取る"

    def test_build_enhanced_choices_data_missing_scene(self, llm_service, sample_session):
        """Test handling when scene is not found."""
        # Setup: Remove one scene
        sample_session.scenes = [scene for scene in sample_session.scenes if scene.sceneIndex != 2]
        
        # Execute
        result = llm_service._build_enhanced_choices_data(sample_session)
        
        # Verify
        assert len(result) == 2
        
        # First choice should have text
        assert result[0]["text"] == "じっくり考える"
        
        # Second choice should have empty text (scene not found)
        assert result[1]["text"] == ""
        assert result[1]["choice_id"] == "choice_2_1"

    def test_build_enhanced_choices_data_missing_choice_in_scene(self, llm_service, sample_session):
        """Test handling when choice is not found in scene."""
        # Setup: Remove one choice from scene
        scene = sample_session.scenes[0]
        scene.choices = [choice for choice in scene.choices if choice.id != "choice_1_2"]
        
        # Execute
        result = llm_service._build_enhanced_choices_data(sample_session)
        
        # Verify
        assert len(result) == 2
        
        # First choice should have empty text (choice not found in scene)
        assert result[0]["text"] == ""
        assert result[0]["choice_id"] == "choice_1_2"
        
        # Second choice should have text
        assert result[1]["text"] == "リーダーシップを取る"

    def test_build_enhanced_choices_data_empty_choices(self, llm_service, sample_session):
        """Test handling with empty choices list."""
        # Setup: Clear choices
        sample_session.choices = []
        
        # Execute
        result = llm_service._build_enhanced_choices_data(sample_session)
        
        # Verify
        assert result == []

    def test_build_enhanced_choices_data_empty_scenes(self, llm_service, sample_session):
        """Test handling with empty scenes list."""
        # Setup: Clear scenes
        sample_session.scenes = []
        
        # Execute
        result = llm_service._build_enhanced_choices_data(sample_session)
        
        # Verify
        assert len(result) == 2  # choices still exist
        
        # All texts should be empty since no scenes
        for choice_data in result:
            assert choice_data["text"] == ""

    def test_build_enhanced_choices_data_none_timestamp(self, llm_service, sample_session):
        """Test handling when timestamp is None."""
        # Setup: Set timestamp to None
        sample_session.choices[0].timestamp = None
        
        # Execute
        result = llm_service._build_enhanced_choices_data(sample_session)
        
        # Verify
        assert result[0]["timestamp"] is None
        assert result[1]["timestamp"] == "2025-01-15T10:35:00+00:00"

    @patch('app.services.external_llm.logging.getLogger')
    def test_build_enhanced_choices_data_logging(self, mock_get_logger, llm_service, sample_session):
        """Test that appropriate logging occurs."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        # Execute
        result = llm_service._build_enhanced_choices_data(sample_session)
        
        # Verify logging calls
        mock_logger.debug.assert_called()
        mock_logger.info.assert_called_with(f"[Enhanced Choices] Built {len(result)} enhanced choice records")

    def test_build_enhanced_choices_data_complex_choice_ids(self, llm_service, sample_session):
        """Test with complex choice IDs containing special characters."""
        # Setup: Modify choice IDs
        sample_session.choices[0].choiceId = "choice_1_special-id_test"
        sample_session.scenes[0].choices[1].id = "choice_1_special-id_test"
        
        # Execute
        result = llm_service._build_enhanced_choices_data(sample_session)
        
        # Verify
        assert result[0]["choice_id"] == "choice_1_special-id_test"
        assert result[0]["text"] == "じっくり考える"

    def test_build_enhanced_choices_data_performance_with_large_dataset(self, llm_service):
        """Test performance and correctness with larger dataset."""
        # Setup: Create session with 4 scenes and 4 choices
        session_id = uuid4()
        scenes = []
        choice_records = []
        
        for scene_idx in range(1, 5):
            choices = []
            for choice_idx in range(1, 5):
                choice_id = f"choice_{scene_idx}_{choice_idx}"
                choices.append(Choice(
                    id=choice_id, 
                    text=f"Scene {scene_idx} Choice {choice_idx}",
                    weights={"axis_1": 0.1 * choice_idx}
                ))
            
            scenes.append(Scene(
                sceneIndex=scene_idx,
                themeId="focus",
                narrative=f"Scene {scene_idx} narrative",
                choices=choices
            ))
            
            # Add choice record for each scene
            choice_records.append(ChoiceRecord(
                sceneIndex=scene_idx,
                choiceId=f"choice_{scene_idx}_1",
                timestamp=datetime.now(timezone.utc)
            ))
        
        session = Session(
            id=session_id,
            state=SessionState.PLAY,
            initialCharacter="テ",
            keywordCandidates=["テスト", "テーブル", "テーマ", "テクニック"],
            selectedKeyword="テスト",
            themeId="focus",
            scenes=scenes,
            choices=choice_records
        )
        
        # Execute
        result = llm_service._build_enhanced_choices_data(session)
        
        # Verify
        assert len(result) == 4
        for i, choice_data in enumerate(result, 1):
            assert choice_data["scene_index"] == i
            assert choice_data["choice_id"] == f"choice_{i}_1"
            assert choice_data["text"] == f"Scene {i} Choice 1"

    def test_build_enhanced_choices_data_maintains_order(self, llm_service, sample_session):
        """Test that choice order is maintained."""
        # Add more choices in specific order
        additional_choices = [
            ChoiceRecord(
                sceneIndex=1,
                choiceId="choice_1_1",
                timestamp=datetime(2025, 1, 15, 10, 20, 0, tzinfo=timezone.utc)
            ),
            ChoiceRecord(
                sceneIndex=2,
                choiceId="choice_2_3",
                timestamp=datetime(2025, 1, 15, 10, 40, 0, tzinfo=timezone.utc)
            )
        ]
        
        # Insert at beginning to test order preservation
        sample_session.choices = additional_choices + sample_session.choices
        
        # Execute
        result = llm_service._build_enhanced_choices_data(sample_session)
        
        # Verify order is maintained
        assert len(result) == 4
        assert result[0]["choice_id"] == "choice_1_1"
        assert result[1]["choice_id"] == "choice_2_3"
        assert result[2]["choice_id"] == "choice_1_2"
        assert result[3]["choice_id"] == "choice_2_1"
