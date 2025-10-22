"""
Mock LLM client implementation for testing and development.

Provides a mock implementation of BaseLLMClient that returns predefined responses
without making actual API calls.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from .llm_client import BaseLLMClient, LLMRequest, LLMResponse, LLMProvider
from ..models.llm_config import ProviderConfig


class MockLLMClient(BaseLLMClient):
    """Mock LLM client for testing and development."""
    
    def __init__(self, config: ProviderConfig = None):
        """Initialize mock client (config is ignored for mock)."""
        # Create a dummy config with all required fields
        if not config:
            config = ProviderConfig(
                provider=LLMProvider.MOCK,
                model_name="mock-model",
                api_key="mock-key"
            )
        super().__init__(config)
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
    
    async def generate_keywords(self, request: LLMRequest) -> LLMResponse:
        """Generate mock keywords."""
        await asyncio.sleep(0.1)  # Simulate network delay
        
        initial_character = request.template_data.get("initial_character", "あ")
        self.logger.info(f"[Mock] Generating keywords for: {initial_character}")
        
        # Mock keyword generation based on initial character
        mock_keywords = [
            {"word": "愛情", "reading": f"{initial_character}いじょう"},
            {"word": "明るい", "reading": f"{initial_character}かるい"},
            {"word": "新しい", "reading": f"{initial_character}たらしい"}, 
            {"word": "温かい", "reading": f"{initial_character}たたかい"}
        ]
        
        response = LLMResponse(
            task_type=request.task_type,
            session_id=request.session_id,
            content={"keywords": mock_keywords},
            provider=LLMProvider.MOCK,
            model_name="mock-model",
            tokens_used=100,
            latency_ms=100.0,
            cost_estimate=0.0,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Update metrics
        self._update_metrics("generate_keywords", latency_ms=100.0, tokens_used=100)
        
        self.logger.info(f"[Mock] Generated keywords: {[kw['word'] for kw in mock_keywords]}")
        return response
    
    async def generate_axes(self, request: LLMRequest) -> LLMResponse:
        """Generate mock axes."""
        await asyncio.sleep(0.1)  # Simulate network delay
        
        keyword = request.template_data.get("keyword", "愛情")
        self.logger.info(f"[Mock] Generating axes for keyword: {keyword}")
        
        # Mock axis generation based on keyword
        mock_axes = [
            {
                "id": "axis_1",
                "name": "感情表現",
                "description": "感情を表現する傾向の強さ",
                "direction": "表現的 ⟷ 内省的"
            },
            {
                "id": "axis_2",
                "name": "行動力",
                "description": "積極的に行動を起こす傾向",
                "direction": "能動的 ⟷ 受動的"
            },
            {
                "id": "axis_3",
                "name": "共感性",
                "description": "他者の感情に共感する度合い",
                "direction": "共感的 ⟷ 客観的"
            },
            {
                "id": "axis_4",
                "name": "コミット度",
                "description": "関係に対する献身的な姿勢",
                "direction": "献身的 ⟷ 自立的"
            }
        ]
        
        response = LLMResponse(
            task_type=request.task_type,
            session_id=request.session_id,
            content={"axes": mock_axes},
            provider=LLMProvider.MOCK,
            model_name="mock-model",
            tokens_used=120,
            latency_ms=100.0,
            cost_estimate=0.0,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Update metrics
        self._update_metrics("generate_axes", latency_ms=100.0, tokens_used=120)
        
        self.logger.info(f"[Mock] Generated {len(mock_axes)} axes for keyword '{keyword}'")
        return response
    
    async def generate_scenario(self, request: LLMRequest) -> LLMResponse:
        """Generate mock scenario.""" 
        raise NotImplementedError("Mock scenario generation not implemented")
    
    async def analyze_results(self, request: LLMRequest) -> LLMResponse:
        """Analyze mock results."""
        raise NotImplementedError("Mock result analysis not implemented")
    
    async def health_check(self) -> bool:
        """Mock health check always returns True."""
        self.logger.debug("[Mock] Health check: always healthy")
        return True
