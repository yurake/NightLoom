"""
Test module for score consistency and session update timing.

Tests the integrity of score calculation, session state updates,
and the consistency between raw scores, normalized scores, and AI analysis.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock

from app.services.scoring import ScoringService, calculate_session_scores, normalize_session_scores
from app.services.external_llm import ExternalLLMService
from app.models.session import (
    Session, SessionState, Scene, Choice, ChoiceRecord, Axis
)
from app.clients.llm_client import LLMResponse, LLMTaskType


class TestScoreConsistency:
    """Test cases for score calculation consistency and session state integrity."""

    @pytest.fixture
    def scoring_service(self):
        """Create scoring service instance."""
        return ScoringService()

    @pytest.fixture
    def sample_session_with_choices(self):
        """Create a session with realistic choice data for score testing."""
        session_id = uuid4()
        
        # Create consistent axes
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
                description="Preference for solo or collaborative approach",
                direction="個人主義 ⟷ 協調性"
            )
        ]
        
        # Create scenes with weighted choices
        scenes = []
        for scene_idx in range(1, 5):
            choices = [
                Choice(
                    id=f"choice_{scene_idx}_1",
                    text=f"論理的選択 {scene_idx}",
                    weights={"axis_1": 0.8, "axis_2": 0.2, "axis_3": -0.1}
                ),
                Choice(
                    id=f"choice_{scene_idx}_2", 
                    text=f"感情的選択 {scene_idx}",
                    weights={"axis_1": -0.7, "axis_2": -0.3, "axis_3": 0.4}
                ),
                Choice(
                    id=f"choice_{scene_idx}_3",
                    text=f"慎重選択 {scene_idx}",
                    weights={"axis_1": 0.1, "axis_2": -0.9, "axis_3": 0.2}
                ),
                Choice(
                    id=f"choice_{scene_idx}_4",
                    text=f"協調選択 {scene_idx}",
                    weights={"axis_1": -0.2, "axis_2": 0.3, "axis_3": 0.8}
                )
            ]
            
            scene = Scene(
                sceneIndex=scene_idx,
                themeId="consistency",
                narrative=f"Scene {scene_idx} for consistency testing",
                choices=choices
            )
            scenes.append(scene)
        
        # Create predictable choice pattern
        choice_records = [
            ChoiceRecord(
                sceneIndex=1,
                choiceId="choice_1_1",  # Logic +0.8
                timestamp=datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
            ),
            ChoiceRecord(
                sceneIndex=2,
                choiceId="choice_2_3",  # Caution -0.9
                timestamp=datetime(2025, 1, 15, 10, 35, 0, tzinfo=timezone.utc)
            ),
            ChoiceRecord(
                sceneIndex=3,
                choiceId="choice_3_4",  # Group +0.8
                timestamp=datetime(2025, 1, 15, 10, 40, 0, tzinfo=timezone.utc)
            ),
            ChoiceRecord(
                sceneIndex=4,
                choiceId="choice_4_2",  # Emotion -0.7
                timestamp=datetime(2025, 1, 15, 10, 45, 0, tzinfo=timezone.utc)
            )
        ]
        
        # Expected raw scores: axis_1: 0.1, axis_2: -0.7, axis_3: 1.1
        
        session = Session(
            id=session_id,
            state=SessionState.PLAY,
            initialCharacter="整",
            keywordCandidates=["整理", "整頓", "整合", "整備"],
            selectedKeyword="整合",
            themeId="consistency",
            axes=axes,
            scenes=scenes,
            choices=choice_records
        )
        
        return session

    @pytest.mark.asyncio
    async def test_raw_score_calculation_consistency(self, scoring_service, sample_session_with_choices):
        """Test that raw score calculation is consistent and predictable."""
        # Execute score calculation
        raw_scores = await scoring_service.calculate_scores(sample_session_with_choices)
        
        # Verify expected scores based on choice pattern
        # choice_1_1: axis_1: +0.8, axis_2: +0.2, axis_3: -0.1
        # choice_2_3: axis_1: +0.1, axis_2: -0.9, axis_3: +0.2
        # choice_3_4: axis_1: -0.2, axis_2: +0.3, axis_3: +0.8
        # choice_4_2: axis_1: -0.7, axis_2: -0.3, axis_3: +0.4
        # Total: axis_1: 0.0, axis_2: -0.7, axis_3: 1.3
        
        assert "axis_1" in raw_scores
        assert "axis_2" in raw_scores
        assert "axis_3" in raw_scores
        
        # Check approximately expected values (allowing for floating point precision)
        assert abs(raw_scores["axis_1"] - 0.0) < 0.01
        assert abs(raw_scores["axis_2"] - (-0.7)) < 0.01
        assert abs(raw_scores["axis_3"] - 1.3) < 0.01

    @pytest.mark.asyncio
    async def test_score_normalization_consistency(self, scoring_service, sample_session_with_choices):
        """Test that score normalization maintains mathematical consistency."""
        # Calculate raw scores
        raw_scores = await scoring_service.calculate_scores(sample_session_with_choices)
        
        # Normalize scores
        normalized_scores = await scoring_service.normalize_scores(raw_scores)
        
        # Verify normalization consistency
        assert len(normalized_scores) == len(raw_scores)
        
        for axis_id in raw_scores:
            raw_score = raw_scores[axis_id]
            normalized_score = normalized_scores[axis_id]
            
            # Verify normalization formula: (raw - (-5)) / (5 - (-5)) * (100 - 0) + 0
            expected_normalized = ((raw_score + 5.0) / 10.0) * 100.0
            assert abs(normalized_score - expected_normalized) < 0.1

    @pytest.mark.asyncio
    async def test_axis_id_consistency_across_calculations(self, scoring_service, sample_session_with_choices):
        """Test that axis IDs remain consistent throughout calculation pipeline."""
        # Get expected axis IDs from session
        expected_axis_ids = {axis.id for axis in sample_session_with_choices.axes}
        
        # Calculate raw scores
        raw_scores = await scoring_service.calculate_scores(sample_session_with_choices)
        raw_axis_ids = set(raw_scores.keys())
        
        # Normalize scores
        normalized_scores = await scoring_service.normalize_scores(raw_scores)
        normalized_axis_ids = set(normalized_scores.keys())
        
        # Verify consistency
        assert raw_axis_ids == expected_axis_ids
        assert normalized_axis_ids == expected_axis_ids
        assert raw_axis_ids == normalized_axis_ids

    @pytest.mark.asyncio
    async def test_session_state_update_timing(self, sample_session_with_choices):
        """Test that session state updates occur in correct sequence."""
        # Verify initial state
        assert sample_session_with_choices.rawScores == {}
        assert sample_session_with_choices.normalizedScores == {}
        
        # Simulate score calculation and session update
        scoring_service = ScoringService()
        raw_scores = await scoring_service.calculate_scores(sample_session_with_choices)
        normalized_scores = await scoring_service.normalize_scores(raw_scores)
        
        # Update session (simulating result generation workflow)
        sample_session_with_choices.rawScores = raw_scores
        sample_session_with_choices.normalizedScores = normalized_scores
        
        # Verify session state is updated
        assert sample_session_with_choices.rawScores != {}
        assert sample_session_with_choices.normalizedScores != {}
        assert len(sample_session_with_choices.rawScores) == 3
        assert len(sample_session_with_choices.normalizedScores) == 3

    @pytest.mark.asyncio
    async def test_score_range_validation(self, scoring_service, sample_session_with_choices):
        """Test that scores remain within expected ranges."""
        # Calculate scores
        raw_scores = await scoring_service.calculate_scores(sample_session_with_choices)
        normalized_scores = await scoring_service.normalize_scores(raw_scores)
        
        # Verify raw score ranges (-5.0 to 5.0)
        for axis_id, raw_score in raw_scores.items():
            assert -5.0 <= raw_score <= 5.0, f"Raw score {raw_score} for {axis_id} out of range"
        
        # Verify normalized score ranges (0.0 to 100.0)
        for axis_id, normalized_score in normalized_scores.items():
            assert 0.0 <= normalized_score <= 100.0, f"Normalized score {normalized_score} for {axis_id} out of range"

    @pytest.mark.asyncio
    async def test_score_consistency_with_ai_analysis_data(self, sample_session_with_choices):
        """Test that scores remain consistent when used for AI analysis."""
        # Calculate scores and update session
        scoring_service = ScoringService()
        raw_scores = await scoring_service.calculate_scores(sample_session_with_choices)
        normalized_scores = await scoring_service.normalize_scores(raw_scores)
        
        sample_session_with_choices.rawScores = raw_scores
        sample_session_with_choices.normalizedScores = normalized_scores
        
        # Create LLM service and build enhanced choices data
        llm_service = ExternalLLMService()
        enhanced_choices = llm_service._build_enhanced_choices_data(sample_session_with_choices)
        
        # Prepare template data that would be used for AI analysis
        template_data = {
            "session_id": str(sample_session_with_choices.id),
            "keyword": sample_session_with_choices.selectedKeyword,
            "axes": [axis.dict() for axis in sample_session_with_choices.axes],
            "scores": normalized_scores,
            "choices": enhanced_choices,
            "raw_scores": raw_scores
        }
        
        # Verify data consistency for AI analysis
        assert template_data["raw_scores"] == sample_session_with_choices.rawScores
        assert template_data["scores"] == sample_session_with_choices.normalizedScores
        assert len(template_data["choices"]) == len(sample_session_with_choices.choices)
        
        # Verify axis consistency between session and template data
        template_axis_ids = {axis["id"] for axis in template_data["axes"]}
        session_axis_ids = {axis.id for axis in sample_session_with_choices.axes}
        score_axis_ids = set(template_data["scores"].keys())
        
        assert template_axis_ids == session_axis_ids == score_axis_ids

    def test_score_interpretation_consistency(self, scoring_service):
        """Test that score interpretation categories are consistent."""
        test_scores = {
            "low_score": 15.0,
            "moderate_low": 35.0,
            "moderate_mid": 50.0,
            "moderate_high": 65.0,
            "high_score": 85.0
        }
        
        for axis_id, score in test_scores.items():
            interpretation = scoring_service.get_score_interpretation(axis_id, score)
            
            # Verify interpretation consistency
            if score < 30:
                assert interpretation == "Low"
            elif score < 70:
                assert interpretation == "Moderate"
            else:
                assert interpretation == "High"

    @pytest.mark.asyncio
    async def test_empty_choices_handling(self, scoring_service):
        """Test handling of session with no choices."""
        # Create session with no choices
        session = Session(
            id=uuid4(),
            state=SessionState.PLAY,
            initialCharacter="空",
            keywordCandidates=["空白", "空虚", "空想", "空気"],
            selectedKeyword="空白",
            themeId="empty",
            axes=[
                Axis(id="axis_1", name="Test Axis", description="Test", direction="左 ⟷ 右")
            ],
            scenes=[],
            choices=[]
        )
        
        # Should raise ValueError for empty choices
        with pytest.raises(ValueError, match="Expected 4 choices"):
            await scoring_service.calculate_scores(session)

    @pytest.mark.asyncio
    async def test_utility_functions_consistency(self):
        """Test that utility functions produce consistent results."""
        # Create test session
        session = Session(
            id=uuid4(),
            state=SessionState.PLAY,
            initialCharacter="テ",
            keywordCandidates=["テスト", "テーマ", "テクニック", "テーブル"],
            selectedKeyword="テスト",
            themeId="test",
            axes=[
                Axis(id="test_axis", name="Test", description="Test axis", direction="左 ⟷ 右")
            ],
            scenes=[
                Scene(
                    sceneIndex=1,
                    themeId="test",
                    narrative="Test narrative",
                    choices=[
                        Choice(id="choice_1", text="Choice 1", weights={"test_axis": 0.5}),
                        Choice(id="choice_2", text="Choice 2", weights={"test_axis": -0.3}),
                        Choice(id="choice_3", text="Choice 3", weights={"test_axis": 0.1}),
                        Choice(id="choice_4", text="Choice 4", weights={"test_axis": 0.2})
                    ]
                )
            ] * 4,  # Repeat for 4 scenes
            choices=[
                ChoiceRecord(
                    sceneIndex=i,
                    choiceId=f"choice_{i}",
                    timestamp=datetime.now(timezone.utc)
                )
                for i in range(1, 5)
            ]
        )
        
        # Test utility functions
        raw_scores = await calculate_session_scores(session)
        normalized_scores = await normalize_session_scores(raw_scores)
        
        # Test direct service methods
        service = ScoringService()
        service_raw = await service.calculate_scores(session)
        service_normalized = await service.normalize_scores(raw_scores)
        
        # Verify consistency
        assert raw_scores == service_raw
        assert normalized_scores == service_normalized
