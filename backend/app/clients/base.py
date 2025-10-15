"""
HTTP client wrapper for external LLM calls in NightLoom MVP.

Provides base infrastructure for LLM API calls with timeout, retry logic,
and error handling. Supports the fallback strategy defined in research.md.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime
import httpx


class HTTPClientError(Exception):
    """Base exception for HTTP client errors."""
    pass


class TimeoutError(HTTPClientError):
    """Raised when request exceeds timeout."""
    pass


class RetryExhaustedError(HTTPClientError):
    """Raised when all retry attempts are exhausted."""
    pass


class BaseHTTPClient(ABC):
    """Abstract base class for HTTP clients with retry and timeout support."""
    
    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        max_retries: int = 1,
        retry_delay: float = 1.0,
        headers: Optional[Dict[str, str]] = None
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.default_headers = headers or {}
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def _ensure_client(self):
        """Ensure HTTP client is initialized."""
        if not self._client:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers=self.default_headers
            )
    
    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make POST request with retry logic."""
        await self._ensure_client()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                start_time = datetime.utcnow()
                response = await self._client.post(url, json=data)
                end_time = datetime.utcnow()
                
                latency_ms = (end_time - start_time).total_seconds() * 1000
                await self._log_request("POST", url, response.status_code, latency_ms, attempt)
                
                response.raise_for_status()
                return response.json()
                
            except httpx.TimeoutException:
                last_exception = TimeoutError(f"Request timed out after {self.timeout}s")
                await self._log_error("POST", url, "timeout", attempt)
                
            except httpx.HTTPStatusError as e:
                last_exception = HTTPClientError(f"HTTP {e.response.status_code}")
                await self._log_error("POST", url, f"http_{e.response.status_code}", attempt)
                
            except Exception as e:
                last_exception = HTTPClientError(f"Unexpected error: {str(e)}")
                await self._log_error("POST", url, "unexpected", attempt)
            
            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay)
        
        raise RetryExhaustedError(f"Request failed after {self.max_retries + 1} attempts")
    
    @abstractmethod
    async def _log_request(self, method: str, url: str, status_code: int, latency_ms: float, attempt: int) -> None:
        """Log successful request details."""
        pass
    
    @abstractmethod
    async def _log_error(self, method: str, url: str, error_type: str, attempt: int) -> None:
        """Log error details."""
        pass


class LLMHTTPClient(BaseHTTPClient):
    """HTTP client specifically for LLM API calls."""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, **kwargs):
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        super().__init__(base_url=base_url, headers=headers, **kwargs)
    
    async def _log_request(self, method: str, url: str, status_code: int, latency_ms: float, attempt: int) -> None:
        """Log LLM request details for observability."""
        print(f"LLM Request: {method} {url} -> {status_code} ({latency_ms:.1f}ms, attempt {attempt + 1})")
    
    async def _log_error(self, method: str, url: str, error_type: str, attempt: int) -> None:
        """Log LLM error details."""
        print(f"LLM Error: {method} {url} -> {error_type} (attempt {attempt + 1})")


class MockLLMClient(LLMHTTPClient):
    """Mock LLM client for testing and development."""
    
    def __init__(self):
        super().__init__(base_url="http://mock-llm-api", api_key="mock-key")
    
    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Mock request that returns fallback-like responses."""
        await asyncio.sleep(0.1)  # Simulate network delay
        
        if "bootstrap" in endpoint:
            return {
                "axes": ["logic_emotion", "speed_caution"],
                "keywords": ["希望", "挑戦", "成長", "発見"],
                "theme": "serene",
                "character": "あ"
            }
        elif "scene" in endpoint:
            return {
                "narrative": "モック用のシナリオテキストです。",
                "choices": [
                    {"id": "choice_1_1", "text": "選択肢1", "weights": {"logic_emotion": 0.5}},
                    {"id": "choice_1_2", "text": "選択肢2", "weights": {"logic_emotion": -0.5}},
                    {"id": "choice_1_3", "text": "選択肢3", "weights": {"speed_caution": 0.5}},
                    {"id": "choice_1_4", "text": "選択肢4", "weights": {"speed_caution": -0.5}}
                ]
            }
        elif "result" in endpoint:
            return {
                "types": [
                    {"name": "Mock Type", "description": "テスト用タイプ", "axes": ["logic_emotion", "speed_caution"]}
                ]
            }
        else:
            return {"status": "ok", "message": "Mock response"}
