"""
T044: Result generation fallback tests for NightLoom LLM integration.

Tests fallback behavior when AI result analysis fails, ensuring
graceful degradation to static type profiles.
"""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.models.session import Session, SessionState, Axis, ChoiceRecord
from app.services.external_llm import ExternalLLMService, AllProvidersFailedError
from app.clients.llm_client import LLMRequest, LLMResponse, LLMTaskType, ValidationError, ProviderUnavailableError
from app.models.llm_config import LLMProvider


@pytest.fixture
def completed_session():
    """Create a sample completed session for result fallback testing."""
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
            )
        ],
        choices=[
            ChoiceRecord(sceneIndex=1, choiceId="choice_1_1", timestamp=None),
            ChoiceRecord(sceneIndex=2, choiceId="choice_2_2", timestamp=None),
            ChoiceRecord(sceneIndex=3, choiceId="choice_3_3", timestamp=None),
            ChoiceRecord(sceneIndex=4, choiceId="choice_4_4", timestamp=None)
        ],
        rawScores={
            "logic_emotion": 1.2,
            "speed_caution": -0.5
        },
        normalizedScores={
            "logic_emotion": 70.0,
            "speed_caution": 40.0
        }
    )
    return session


@pytest.fixture
def llm_service():
    """Create ExternalLLMService instance for testing."""
    return ExternalLLMService()


