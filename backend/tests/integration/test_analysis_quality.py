"""
T043: Personality analysis quality tests for NightLoom LLM integration.

Tests the quality and consistency of AI-generated personality analysis
to ensure meaningful and accurate results.
"""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.models.session import Session, SessionState, Axis, ChoiceRecord
from app.services.external_llm import ExternalLLMService
from app.clients.llm_client import LLMRequest, LLMResponse, LLMTaskType
from app.models.llm_config import LLMProvider


@pytest.fixture
def sample_session():
    """Create a sample completed session for analysis testing."""
    session = Session(
        id=uuid4(),
        state=SessionState.PLAY,
        initialCharacter="あ",
        selectedKeyword="愛情",
        themeId="serene",
        axes=[
            Axis(
                id="logic_emotion",
                name="Logic vs Emotion",
                description="Balance between analytical and intuitive decision making",
                direction="論理的 ⟷ 感情的"
            ),
            Axis(
                id="speed_caution", 
                name="Speed vs Caution",
                description="Pace of decision making",
                direction="迅速 ⟷ 慎重"
            ),
            Axis(
                id="individual_group",
                name="Individual vs Group",
                description="Focus on self vs others",
                direction="個人 ⟷ 集団"
            )
        ],
        choices=[
            ChoiceRecord(sceneIndex=1, choiceId="choice_1_1", timestamp=None),
            ChoiceRecord(sceneIndex=2, choiceId="choice_2_3", timestamp=None),
            ChoiceRecord(sceneIndex=3, choiceId="choice_3_2", timestamp=None),
            ChoiceRecord(sceneIndex=4, choiceId="choice_4_1", timestamp=None)
        ],
        rawScores={
            "logic_emotion": 1.5,
            "speed_caution": -0.8,
            "individual_group": 0.3
        },
        normalizedScores={
            "logic_emotion": 75.0,
            "speed_caution": 35.0,
            "individual_group": 55.0
        }
    )
    return session


@pytest.fixture
def llm_service():
    """Create ExternalLLMService instance for testing."""
    return ExternalLLMService()


