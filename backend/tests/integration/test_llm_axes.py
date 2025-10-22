"""
Integration tests for LLM-powered evaluation axes generation (User Story 2).

Tests the complete flow of generating dynamic evaluation axes based on selected keywords,
validating OpenAI/Anthropic integration, fallback behavior, and session consistency.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.clients.llm_client import LLMTaskType, LLMProvider
from app.services.external_llm import ExternalLLMService
from app.models.session import SessionManager
from fastapi.testclient import TestClient


class TestUS2AxisGenerationIntegration:
    """Integration tests for User Story 2: Dynamic evaluation axes generation."""

    @pytest.mark.asyncio
    async def test_us2_complete_workflow_success(self, llm_service, session_manager):
        """
        Test US2: Complete workflow from keyword selection to axis generation.
        
        Validates that:
        1. User can select a keyword from generated candidates
        2. System generates 2-6 dynamic evaluation axes based on keyword
        3. Axes are structurally valid and contextually relevant
        4. Session stores generated axes for later use
        """
        session_id = uuid4()
        await session_manager.create_session(session_id)
        
        # First generate keywords (prerequisite from US1)
        keyword_response = await llm_service.generate_keywords(
            session_id=session_id,
            initial_character="愛",
            provider=LLMProvider.OPENAI
        )
        
        # Select first keyword for axis generation
        selected_keyword = keyword_response.content["keywords"][0]["word"]
        
        # Generate axes based on selected keyword
        axis_response = await llm_service.generate_axes(
            session_id=session_id,
            keyword=selected_keyword,
            provider=LLMProvider.OPENAI
        )
        
        # Validate response structure
        assert axis_response is not None
        assert axis_response.task_type == LLMTaskType.AXIS_GENERATION
        assert "axes" in axis_response.content
        
        axes = axis_response.content["axes"]
        assert isinstance(axes, list)
        assert 2 <= len(axes) <= 6, f"Expected 2-6 axes, got {len(axes)}"
        
        # Validate each axis structure
        for i, axis in enumerate(axes):
            assert isinstance(axis, dict), f"Axis {i+1} must be object"
            assert "id" in axis, f"Axis {i+1} missing 'id'"
            assert "name" in axis, f"Axis {i+1} missing 'name'"
            assert "description" in axis, f"Axis {i+1} missing 'description'"
            assert "direction" in axis, f"Axis {i+1} missing 'direction'"
            
            # Validate field types and content
            assert isinstance(axis["id"], str) and axis["id"].strip()
            assert isinstance(axis["name"], str) and axis["name"].strip()
            assert isinstance(axis["description"], str) and axis["description"].strip()
            assert isinstance(axis["direction"], str) and "⟷" in axis["direction"]
        
        # Verify session stores axes
        session = await session_manager.get_session(session_id)
        assert session is not None
        assert hasattr(session, 'generated_axes')
        assert session.generated_axes is not None

    @pytest.mark.asyncio
    async def test_us2_different_keywords_generate_different_axes(self, llm_service, session_manager):
        """
        Test US2: Different keywords generate contextually different axes.
        
        Validates that:
        1. Keyword "愛" generates love/relationship-focused axes
        2. Keyword "冒険" generates adventure/risk-focused axes  
        3. Generated axes reflect keyword context appropriately
        """
        # Test with keyword "愛" (love)
        session_id_1 = uuid4()
        await session_manager.create_session(session_id_1)
        
        love_response = await llm_service.generate_axes(
            session_id=session_id_1,
            keyword="愛",
            provider=LLMProvider.OPENAI
        )
        
        # Test with keyword "冒険" (adventure)  
        session_id_2 = uuid4()
        await session_manager.create_session(session_id_2)
        
        adventure_response = await llm_service.generate_axes(
            session_id=session_id_2,
            keyword="冒険",
            provider=LLMProvider.OPENAI
        )
        
        # Verify both responses are valid
        assert love_response.content["axes"] is not None
        assert adventure_response.content["axes"] is not None
        
        love_axes = love_response.content["axes"]
        adventure_axes = adventure_response.content["axes"]
        
        # Verify axes are different (at least axis names should differ)
        love_names = {axis["name"] for axis in love_axes}
        adventure_names = {axis["name"] for axis in adventure_axes}
        
        # Should have some different axis names
        assert len(love_names.intersection(adventure_names)) < len(love_names), \
            "Expected different axes for different keywords"

    @pytest.mark.asyncio 
    async def test_us2_fallback_integration(self, llm_service, session_manager):
        """
        Test US2: Fallback behavior when LLM axis generation fails.
        
        Validates that:
        1. System detects LLM failure for axis generation
        2. Falls back to predetermined axis templates
        3. Fallback axes are still valid and usable
        4. Session continues normally with fallback axes
        """
        session_id = uuid4()
        await session_manager.create_session(session_id)
        
        # Mock LLM failure
        with patch.object(llm_service, '_call_llm_provider') as mock_llm:
            mock_llm.side_effect = Exception("Simulated LLM failure")
            
            # Should fall back gracefully
            axis_response = await llm_service.generate_axes(
                session_id=session_id,
                keyword="愛",
                provider=LLMProvider.OPENAI
            )
            
            # Verify fallback response
            assert axis_response is not None
            assert axis_response.fallback_used is True
            assert "axes" in axis_response.content
            
            axes = axis_response.content["axes"]
            assert 2 <= len(axes) <= 6
            
            # Fallback axes should still be valid
            for axis in axes:
                assert "id" in axis and "name" in axis
                assert "description" in axis and "direction" in axis

    @pytest.mark.asyncio
    async def test_us2_session_isolation(self, llm_service, session_manager):
        """
        Test US2: Axis generation maintains session isolation.
        
        Validates that:
        1. Multiple concurrent sessions generate independent axes
        2. Axes don't leak between sessions
        3. Each session maintains its own axis context
        """
        # Create multiple sessions
        session_ids = [uuid4() for _ in range(3)]
        keywords = ["愛", "平和", "成長"]
        
        tasks = []
        for session_id, keyword in zip(session_ids, keywords):
            await session_manager.create_session(session_id)
            tasks.append(
                llm_service.generate_axes(
                    session_id=session_id,
                    keyword=keyword,
                    provider=LLMProvider.OPENAI
                )
            )
        
        # Execute concurrently
        responses = await asyncio.gather(*tasks)
        
        # Verify each response is independent
        for i, response in enumerate(responses):
            assert response.session_id == session_ids[i]
            assert "axes" in response.content
            assert len(response.content["axes"]) >= 2


class TestUS2EdgeCases:
    """Edge case tests for User Story 2 axis generation."""

    @pytest.mark.asyncio
    async def test_us2_invalid_keyword(self, llm_service, session_manager):
        """Test axis generation with invalid keyword input."""
        session_id = uuid4()
        await session_manager.create_session(session_id)
        
        with pytest.raises(ValueError, match="keyword"):
            await llm_service.generate_axes(
                session_id=session_id,
                keyword="",  # Empty keyword
                provider=LLMProvider.OPENAI
            )
            
        with pytest.raises(ValueError, match="keyword"):
            await llm_service.generate_axes(
                session_id=session_id,
                keyword="a" * 100,  # Too long keyword
                provider=LLMProvider.OPENAI
            )

    @pytest.mark.asyncio
    async def test_us2_session_not_found(self, llm_service):
        """Test axis generation with non-existent session."""
        non_existent_session = uuid4()
        
        with pytest.raises(ValueError, match="Session not found"):
            await llm_service.generate_axes(
                session_id=non_existent_session,
                keyword="愛",
                provider=LLMProvider.OPENAI
            )

    @pytest.mark.asyncio
    async def test_us2_axis_count_validation(self, llm_service, session_manager):
        """Test that axis count stays within 2-6 range."""
        session_id = uuid4()
        await session_manager.create_session(session_id)
        
        # Mock response with invalid axis count
        with patch.object(llm_service, '_call_llm_provider') as mock_llm:
            # Test too few axes (1)
            mock_llm.return_value.content = {"axes": [{"id": "axis_1", "name": "Test"}]}
            
            with pytest.raises(ValueError, match="2-6 axes"):
                await llm_service.generate_axes(
                    session_id=session_id,
                    keyword="愛",
                    provider=LLMProvider.OPENAI
                )
            
            # Test too many axes (7)
            mock_axes = [{"id": f"axis_{i}", "name": f"Test {i}"} for i in range(1, 8)]
            mock_llm.return_value.content = {"axes": mock_axes}
            
            with pytest.raises(ValueError, match="2-6 axes"):
                await llm_service.generate_axes(
                    session_id=session_id,
                    keyword="愛", 
                    provider=LLMProvider.OPENAI
                )


@pytest.fixture
async def llm_service():
    """Create LLM service instance for testing."""
    service = ExternalLLMService()
    yield service

@pytest.fixture  
async def session_manager():
    """Create session manager for testing."""
    manager = SessionManager()
    yield manager
    # Cleanup sessions after test
    await manager.cleanup_all_sessions()
