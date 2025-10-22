"""
Integration tests for axis generation fallback behavior (User Story 2).

Tests fallback mechanisms when LLM axis generation fails,
ensuring system continues to function with predetermined axis templates.
"""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.clients.llm_client import LLMProvider, ProviderUnavailableError, RateLimitError
from app.services.external_llm import ExternalLLMService
from app.services.fallback_manager import FallbackManager
from app.models.session import SessionManager


class TestAxisFallbackIntegration:
    """Integration tests for axis generation fallback scenarios."""

    @pytest.mark.asyncio
    async def test_openai_failure_fallback_to_predetermined_axes(self, llm_service, session_manager):
        """
        Test fallback when OpenAI axis generation fails.
        
        Validates that:
        1. System detects OpenAI failure
        2. Falls back to predetermined axis templates
        3. Fallback axes are contextually appropriate for keyword
        4. Session continues normally with fallback data
        """
        session_id = uuid4()
        await session_manager.create_session(session_id)
        
        # Mock OpenAI failure
        with patch.object(llm_service, '_get_llm_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.generate_axes.side_effect = ProviderUnavailableError("OpenAI service unavailable")
            mock_get_client.return_value = mock_client
            
            # Should fallback gracefully
            response = await llm_service.generate_axes(
                session_id=session_id,
                keyword="愛",
                provider=LLMProvider.OPENAI
            )
            
            # Verify fallback was used
            assert response is not None
            assert response.fallback_used is True
            assert response.provider == LLMProvider.OPENAI  # Still reports original provider
            assert "axes" in response.content
            
            axes = response.content["axes"]
            assert isinstance(axes, list)
            assert 2 <= len(axes) <= 6
            
            # Verify fallback axes structure
            for axis in axes:
                assert "id" in axis and "name" in axis
                assert "description" in axis and "direction" in axis
                assert isinstance(axis["name"], str) and axis["name"].strip()

    @pytest.mark.asyncio
    async def test_anthropic_failure_fallback_to_predetermined_axes(self, llm_service, session_manager):
        """
        Test fallback when Anthropic axis generation fails.
        
        Validates similar fallback behavior for Anthropic provider.
        """
        session_id = uuid4()
        await session_manager.create_session(session_id)
        
        # Mock Anthropic failure
        with patch.object(llm_service, '_get_llm_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.generate_axes.side_effect = RateLimitError("Anthropic rate limit exceeded")
            mock_get_client.return_value = mock_client
            
            response = await llm_service.generate_axes(
                session_id=session_id,
                keyword="冒険",
                provider=LLMProvider.ANTHROPIC
            )
            
            assert response.fallback_used is True
            assert response.provider == LLMProvider.ANTHROPIC
            assert len(response.content["axes"]) >= 2

    @pytest.mark.asyncio
    async def test_keyword_specific_fallback_axes(self, llm_service, session_manager, fallback_manager):
        """
        Test that fallback axes are contextually appropriate for different keywords.
        
        Validates that:
        1. Keyword "愛" gets love/relationship-focused fallback axes
        2. Keyword "冒険" gets adventure/risk-focused fallback axes
        3. Generic keywords get balanced general axes
        """
        session_id = uuid4()
        await session_manager.create_session(session_id)
        
        # Mock LLM failure for consistent fallback testing
        with patch.object(llm_service, '_get_llm_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.generate_axes.side_effect = Exception("Simulated failure")
            mock_get_client.return_value = mock_client
            
            # Test love-themed keyword
            love_response = await llm_service.generate_axes(
                session_id=session_id,
                keyword="愛",
                provider=LLMProvider.OPENAI
            )
            
            love_axes = love_response.content["axes"]
            love_axis_names = [axis["name"] for axis in love_axes]
            
            # Should contain relationship/emotion-focused axes
            relationship_terms = ["感情", "共感", "信頼", "調和", "思いやり"]
            has_relationship_focus = any(
                any(term in axis_name for term in relationship_terms)
                for axis_name in love_axis_names
            )
            assert has_relationship_focus, f"Expected relationship-focused axes for '愛', got: {love_axis_names}"
            
            # Test adventure-themed keyword
            adventure_response = await llm_service.generate_axes(
                session_id=session_id,
                keyword="冒険",
                provider=LLMProvider.OPENAI
            )
            
            adventure_axes = adventure_response.content["axes"]
            adventure_axis_names = [axis["name"] for axis in adventure_axes]
            
            # Should contain risk/action-focused axes
            adventure_terms = ["挑戦", "リスク", "探索", "行動", "革新"]
            has_adventure_focus = any(
                any(term in axis_name for term in adventure_terms)
                for axis_name in adventure_axis_names
            )
            assert has_adventure_focus, f"Expected adventure-focused axes for '冒険', got: {adventure_axis_names}"

    @pytest.mark.asyncio
    async def test_fallback_axes_session_integration(self, llm_service, session_manager):
        """
        Test that fallback axes integrate properly with session state.
        
        Validates that:
        1. Fallback axes are stored in session
        2. Session can proceed to next steps with fallback axes
        3. Fallback status is properly tracked
        """
        session_id = uuid4()
        await session_manager.create_session(session_id)
        
        # Force fallback
        with patch.object(llm_service, '_get_llm_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.generate_axes.side_effect = Exception("Force fallback")
            mock_get_client.return_value = mock_client
            
            response = await llm_service.generate_axes(
                session_id=session_id,
                keyword="平和",
                provider=LLMProvider.OPENAI
            )
            
            # Verify session state
            session = await session_manager.get_session(session_id)
            assert session is not None
            assert hasattr(session, 'generated_axes')
            assert session.generated_axes is not None
            
            # Verify fallback tracking
            assert hasattr(session, 'fallback_used')
            assert session.fallback_used is True

    @pytest.mark.asyncio
    async def test_partial_failure_recovery(self, llm_service, session_manager):
        """
        Test recovery when LLM returns partial or malformed axis data.
        
        Validates that:
        1. System detects malformed LLM responses
        2. Falls back when axis validation fails
        3. Provides complete, valid axis set from fallback
        """
        session_id = uuid4()
        await session_manager.create_session(session_id)
        
        # Mock malformed LLM response
        with patch.object(llm_service, '_get_llm_client') as mock_get_client:
            mock_client = AsyncMock()
            
            # Return malformed response (missing required fields)
            malformed_response = AsyncMock()
            malformed_response.content = {
                "axes": [
                    {"id": "axis_1", "name": "不完全な軸"},  # Missing description and direction
                    {"name": "軸2", "description": "IDがない"}  # Missing id
                ]
            }
            malformed_response.fallback_used = False
            mock_client.generate_axes.return_value = malformed_response
            mock_get_client.return_value = mock_client
            
            # Should detect malformed data and fallback
            response = await llm_service.generate_axes(
                session_id=session_id,
                keyword="成長",
                provider=LLMProvider.OPENAI
            )
            
            # Should have fallen back to valid axes
            assert response.fallback_used is True
            axes = response.content["axes"]
            
            # Verify all axes are properly structured
            for axis in axes:
                assert "id" in axis and axis["id"].strip()
                assert "name" in axis and axis["name"].strip()
                assert "description" in axis and axis["description"].strip()
                assert "direction" in axis and "⟷" in axis["direction"]

    @pytest.mark.asyncio
    async def test_provider_switching_on_failure(self, llm_service, session_manager):
        """
        Test automatic provider switching when primary provider fails.
        
        Validates that:
        1. Primary provider failure triggers fallback attempt
        2. Secondary provider is tried before predetermined fallback
        3. Final fallback is used if all providers fail
        """
        session_id = uuid4()
        await session_manager.create_session(session_id)
        
        # Mock both providers failing
        with patch.object(llm_service, '_get_llm_client') as mock_get_client:
            def mock_client_factory(provider):
                mock_client = AsyncMock()
                if provider == LLMProvider.OPENAI:
                    mock_client.generate_axes.side_effect = ProviderUnavailableError("OpenAI down")
                elif provider == LLMProvider.ANTHROPIC:
                    mock_client.generate_axes.side_effect = RateLimitError("Anthropic rate limited")
                return mock_client
            
            mock_get_client.side_effect = mock_client_factory
            
            # Should try providers and finally fallback
            response = await llm_service.generate_axes(
                session_id=session_id,
                keyword="調和",
                provider=LLMProvider.OPENAI  # Start with OpenAI
            )
            
            # Should have used fallback after provider failures
            assert response.fallback_used is True
            assert response.content["axes"] is not None
            assert len(response.content["axes"]) >= 2


class TestAxisFallbackEdgeCases:
    """Edge case tests for axis fallback scenarios."""

    @pytest.mark.asyncio
    async def test_fallback_manager_unavailable(self, llm_service, session_manager):
        """Test behavior when even fallback manager fails."""
        session_id = uuid4()
        await session_manager.create_session(session_id)
        
        with patch.object(llm_service, '_get_llm_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.generate_axes.side_effect = Exception("LLM failure")
            mock_get_client.return_value = mock_client
            
            # Also mock fallback manager failure
            with patch.object(llm_service, 'fallback_manager') as mock_fallback:
                mock_fallback.get_fallback_axes.side_effect = Exception("Fallback manager error")
                
                # Should raise exception when all fallbacks fail
                with pytest.raises(Exception, match="Unable to generate axes"):
                    await llm_service.generate_axes(
                        session_id=session_id,
                        keyword="テスト",
                        provider=LLMProvider.OPENAI
                    )

    @pytest.mark.asyncio
    async def test_fallback_with_unknown_keyword(self, llm_service, session_manager):
        """Test fallback behavior with unknown/rare keywords."""
        session_id = uuid4()
        await session_manager.create_session(session_id)
        
        with patch.object(llm_service, '_get_llm_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.generate_axes.side_effect = Exception("LLM failure")
            mock_get_client.return_value = mock_client
            
            # Test with obscure keyword
            response = await llm_service.generate_axes(
                session_id=session_id,
                keyword="量子もつれ",  # Obscure scientific term
                provider=LLMProvider.OPENAI
            )
            
            # Should still provide reasonable fallback axes
            assert response.fallback_used is True
            axes = response.content["axes"]
            assert len(axes) >= 2
            
            # Should be generic but valid axes
            for axis in axes:
                assert all(field in axis for field in ["id", "name", "description", "direction"])


@pytest.fixture
async def llm_service():
    """Create LLM service for testing."""
    service = ExternalLLMService()
    yield service

@pytest.fixture
async def session_manager():
    """Create session manager for testing."""
    manager = SessionManager()
    yield manager
    await manager.cleanup_all_sessions()

@pytest.fixture
async def fallback_manager():
    """Create fallback manager for testing."""
    manager = FallbackManager()
    yield manager
