
"""
LLM API usage metrics tracking for NightLoom.

Tracks token usage, costs, latency, and rate limits for LLM providers
with session-based monitoring and alerts.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json

from ..models.llm_config import LLMProvider
from ..clients.llm_client import LLMTaskType, LLMResponse, LLMError


class MetricType(str, Enum):
    """Types of metrics tracked."""
    TOKEN_USAGE = "token_usage"
    COST = "cost"
    LATENCY = "latency"
    ERROR_RATE = "error_rate"
    RATE_LIMIT = "rate_limit"


@dataclass
class MetricPoint:
    """Individual metric measurement."""
    timestamp: datetime
    provider: LLMProvider
    task_type: LLMTaskType
    session_id: str
    metric_type: MetricType
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "provider": self.provider.value,
            "task_type": self.task_type.value,
            "session_id": self.session_id,
            "metric_type": self.metric_type.value,
            "value": self.value,
            "metadata": self.metadata
        }


@dataclass
class SessionMetrics:
    """Aggregated metrics for a session."""
    session_id: str
    total_tokens: int = 0
    total_cost: float = 0.0
    avg_latency_ms: float = 0.0
    total_requests: int = 0
    error_count: int = 0
    provider_breakdown: Dict[LLMProvider, Dict[str, Any]] = field(default_factory=dict)
    task_breakdown: Dict[LLMTaskType, Dict[str, Any]] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    last_activity: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "session_id": self.session_id,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "avg_latency_ms": self.avg_latency_ms,
            "total_requests": self.total_requests,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(self.total_requests, 1),
            "provider_breakdown": {
                p.value: stats for p, stats in self.provider_breakdown.items()
            },
            "task_breakdown": {
                t.value: stats for t, stats in self.task_breakdown.items()
            },
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "duration_seconds": (
                (self.last_activity - self.start_time).total_seconds()
                if self.start_time and self.last_activity else 0
            )
        }


class LLMMetricsTracker:
    """Tracks and aggregates LLM usage metrics."""
    
    def __init__(self, cost_per_token: Optional[Dict[LLMProvider, float]] = None):
        """
        Initialize metrics tracker.
        
        Args:
            cost_per_token: Cost per token for each provider (USD)
        """
        self._metrics: List[MetricPoint] = []
        self._session_metrics: Dict[str, SessionMetrics] = {}
        self._cost_per_token = cost_per_token or {
            LLMProvider.OPENAI: 0.00003,  # Approximate GPT-4 cost
            LLMProvider.ANTHROPIC: 0.00003,  # Approximate Claude cost
            LLMProvider.MOCK: 0.0
        }
        
        # Rate limiting tracking
        self._rate_limits: Dict[LLMProvider, Dict[str, Any]] = {}
        self._request_windows: Dict[LLMProvider, List[datetime]] = {}
        
        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup()

    async def record_response(self, response: LLMResponse) -> None:
        """Record metrics from successful LLM response."""
        now = datetime.now(timezone.utc)
        
        # Record token usage
        if response.tokens_used:
            await self._add_metric(
                MetricPoint(
                    timestamp=now,
                    provider=response.provider,
                    task_type=response.task_type,
                    session_id=response.session_id,
                    metric_type=MetricType.TOKEN_USAGE,
                    value=float(response.tokens_used),
                    metadata={"model": response.model_name}
                )
            )
        
        # Record latency
        if response.latency_ms:
            await self._add_metric(
                MetricPoint(
                    timestamp=now,
                    provider=response.provider,
                    task_type=response.task_type,
                    session_id=response.session_id,
                    metric_type=MetricType.LATENCY,
                    value=response.latency_ms,
                    metadata={"model": response.model_name}
                )
            )
        
        # Record cost
        cost = response.cost_estimate or (
            response.tokens_used * self._cost_per_token.get(response.provider, 0.0)
            if response.tokens_used else 0.0
        )
        if cost > 0:
            await self._add_metric(
                MetricPoint(
                    timestamp=now,
                    provider=response.provider,
                    task_type=response.task_type,
                    session_id=response.session_id,
                    metric_type=MetricType.COST,
                    value=cost,
                    metadata={"model": response.model_name}
                )
            )
        
        # Update session metrics
        await self._update_session_metrics(response.session_id, response, success=True)
        
        # Update rate limit tracking
        await self._track_rate_limit(response.provider, now)

    async def record_error(self, error: LLMError) -> None:
        """Record metrics from LLM error."""
        now = datetime.now(timezone.utc)
        
        await self._add_metric(
            MetricPoint(
                timestamp=now,
                provider=error.provider,
                task_type=error.task_type,
                session_id=error.session_id,
                metric_type=MetricType.ERROR_RATE,
                value=1.0,
                metadata={
                    "error_type": error.error_type,
                    "retry_count": error.retry_count,
                    "is_retryable": error.is_retryable
                }
            )
        )
        
        # Update session metrics
        await self._update_session_metrics(error.session_id, None, success=False)

    async def _add_metric(self, metric: MetricPoint) -> None:
        """Add metric point to collection."""
        self._metrics.append(metric)

    async def _update_session_metrics(
        self, 
        session_id: str, 
        response: Optional[LLMResponse], 
        success: bool
    ) -> None:
        """Update aggregated session metrics."""
        if session_id not in self._session_metrics:
            self._session_metrics[session_id] = SessionMetrics(
                session_id=session_id,
                start_time=datetime.now(timezone.utc)
            )
        
        metrics = self._session_metrics[session_id]
        metrics.last_activity = datetime.now(timezone.utc)
        metrics.total_requests += 1
        
        if success and response:
            if response.tokens_used:
                metrics.total_tokens += response.tokens_used
            
            if response.cost_estimate:
                metrics.total_cost += response.cost_estimate
            elif response.tokens_used:
                cost = response.tokens_used * self._cost_per_token.get(response.provider, 0.0)
                metrics.total_cost += cost
            
            if response.latency_ms:
                # Update running average
                old_avg = metrics.avg_latency_ms
                n = metrics.total_requests - metrics.error_count
                metrics.avg_latency_ms = ((old_avg * (n - 1)) + response.latency_ms) / n
            
            # Update provider breakdown
            if response.provider not in metrics.provider_breakdown:
                metrics.provider_breakdown[response.provider] = {
                    "requests": 0, "tokens": 0, "cost": 0.0, "avg_latency": 0.0
                }
            
            provider_stats = metrics.provider_breakdown[response.provider]
            provider_stats["requests"] += 1
            if response.tokens_used:
                provider_stats["tokens"] += response.tokens_used
            if response.cost_estimate:
                provider_stats["cost"] += response.cost_estimate
            if response.latency_ms:
                old_avg = provider_stats["avg_latency"]
                n = provider_stats["requests"]
                provider_stats["avg_latency"] = ((old_avg * (n - 1)) + response.latency_ms) / n
            
            # Update task breakdown
            if response.task_type not in metrics.task_breakdown:
                metrics.task_breakdown[response.task_type] = {
                    "requests": 0, "tokens": 0, "cost": 0.0, "avg_latency": 0.0
                }
            
            task_stats = metrics.task_breakdown[response.task_type]
            task_stats["requests"] += 1
            if response.tokens_used:
                task_stats["tokens"] += response.tokens_used
            if response.cost_estimate:
                task_stats["cost"] += response.cost_estimate
            if response.latency_ms:
                old_avg = task_stats["avg_latency"]
                n = task_stats["requests"]
                task_stats["avg_latency"] = ((old_avg * (n - 1)) + response.latency_ms) / n
        
        else:
            metrics.error_count += 1

    async def _track_rate_limit(self, provider: LLMProvider, timestamp: datetime) -> None:
        """Track rate limit for provider."""
        if provider not in self._request_windows:
            self._request_windows[provider] = []
        
        window = self._request_windows[provider]
        window.append(timestamp)
        
        # Keep only requests from last minute
        cutoff = timestamp - timedelta(minutes=1)
        self._request_windows[provider] = [t for t in window if t > cutoff]

    async def get_session_metrics(self, session_id: str) -> Optional[SessionMetrics]:
        """Get metrics for specific session."""
        return self._session_metrics.get(session_id)

    async def get_provider_rate_limit_status(self, provider: LLMProvider) -> Dict[str, Any]:
        """Get current rate limit status for provider."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=1)
        
        recent_requests = [
            t for t in self._request_windows.get(provider, []) 
            if t > cutoff
        ]
        
        # Provider-specific limits (requests per minute)
        limits = {
            LLMProvider.OPENAI: 60,
            LLMProvider.ANTHROPIC: 60,
            LLMProvider.MOCK: 1000
        }
        
        limit = limits.get(provider, 60)
        current_usage = len(recent_requests)
        
        return {
            "provider": provider.value,
            "current_usage": current_usage,
            "limit": limit,
            "usage_percentage": (current_usage / limit) * 100,
            "is_approaching_limit": current_usage > (limit * 0.8),
            "is_at_limit": current_usage >= limit,
            "reset_time": (cutoff + timedelta(minutes=1)).isoformat()
        }

    async def get_global_metrics(
        self, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get aggregated global metrics."""
        if start_time is None:
            start_time = datetime.now(timezone.utc) - timedelta(hours=24)
        if end_time is None:
            end_time = datetime.now(timezone.utc)
        
        # Filter metrics by time range
        filtered_metrics = [
            m for m in self._metrics 
            if start_time <= m.timestamp <= end_time
        ]
        
        # Aggregate by provider and task type
        provider_stats = {}
        task_stats = {}
        
        for metric in filtered_metrics:
            # Provider aggregation
            if metric.provider not in provider_stats:
                provider_stats[metric.provider] = {
                    "total_tokens": 0, "total_cost": 0.0, "total_requests": 0,
                    "avg_latency": 0.0, "error_count": 0
                }
            
            stats = provider_stats[metric.provider]
            if metric.metric_type == MetricType.TOKEN_USAGE:
                stats["total_tokens"] += metric.value
            elif metric.metric_type == MetricType.COST:
                stats["total_cost"] += metric.value
            elif metric.metric_type == MetricType.ERROR_RATE:
                stats["error_count"] += metric.value
            
            stats["total_requests"] += 1
            
            # Task type aggregation
            if metric.task_type not in task_stats:
                task_stats[metric.task_type] = {
                    "total_tokens": 0, "total_cost": 0.0, "total_requests": 0,
                    "avg_latency": 0.0, "error_count": 0
                }
            
            task_stat = task_stats[metric.task_type]
            if metric.metric_type == MetricType.TOKEN_USAGE:
                task_stat["total_tokens"] += metric.value
            elif metric.metric_type == MetricType.COST:
                task_stat["total_cost"] += metric.value
            elif metric.metric_type == MetricType.ERROR_RATE:
                task_stat["error_count"] += metric.value
            
            task_stat["total_requests"] += 1
        
        return {
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "provider_breakdown": {
                p.value: stats for p, stats in provider_stats.items()
            },
            "task_breakdown": {
                t.value: stats for t, stats in task_stats.items()
            },
            "active_sessions": len(self._session_metrics),
            "total_metrics": len(filtered_metrics)
        }

    def _start_cleanup(self) -> None:
        """Start background cleanup task."""
        try:
            # Only create task if there's a running event loop
            loop = asyncio.get_running_loop()
            if self._cleanup_task is None or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(self._cleanup_old_metrics())
        except RuntimeError:
            # No event loop running, skip cleanup task creation
            # This is common during testing or module import
            self._cleanup_task = None
    
    async def _cleanup_old_metrics(self) -> None:
        """Clean up old metrics periodically."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
                
                # Remove old metrics
                self._metrics = [m for m in self._metrics if m.timestamp > cutoff]
                
                # Remove inactive sessions
                inactive_sessions = [
                    sid for sid, metrics in self._session_metrics.items()
                    if metrics.last_activity and metrics.last_activity < cutoff
                ]
                for sid in inactive_sessions:
                    del self._session_metrics[sid]
                
            except Exception as e:
                print(f"Metrics cleanup error: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute on error


# Global metrics tracker instance
_metrics_tracker: Optional[LLMMetricsTracker] = None

def get_metrics_tracker() -> LLMMetricsTracker:
    """Get global metrics tracker instance."""
    global _metrics_tracker
    if _metrics_tracker is None:
        _metrics_tracker = LLMMetricsTracker()
    return _metrics_tracker

async def record_llm_response(response: LLMResponse) -> None:
    """Convenience function to record LLM response metrics."""
    tracker = get_metrics_tracker()
    await tracker.record_response(response)

async def record_llm_error(error: LLMError) -> None:
    """Convenience function to record LLM error metrics."""
    tracker = get_metrics_tracker()
    await tracker.record_error(error)

async def get_session_usage(session_id: str) -> Optional[Dict[str, Any]]:
    """Get usage metrics for a session."""
    tracker = get_metrics_tracker()
    metrics = await tracker.get_session_metrics(session_id)
    return metrics.to_dict() if metrics else None
