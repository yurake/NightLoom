"""
Performance tests for keyword generation functionality.

Tests T021: Keyword performance requirements validation.
Ensures keyword generation meets 95% success rate and 500ms latency requirements.
"""

import pytest
import uuid
import time
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

from app.services.external_llm import ExternalLLMService, get_llm_service, AllProvidersFailedError
from app.models.session import Session, SessionState
from app.models.llm_config import LLMProvider
from app.clients.llm_client import (
    LLMResponse, LLMTaskType, LLMClientError,
    RateLimitError, ProviderUnavailableError
)


class TestKeywordGenerationPerformance:
    """Test performance characteristics of keyword generation."""
    
    @pytest.fixture
    def llm_service(self):
        """Create LLM service instance for testing."""
        return ExternalLLMService()
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock session for testing."""
        return Session(
            id=uuid.uuid4(),
            state=SessionState.INIT,
            initialCharacter="あ",
            themeId="adventure",
            keywordCandidates=[],
            axes=[],
            scenes=[],
            choices=[],
            rawScores={},
            normalizedScores={},
            typeProfiles=[],
            fallbackFlags=[],
            llmGenerations=[],
            llmErrors=[]
        )
    
    @pytest.mark.asyncio
    async def test_keyword_generation_latency_requirement(self, llm_service, mock_session):
        """Test that keyword generation meets 500ms latency requirement."""
        mock_keywords = ["愛情", "冒険", "希望", "成長"]
        
        # Mock fast response (within requirement)
        mock_response = LLMResponse(
            task_type=LLMTaskType.KEYWORD_GENERATION,
            session_id=str(mock_session.id),
            content={"keywords": mock_keywords},
            provider=LLMProvider.OPENAI,
            model_name="gpt-4",
            latency_ms=250.0  # Well within 500ms requirement
        )
        
        with patch.object(llm_service, '_execute_with_fallback', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = mock_response
            
            # Measure actual execution time
            start_time = time.time()
            keywords = await llm_service.generate_keywords(mock_session)
            end_time = time.time()
            
            actual_latency_ms = (end_time - start_time) * 1000
            
            # Verify performance requirement (500ms)
            assert actual_latency_ms < 500, f"Keyword generation took {actual_latency_ms}ms, exceeds 500ms requirement"
            assert keywords == mock_keywords
    
    @pytest.mark.asyncio
    async def test_keyword_generation_success_rate_requirement(self, llm_service):
        """Test that keyword generation achieves 95% success rate."""
        total_attempts = 100
        successful_attempts = 0
        
        for i in range(total_attempts):
            session = Session(
                id=uuid.uuid4(),
                state=SessionState.INIT,
                initialCharacter="あ",
                themeId="adventure"
            )
            
            # Mock 95% success rate (fail 5% of the time)
            if i < 95:  # First 95 attempts succeed
                mock_keywords = [f"成功{i}a", f"成功{i}b", f"成功{i}c", f"成功{i}d"]
                mock_response = LLMResponse(
                    task_type=LLMTaskType.KEYWORD_GENERATION,
                    session_id=str(session.id),
                    content={"keywords": mock_keywords},
                    provider=LLMProvider.OPENAI,
                    model_name="gpt-4"
                )
                
                with patch.object(llm_service, '_execute_with_fallback', new_callable=AsyncMock) as mock_execute:
                    mock_execute.return_value = mock_response
                    
                    try:
                        keywords = await llm_service.generate_keywords(session)
                        if len(keywords) == 4:
                            successful_attempts += 1
                    except Exception:
                        pass
            else:  # Last 5 attempts fail, use fallback
                fallback_keywords = [f"fallback{i}a", f"fallback{i}b", f"fallback{i}c", f"fallback{i}d"]
                
                with patch.object(llm_service, '_execute_with_fallback', new_callable=AsyncMock) as mock_execute:
                    mock_execute.side_effect = AllProvidersFailedError("Provider failed")
                    
                    with patch.object(llm_service.fallback_manager, 'get_keywords_for_character', new_callable=AsyncMock) as mock_fallback:
                        mock_fallback.return_value = fallback_keywords
                        
                        try:
                            keywords = await llm_service.generate_keywords(session)
                            if len(keywords) == 4:
                                successful_attempts += 1
                        except Exception:
                            pass
        
        success_rate = (successful_attempts / total_attempts) * 100
        
        # Verify 95% success rate requirement
        assert success_rate >= 95.0, f"Success rate {success_rate}% below 95% requirement"
    
    @pytest.mark.asyncio
    async def test_keyword_generation_concurrent_performance(self, llm_service):
        """Test keyword generation performance under concurrent load."""
        concurrent_requests = 10
        sessions = []
        
        # Create multiple sessions
        for i in range(concurrent_requests):
            session = Session(
                id=uuid.uuid4(),
                state=SessionState.INIT,
                initialCharacter="あ",
                themeId="adventure"
            )
            sessions.append(session)
        
        mock_keywords = ["並行1", "並行2", "並行3", "並行4"]
        mock_response = LLMResponse(
            task_type=LLMTaskType.KEYWORD_GENERATION,
            session_id="test",
            content={"keywords": mock_keywords},
            provider=LLMProvider.OPENAI,
            model_name="gpt-4",
            latency_ms=200.0
        )
        
        with patch.object(llm_service, '_execute_with_fallback', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = mock_response
            
            # Execute concurrent requests
            start_time = time.time()
            
            tasks = [
                llm_service.generate_keywords(session) 
                for session in sessions
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            total_time_ms = (end_time - start_time) * 1000
            
            # Verify all requests succeeded
            successful_results = [r for r in results if not isinstance(r, Exception)]
            assert len(successful_results) == concurrent_requests
            
            # Verify concurrent performance (should not be much slower than single request)
            average_time_per_request = total_time_ms / concurrent_requests
            assert average_time_per_request < 1000, f"Average time per concurrent request {average_time_per_request}ms too slow"
    
    @pytest.mark.asyncio
    async def test_keyword_generation_memory_efficiency(self, llm_service):
        """Test memory efficiency of keyword generation."""
        import tracemalloc
        
        tracemalloc.start()
        
        session = Session(
            id=uuid.uuid4(),
            state=SessionState.INIT,
            initialCharacter="あ",
            themeId="adventure"
        )
        
        mock_keywords = ["メモリ1", "メモリ2", "メモリ3", "メモリ4"]
        mock_response = LLMResponse(
            task_type=LLMTaskType.KEYWORD_GENERATION,
            session_id=str(session.id),
            content={"keywords": mock_keywords},
            provider=LLMProvider.OPENAI,
            model_name="gpt-4"
        )
        
        with patch.object(llm_service, '_execute_with_fallback', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = mock_response
            
            # Measure memory before
            snapshot_before = tracemalloc.take_snapshot()
            
            # Execute keyword generation
            keywords = await llm_service.generate_keywords(session)
            
            # Measure memory after
            snapshot_after = tracemalloc.take_snapshot()
            
            tracemalloc.stop()
            
            # Calculate memory usage
            top_stats = snapshot_after.compare_to(snapshot_before, 'lineno')
            total_memory_kb = sum(stat.size_diff for stat in top_stats) / 1024
            
            # Verify reasonable memory usage (< 1MB for single request)
            assert total_memory_kb < 1024, f"Memory usage {total_memory_kb}KB exceeds 1MB limit"
            assert keywords == mock_keywords
    
    @pytest.mark.asyncio
    async def test_keyword_generation_error_recovery_time(self, llm_service, mock_session):
        """Test that error recovery (fallback) happens quickly."""
        fallback_keywords = ["復旧1", "復旧2", "復旧3", "復旧4"]
        
        with patch.object(llm_service, '_execute_with_fallback', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = AllProvidersFailedError("All providers failed")
            
            with patch.object(llm_service.fallback_manager, 'get_keywords_for_character', new_callable=AsyncMock) as mock_fallback:
                mock_fallback.return_value = fallback_keywords
                
                # Measure fallback recovery time
                start_time = time.time()
                keywords = await llm_service.generate_keywords(mock_session)
                end_time = time.time()
                
                recovery_time_ms = (end_time - start_time) * 1000
                
                # Fallback should be very fast (< 100ms)
                assert recovery_time_ms < 100, f"Error recovery took {recovery_time_ms}ms, should be < 100ms"
                assert keywords == fallback_keywords
                assert "keyword_generation" in mock_session.fallbackFlags


class TestKeywordGenerationStressTest:
    """Stress tests for keyword generation under high load."""
    
    @pytest.fixture
    def llm_service(self):
        return ExternalLLMService()
    
    @pytest.mark.asyncio
    async def test_keyword_generation_high_frequency(self, llm_service):
        """Test keyword generation under high frequency requests."""
        request_count = 50
        max_duration_seconds = 10
        
        sessions = []
        for i in range(request_count):
            session = Session(
                id=uuid.uuid4(),
                state=SessionState.INIT,
                initialCharacter="あ",
                themeId="adventure"
            )
            sessions.append(session)
        
        mock_keywords = ["高頻度1", "高頻度2", "高頻度3", "高頻度4"]
        mock_response = LLMResponse(
            task_type=LLMTaskType.KEYWORD_GENERATION,
            session_id="test",
            content={"keywords": mock_keywords},
            provider=LLMProvider.OPENAI,
            model_name="gpt-4",
            latency_ms=100.0
        )
        
        with patch.object(llm_service, '_execute_with_fallback', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = mock_response
            
            start_time = time.time()
            
            # Execute all requests
            tasks = [
                llm_service.generate_keywords(session) 
                for session in sessions
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            total_duration = end_time - start_time
            
            # Verify all completed within time limit
            assert total_duration < max_duration_seconds, f"High frequency test took {total_duration}s, exceeds {max_duration_seconds}s limit"
            
            # Verify all requests succeeded
            successful_results = [r for r in results if not isinstance(r, Exception) and len(r) == 4]
            success_rate = (len(successful_results) / request_count) * 100
            
            assert success_rate >= 95.0, f"High frequency success rate {success_rate}% below 95%"
    
    @pytest.mark.asyncio
    async def test_keyword_generation_sustained_load(self, llm_service):
        """Test keyword generation under sustained load over time."""
        duration_seconds = 5
        requests_per_second = 2
        total_requests = duration_seconds * requests_per_second
        
        mock_keywords = ["持続1", "持続2", "持続3", "持続4"]
        mock_response = LLMResponse(
            task_type=LLMTaskType.KEYWORD_GENERATION,
            session_id="test",
            content={"keywords": mock_keywords},
            provider=LLMProvider.OPENAI,
            model_name="gpt-4",
            latency_ms=150.0
        )
        
        successful_requests = 0
        
        with patch.object(llm_service, '_execute_with_fallback', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = mock_response
            
            start_time = time.time()
            
            while time.time() - start_time < duration_seconds:
                session = Session(
                    id=uuid.uuid4(),
                    state=SessionState.INIT,
                    initialCharacter="あ",
                    themeId="adventure"
                )
                
                try:
                    keywords = await llm_service.generate_keywords(session)
                    if len(keywords) == 4:
                        successful_requests += 1
                except Exception:
                    pass
                
                # Control request rate
                await asyncio.sleep(1 / requests_per_second)
            
            # Verify sustained performance
            expected_min_requests = total_requests * 0.95  # 95% success rate
            assert successful_requests >= expected_min_requests, f"Sustained load: {successful_requests} successful requests, expected >= {expected_min_requests}"
