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
        raise NotImplementedError("Mock axes generation not implemented")
    
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