class TestResultFallback:
    """Test result generation fallback scenarios."""
    
    @pytest.mark.asyncio
    async def test_fallback_on_all_providers_failed(self, llm_service, completed_session):
        """Test fallback when all LLM providers fail."""
        # Mock all providers failing
        with patch.object(llm_service, '_execute_with_fallback', 
                         side_effect=AllProvidersFailedError("All providers failed")):
            
            # Mock fallback manager to return static profiles
            with patch.object(llm_service.fallback_manager, 'generate_fallback_profiles') as mock_fallback:
                mock_fallback.return_value = [
                    {
                        "name": "Fallback Type",
                        "description": "静的フォールバックプロファイル",
                        "keywords": ["fallback", "static"],
                        "dominantAxes": ["logic_emotion", "speed_caution"],
                        "polarity": "Hi-Lo"
                    }
                ]
                
                # Should use fallback without raising exception
                profiles = await llm_service.analyze_results(completed_session)
                
                assert profiles, "Should return fallback profiles"
                assert len(profiles) > 0, "Should have at least one fallback profile"
                
                # Verify fallback was called with correct parameters
                mock_fallback.assert_called_once()
                call_args = mock_fallback.call_args
                assert call_args[1]['scores'] == completed_session.normalizedScores
                assert call_args[1]['keyword'] == completed_session.selectedKeyword

    @pytest.mark.asyncio
    async def test_fallback_on_validation_error(self, llm_service, completed_session):
        """Test fallback when LLM response fails validation."""
        # Mock invalid LLM response
        invalid_response = LLMResponse(
            task_type=LLMTaskType.RESULT_ANALYSIS,
            session_id=str(completed_session.id),
            content={
                "invalid_structure": "malformed response"
            },
            provider=LLMProvider.OPENAI,
            model_name="gpt-4"
        )
        
        with patch.object(llm_service, '_execute_with_fallback', return_value=invalid_response):
            with patch.object(llm_service.fallback_manager, 'generate_fallback_profiles') as mock_fallback:
                mock_fallback.return_value = [
                    {
                        "name": "Validation Fallback",
                        "description": "バリデーションエラー時のフォールバックプロファイル",
                        "keywords": ["validation", "error", "fallback"],
                        "dominantAxes": ["logic_emotion", "speed_caution"],
                        "polarity": "Hi-Lo"
                    }
                ]
                
                # Should handle validation error gracefully
                profiles = await llm_service.analyze_results(completed_session)
                
                assert profiles, "Should return fallback profiles on validation error"
                assert len(profiles) > 0
                
                profile = profiles[0]
                assert profile["name"] == "Validation Fallback"

    @pytest.mark.asyncio
    async def test_fallback_preserves_session_context(self, llm_service, completed_session):
        """Test that fallback maintains session keyword and score context."""
        # Test with specific keyword and scores
        completed_session.selectedKeyword = "挑戦"
        completed_session.normalizedScores = {
            "logic_emotion": 80.0,  # High logic
            "speed_caution": 30.0   # High caution
        }
        
        with patch.object(llm_service, '_execute_with_fallback', 
                         side_effect=ProviderUnavailableError("Provider down")):
            
            with patch.object(llm_service.fallback_manager, 'generate_fallback_profiles') as mock_fallback:
                mock_fallback.return_value = [
                    {
                        "name": "Challenge Seeker",
                        "description": "挑戦を重視する論理的で慎重な性格",
                        "keywords": ["challenge", "logical", "careful"],
                        "dominantAxes": ["logic_emotion", "speed_caution"],
                        "polarity": "Hi-Lo"
                    }
                ]
                
                profiles = await llm_service.analyze_results(completed_session)
                
                # Verify fallback received correct context
                call_args = mock_fallback.call_args
                assert call_args[1]['keyword'] == "挑戦"
                assert call_args[1]['scores']['logic_emotion'] == 80.0
                assert call_args[1]['scores']['speed_caution'] == 30.0
                
                # Verify result reflects context
                profile = profiles[0]
                assert "挑戦" in profile["description"] or "challenge" in profile["name"].lower()

    @pytest.mark.asyncio
    async def test_fallback_handles_partial_failure(self, llm_service, completed_session):
        """Test fallback when only some providers fail."""
        # Mock primary provider failure, secondary success
        call_count = 0
        def mock_execute_with_fallback(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call (primary provider) fails
                raise ProviderUnavailableError("OpenAI unavailable")
            else:
                # Second call (secondary provider) succeeds
                return LLMResponse(
                    task_type=LLMTaskType.RESULT_ANALYSIS,
                    session_id=str(completed_session.id),
                    content={
                        "type_profiles": [
                            {
                                "name": "Secondary Success",
                                "description": "セカンダリプロバイダーによる分析結果",
                                "keywords": ["secondary", "success", "backup"],
                                "dominantAxes": ["logic_emotion", "speed_caution"],
                                "polarity": "Hi-Lo"
                            }
                        ]
                    },
                    provider=LLMProvider.ANTHROPIC,
                    model_name="claude-3-sonnet"
                )
        
        with patch.object(llm_service, '_execute_with_fallback', side_effect=mock_execute_with_fallback):
            profiles = await llm_service.analyze_results(completed_session)
            
            assert profiles, "Should succeed with secondary provider"
            assert len(profiles) > 0
            
            profile = profiles[0]
            assert profile.name == "Secondary Success"
            assert "セカンダリ" in profile.description

    @pytest.mark.asyncio
    async def test_fallback_tracks_usage_in_session(self, llm_service, completed_session):
        """Test that fallback usage is properly tracked in session."""
        with patch.object(llm_service, '_execute_with_fallback', 
                         side_effect=AllProvidersFailedError("Complete failure")):
            
            with patch.object(llm_service.fallback_manager, 'generate_fallback_profiles') as mock_fallback:
                mock_fallback.return_value = [
                    {
                        "name": "Tracked Fallback",
                        "description": "フォールバック使用追跡テスト",
                        "keywords": ["tracked", "fallback"],
                        "dominantAxes": ["logic_emotion", "speed_caution"], 
                        "polarity": "Hi-Lo"
                    }
                ]
                
                await llm_service.analyze_results(completed_session)
                
                # Verify fallback flag was set
                assert "result_analysis" in completed_session.fallbackFlags

    @pytest.mark.asyncio
    async def test_fallback_strategy_selection(self, llm_service, completed_session):
        """Test that appropriate fallback strategy is selected based on context."""
        # Test different score patterns to verify strategy selection
        test_cases = [
            {
                "scores": {"logic_emotion": 90.0, "speed_caution": 10.0},
                "expected_strategy": "adaptive",
                "keyword": "分析"
            },
            {
                "scores": {"logic_emotion": 50.0, "speed_caution": 50.0},
                "expected_strategy": "adaptive", 
                "keyword": "バランス"
            },
            {
                "scores": {"logic_emotion": 20.0, "speed_caution": 80.0},
                "expected_strategy": "adaptive",
                "keyword": "感情"
            }
        ]
        
        for test_case in test_cases:
            completed_session.normalizedScores = test_case["scores"]
            completed_session.selectedKeyword = test_case["keyword"]
            
            with patch.object(llm_service, '_execute_with_fallback', 
                             side_effect=AllProvidersFailedError("Test failure")):
                
                with patch.object(llm_service.fallback_manager, 'generate_fallback_profiles') as mock_fallback:
                    mock_fallback.return_value = [
                        {
                            "name": f"Strategy Test",
                            "description": f"{test_case['keyword']}に基づく戦略的フォールバック",
                            "keywords": ["strategy", "test"],
                            "dominantAxes": ["logic_emotion", "speed_caution"],
                            "polarity": "Hi-Lo"
                        }
                    ]
                    
                    await llm_service.analyze_results(completed_session)
                    
                    # Verify strategy parameter was passed
                    call_args = mock_fallback.call_args
                    strategy_used = call_args[1].get('strategy')
                    assert strategy_used == test_case["expected_strategy"]

    @pytest.mark.asyncio
    async def test_fallback_performance_tracking(self, llm_service, completed_session):
        """Test that fallback operations are properly tracked for performance monitoring."""
        with patch.object(llm_service, '_execute_with_fallback', 
                         side_effect=AllProvidersFailedError("Performance test failure")):
            
            with patch.object(llm_service.fallback_manager, 'generate_fallback_profiles') as mock_fallback:
                with patch.object(llm_service.fallback_manager, 'record_fallback_usage') as mock_track:
                    mock_fallback.return_value = [
                        {
                            "name": "Performance Test",
                            "description": "パフォーマンス追跡テスト用フォールバック",
                            "keywords": ["performance", "tracking"],
                            "dominantAxes": ["logic_emotion", "speed_caution"],
                            "polarity": "Hi-Lo"
                        }
                    ]
                    
                    await llm_service.analyze_results(completed_session)
                    
                    # Verify performance tracking was called
                    mock_track.assert_called_once_with(
                        operation_type="result_analysis",
                        strategy="adaptive", 
                        session_id=str(completed_session.id)
                    )

    @pytest.mark.asyncio
    async def test_fallback_maintains_quality_standards(self, llm_service, completed_session):
        """Test that fallback profiles maintain quality standards."""
        with patch.object(llm_service, '_execute_with_fallback', 
                         side_effect=AllProvidersFailedError("Quality test failure")):
            
            with patch.object(llm_service.fallback_manager, 'generate_fallback_profiles') as mock_fallback:
                mock_fallback.return_value = [
                    {
                        "name": "Quality Fallback",
                        "description": "高品質を維持するフォールバックプロファイル。ユーザーの選択パターンを反映し、意味のある洞察を提供する。",
                        "keywords": ["quality", "meaningful", "insightful"],
                        "dominantAxes": ["logic_emotion", "speed_caution"],
                        "polarity": "Hi-Lo",
                        "meta": {"fallback": True, "quality_assured": True}
                    }
                ]
                
                profiles = await llm_service.analyze_results(completed_session)
                
                profile = profiles[0]
                
                # Verify quality standards
                assert len(profile["name"]) <= 14, "Name should meet length constraint"
                assert len(profile["description"]) > 20, "Description should be substantial"
                assert len(profile["keywords"]) >= 2, "Should have meaningful keywords"
                assert len(profile["dominantAxes"]) == 2, "Should identify dominant axes"
                assert profile["polarity"] in ["Hi-Hi", "Hi-Lo", "Lo-Hi", "Lo-Lo", "Mid-Mid"], \
                    "Should have valid polarity"