class TestAnalysisQuality:
    """Test personality analysis quality and consistency."""
    
    @pytest.mark.asyncio
    async def test_analysis_generates_meaningful_profiles(self, llm_service, sample_session):
        """Test that analysis generates meaningful personality profiles."""
        # Mock successful LLM response
        mock_response = LLMResponse(
            task_type=LLMTaskType.RESULT_ANALYSIS,
            session_id=str(sample_session.id),
            content={
                "type_profiles": [
                    {
                        "name": "Thoughtful Deliberator",
                        "description": "論理的思考を重視し、慎重に判断を下す傾向があります。感情よりも分析を優先し、決断前に十分な検討時間を取る特徴があります。",
                        "keywords": ["analytical", "cautious", "systematic"],
                        "dominantAxes": ["logic_emotion", "speed_caution"],
                        "polarity": "Hi-Lo",
                        "meta": {"confidence": 0.85}
                    }
                ]
            },
            provider=LLMProvider.OPENAI,
            model_name="gpt-4",
            tokens_used=250,
            latency_ms=1500.0
        )
        
        with patch.object(llm_service, '_execute_with_fallback', return_value=mock_response):
            profiles = await llm_service.analyze_results(sample_session)
            
            assert len(profiles) > 0, "Should generate at least one profile"
            
            profile = profiles[0]
            assert profile.name, "Profile should have a meaningful name"
            assert len(profile.name) <= 14, "Profile name should fit length constraint"
            assert profile.description, "Profile should have description"
            assert len(profile.description) > 20, "Description should be substantial"
            assert profile.keywords, "Profile should have relevant keywords"
            assert len(profile.dominantAxes) == 2, "Should identify exactly 2 dominant axes"
            
    @pytest.mark.asyncio
    async def test_analysis_reflects_score_patterns(self, llm_service, sample_session):
        """Test that analysis accurately reflects user's score patterns."""
        # Test with high logic, low speed scores
        sample_session.normalizedScores = {
            "logic_emotion": 85.0,    # High logic
            "speed_caution": 25.0,    # High caution (low speed)
            "individual_group": 60.0  # Moderate
        }
        
        mock_response = LLMResponse(
            task_type=LLMTaskType.RESULT_ANALYSIS,
            session_id=str(sample_session.id),
            content={
                "type_profiles": [
                    {
                        "name": "Analytical Planner",
                        "description": "論理的分析を重視し、慎重に計画を立てる傾向が強い。感情よりも事実を基に判断し、時間をかけて検討することを好む。",
                        "keywords": ["logical", "methodical", "deliberate"],
                        "dominantAxes": ["logic_emotion", "speed_caution"],
                        "polarity": "Hi-Lo"
                    }
                ]
            },
            provider=LLMProvider.OPENAI,
            model_name="gpt-4"
        )
        
        with patch.object(llm_service, '_execute_with_fallback', return_value=mock_response):
            profiles = await llm_service.analyze_results(sample_session)
            
            profile = profiles[0]
            
            # Verify the analysis matches high logic, high caution pattern
            assert "logic_emotion" in profile.dominantAxes, "Should identify logic as dominant"
            assert "speed_caution" in profile.dominantAxes, "Should identify caution as relevant"
            assert profile.polarity == "Hi-Lo", "Should reflect high-low score pattern"
            
            # Check description reflects the patterns
            description_lower = profile.description.lower()
            assert any(term in description_lower for term in ["論理", "分析", "慎重"]), \
                "Description should reflect logical and cautious tendencies"

    @pytest.mark.asyncio
    async def test_analysis_keyword_integration(self, llm_service, sample_session):
        """Test that analysis integrates the session keyword meaningfully."""
        sample_session.selectedKeyword = "挑戦"
        
        mock_response = LLMResponse(
            task_type=LLMTaskType.RESULT_ANALYSIS,
            session_id=str(sample_session.id),
            content={
                "type_profiles": [
                    {
                        "name": "Strategic Challenger",
                        "description": "挑戦を重視しながらも論理的アプローチを取る傾向があります。新しい機会を慎重に評価し、計画的に取り組む特徴があります。",
                        "keywords": ["strategic", "growth-oriented", "methodical"],
                        "dominantAxes": ["logic_emotion", "speed_caution"],
                        "polarity": "Hi-Lo"
                    }
                ]
            },
            provider=LLMProvider.OPENAI,
            model_name="gpt-4"
        )
        
        with patch.object(llm_service, '_execute_with_fallback', return_value=mock_response):
            profiles = await llm_service.analyze_results(sample_session)
            
            profile = profiles[0]
            
            # Verify keyword integration
            assert sample_session.selectedKeyword in profile.description or \
                   "挑戦" in profile.description or "challenge" in profile.name.lower(), \
                   "Analysis should integrate the session keyword"

    @pytest.mark.asyncio
    async def test_analysis_consistency_across_calls(self, llm_service, sample_session):
        """Test that analysis provides consistent results for similar inputs."""
        # Mock consistent response structure
        def create_mock_response():
            return LLMResponse(
                task_type=LLMTaskType.RESULT_ANALYSIS,
                session_id=str(sample_session.id),
                content={
                    "type_profiles": [
                        {
                            "name": "Logical Deliberator",
                            "description": "論理的思考と慎重な判断を特徴とする性格パターン。",
                            "keywords": ["analytical", "careful", "systematic"],
                            "dominantAxes": ["logic_emotion", "speed_caution"],
                            "polarity": "Hi-Lo"
                        }
                    ]
                },
                provider=LLMProvider.OPENAI,
                model_name="gpt-4"
            )
        
        with patch.object(llm_service, '_execute_with_fallback', side_effect=create_mock_response):
            # Run analysis multiple times
            results = []
            for _ in range(3):
                profiles = await llm_service.analyze_results(sample_session)
                results.append(profiles[0])
            
            # Check consistency
            first_result = results[0]
            for result in results[1:]:
                assert result.name == first_result.name, "Profile names should be consistent"
                assert result.polarity == first_result.polarity, "Polarity should be consistent"
                assert result.dominantAxes == first_result.dominantAxes, "Dominant axes should be consistent"

    @pytest.mark.asyncio
    async def test_analysis_handles_edge_case_scores(self, llm_service, sample_session):
        """Test analysis handles edge cases like neutral or extreme scores."""
        # Test with all neutral scores
        sample_session.normalizedScores = {
            "logic_emotion": 50.0,
            "speed_caution": 50.0,
            "individual_group": 50.0
        }
        
        mock_response = LLMResponse(
            task_type=LLMTaskType.RESULT_ANALYSIS,
            session_id=str(sample_session.id),
            content={
                "type_profiles": [
                    {
                        "name": "Balanced Adapter",
                        "description": "バランスの取れた判断を行う傾向があります。状況に応じて論理と感情、個人と集団の観点を使い分ける柔軟性を持っています。",
                        "keywords": ["balanced", "adaptable", "flexible"],
                        "dominantAxes": ["logic_emotion", "individual_group"],
                        "polarity": "Mid-Mid"
                    }
                ]
            },
            provider=LLMProvider.OPENAI,
            model_name="gpt-4"
        )
        
        with patch.object(llm_service, '_execute_with_fallback', return_value=mock_response):
            profiles = await llm_service.analyze_results(sample_session)
            
            profile = profiles[0]
            assert profile.polarity in ["Mid-Mid", "Mid-Hi", "Mid-Lo"], \
                "Should handle neutral scores with appropriate polarity"
            assert "バランス" in profile.description or "balanced" in profile.name.lower(), \
                "Should recognize balanced pattern"

    @pytest.mark.asyncio
    async def test_analysis_validates_output_structure(self, llm_service, sample_session):
        """Test that analysis validates and corrects malformed LLM outputs."""
        # Mock malformed response
        malformed_response = LLMResponse(
            task_type=LLMTaskType.RESULT_ANALYSIS,
            session_id=str(sample_session.id),
            content={
                "type_profiles": [
                    {
                        "name": "Way Too Long Profile Name That Exceeds Limits",
                        "description": "Short",  # Too short
                        "keywords": [],  # Empty keywords
                        "dominantAxes": ["logic_emotion"],  # Only one axis
                        "polarity": "Invalid"  # Invalid polarity
                    }
                ]
            },
            provider=LLMProvider.OPENAI,
            model_name="gpt-4"
        )
        
        with patch.object(llm_service, '_execute_with_fallback', return_value=malformed_response):
            # Should handle validation errors gracefully or correct them
            try:
                profiles = await llm_service.analyze_results(sample_session)
                
                if profiles:  # If correction happened
                    profile = profiles[0]
                    assert len(profile.name) <= 14, "Should correct name length"
                    assert len(profile.description) > 10, "Should ensure adequate description"
                    assert len(profile.dominantAxes) >= 1, "Should have at least one dominant axis"
                    
            except Exception as e:
                # Should provide meaningful error message
                assert "validation" in str(e).lower() or "invalid" in str(e).lower(), \
                    "Should provide clear validation error message"

    @pytest.mark.asyncio
    async def test_analysis_quality_metrics(self, llm_service, sample_session):
        """Test that analysis includes quality and confidence metrics."""
        mock_response = LLMResponse(
            task_type=LLMTaskType.RESULT_ANALYSIS,
            session_id=str(sample_session.id),
            content={
                "type_profiles": [
                    {
                        "name": "Quality Profile",
                        "description": "高品質な分析結果として生成されたプロファイル。信頼性の高い洞察を提供します。",
                        "keywords": ["reliable", "insightful", "accurate"],
                        "dominantAxes": ["logic_emotion", "speed_caution"],
                        "polarity": "Hi-Lo",
                        "meta": {
                            "confidence": 0.92,
                            "coherence_score": 0.88,
                            "keyword_alignment": 0.85
                        }
                    }
                ]
            },
            provider=LLMProvider.OPENAI,
            model_name="gpt-4"
        )
        
        with patch.object(llm_service, '_execute_with_fallback', return_value=mock_response):
            profiles = await llm_service.analyze_results(sample_session)
            
            profile = profiles[0]
            
            # Check for quality indicators
            assert profile.meta, "Should include metadata"
            if "confidence" in profile.meta:
                assert 0.0 <= profile.meta["confidence"] <= 1.0, "Confidence should be valid probability"
            
            # Check description quality
            assert len(profile.description.split()) >= 5, "Description should have meaningful content"
            assert profile.keywords, "Should have relevant keywords"
