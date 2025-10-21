
"""
LLM request monitoring middleware for NightLoom.

Provides comprehensive monitoring, logging, and alerting for LLM operations
with request/response tracking, performance monitoring, and error analysis.
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum

from ..models.llm_config import LLMProvider
from ..clients.llm_client import LLMTaskType, LLMRequest, LLMResponse, LLMError
from ..services.llm_metrics import get_metrics_tracker


class AlertLevel(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class LLMRequestLog:
    """Comprehensive LLM request log entry."""
    request_id: str
    session_id: str
    task_type: LLMTaskType
    provider: LLMProvider
    model_name: Optional[str] = None
    
    # Timing
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    
    # Request details
    template_data: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Response details
    success: bool = False
    tokens_used: Optional[int] = None
    cost_estimate: Optional[float] = None
    response_size: Optional[int] = None
    
    # Error details
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    fallback_used: bool = False
    
    # Performance metrics
    queue_time_ms: Optional[float] = None
    processing_time_ms: Optional[float] = None
    network_time_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "request_id": self.request_id,
            "session_id": self.session_id,
            "task_type": self.task_type.value,
            "provider": self.provider.value,
            "model_name": self.model_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "tokens_used": self.tokens_used,
            "cost_estimate": self.cost_estimate,
            "response_size": self.response_size,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "fallback_used": self.fallback_used,
            "queue_time_ms": self.queue_time_ms,
            "processing_time_ms": self.processing_time_ms,
            "network_time_ms": self.network_time_ms
        }


@dataclass
class MonitoringAlert:
    """Monitoring alert with context."""
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "level": self.level.value,
            "title": self.title,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context
        }


class LLMMonitoringMiddleware:
    """
    Middleware for comprehensive LLM operation monitoring.
    
    Tracks requests, responses, errors, performance metrics,
    and generates alerts based on configurable thresholds.
    """
    
    def __init__(
        self,
        max_log_entries: int = 10000,
        alert_thresholds: Optional[Dict[str, Any]] = None,
        enable_detailed_logging: bool = True
    ):
        """
        Initialize monitoring middleware.
        
        Args:
            max_log_entries: Maximum number of log entries to retain
            alert_thresholds: Alert threshold configuration
            enable_detailed_logging: Whether to log detailed request/response data
        """
        self.max_log_entries = max_log_entries
        self.enable_detailed_logging = enable_detailed_logging
        
        # Default alert thresholds
        self.alert_thresholds = alert_thresholds or {
            "error_rate_threshold": 0.1,     # 10% error rate
            "latency_p95_threshold": 10000,  # 10 seconds
            "token_cost_threshold": 0.1,     # $0.10 per request
            "queue_time_threshold": 5000,    # 5 seconds
            "consecutive_failures": 3        # 3 consecutive failures
        }
        
        # Monitoring data
        self.request_logs: List[LLMRequestLog] = []
        self.alerts: List[MonitoringAlert] = []
        self.active_requests: Dict[str, LLMRequestLog] = {}
        
        # Performance tracking
        self.metrics_window: List[Dict[str, Any]] = []
        self.provider_health: Dict[LLMProvider, Dict[str, Any]] = {}
        
        # Alert state tracking
        self._consecutive_failures: Dict[LLMProvider, int] = {}
        self._last_health_check = datetime.now(timezone.utc)
        
        # Background monitoring task
        self._monitoring_task: Optional[asyncio.Task] = None
        self._start_background_monitoring()
    
    async def before_request(
        self, 
        request: LLMRequest, 
        provider: LLMProvider,
        request_id: str
    ) -> str:
        """
        Called before LLM request execution.
        
        Args:
            request: LLM request object
            provider: Provider handling the request
            request_id: Unique request identifier
            
        Returns:
            Request ID for tracking
        """
        log_entry = LLMRequestLog(
            request_id=request_id,
            session_id=request.session_id,
            task_type=request.task_type,
            provider=provider,
            template_data=request.template_data if self.enable_detailed_logging else {},
            context=request.context or {}
        )
        
        self.active_requests[request_id] = log_entry
        
        # Update provider tracking
        if provider not in self.provider_health:
            self.provider_health[provider] = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "avg_latency_ms": 0.0,
                "last_success": None,
                "last_failure": None
            }
        
        self.provider_health[provider]["total_requests"] += 1
        
        return request_id
    
    async def after_response(
        self, 
        request_id: str, 
        response: LLMResponse,
        processing_time_ms: Optional[float] = None
    ) -> None:
        """
        Called after successful LLM response.
        
        Args:
            request_id: Request identifier
            response: LLM response object
            processing_time_ms: Optional processing time
        """
        if request_id not in self.active_requests:
            return
        
        log_entry = self.active_requests[request_id]
        log_entry.end_time = datetime.now(timezone.utc)
        log_entry.duration_ms = (log_entry.end_time - log_entry.start_time).total_seconds() * 1000
        log_entry.success = True
        log_entry.model_name = response.model_name
        log_entry.tokens_used = response.tokens_used
        log_entry.cost_estimate = response.cost_estimate
        log_entry.processing_time_ms = processing_time_ms
        
        if response.content:
            log_entry.response_size = len(json.dumps(response.content))
        
        # Update provider health
        provider_stats = self.provider_health[log_entry.provider]
        provider_stats["successful_requests"] += 1
        provider_stats["last_success"] = log_entry.end_time
        
        # Update average latency
        total_requests = provider_stats["total_requests"]
        old_avg = provider_stats["avg_latency_ms"]
        new_latency = log_entry.duration_ms or 0
        provider_stats["avg_latency_ms"] = ((old_avg * (total_requests - 1)) + new_latency) / total_requests
        
        # Reset consecutive failures on success
        self._consecutive_failures[log_entry.provider] = 0
        
        # Move to completed logs
        self._finalize_log_entry(request_id, log_entry)
        
        # Check for performance alerts
        await self._check_performance_alerts(log_entry)
    
    async def after_error(
        self, 
        request_id: str, 
        error: LLMError,
        processing_time_ms: Optional[float] = None
    ) -> None:
        """
        Called after LLM request error.
        
        Args:
            request_id: Request identifier
            error: Error information
            processing_time_ms: Optional processing time
        """
        if request_id not in self.active_requests:
            return
        
        log_entry = self.active_requests[request_id]
        log_entry.end_time = datetime.now(timezone.utc)
        log_entry.duration_ms = (log_entry.end_time - log_entry.start_time).total_seconds() * 1000
        log_entry.success = False
        log_entry.error_type = error.error_type
        log_entry.error_message = error.error_message
        log_entry.retry_count = error.retry_count
        log_entry.processing_time_ms = processing_time_ms
        
        # Update provider health
        provider_stats = self.provider_health[log_entry.provider]
        provider_stats["failed_requests"] += 1
        provider_stats["last_failure"] = log_entry.end_time
        
        # Track consecutive failures
        if log_entry.provider not in self._consecutive_failures:
            self._consecutive_failures[log_entry.provider] = 0
        self._consecutive_failures[log_entry.provider] += 1
        
        # Move to completed logs
        self._finalize_log_entry(request_id, log_entry)
        
        # Check for error alerts
        await self._check_error_alerts(log_entry)
    
    def _finalize_log_entry(self, request_id: str, log_entry: LLMRequestLog) -> None:
        """Move log entry from active to completed logs."""
        del self.active_requests[request_id]
        self.request_logs.append(log_entry)
        
        # Maintain log size limit
        if len(self.request_logs) > self.max_log_entries:
            self.request_logs = self.request_logs[-self.max_log_entries:]
    
    async def _check_performance_alerts(self, log_entry: LLMRequestLog) -> None:
        """Check for performance-related alerts."""
        # High latency alert
        if (log_entry.duration_ms and 
            log_entry.duration_ms > self.alert_thresholds["latency_p95_threshold"]):
            await self._create_alert(
                AlertLevel.WARNING,
                "High Latency Detected",
                f"Request {log_entry.request_id} took {log_entry.duration_ms:.1f}ms "
                f"(threshold: {self.alert_thresholds['latency_p95_threshold']}ms)",
                {
                    "provider": log_entry.provider.value,
                    "task_type": log_entry.task_type.value,
                    "session_id": log_entry.session_id,
                    "duration_ms": log_entry.duration_ms
                }
            )
        
        # High cost alert
        if (log_entry.cost_estimate and 
            log_entry.cost_estimate > self.alert_thresholds["token_cost_threshold"]):
            await self._create_alert(
                AlertLevel.WARNING,
                "High Cost Request",
                f"Request {log_entry.request_id} cost ${log_entry.cost_estimate:.4f} "
                f"(threshold: ${self.alert_thresholds['token_cost_threshold']:.4f})",
                {
                    "provider": log_entry.provider.value,
                    "task_type": log_entry.task_type.value,
                    "session_id": log_entry.session_id,
                    "cost_estimate": log_entry.cost_estimate,
                    "tokens_used": log_entry.tokens_used
                }
            )
    
    async def _check_error_alerts(self, log_entry: LLMRequestLog) -> None:
        """Check for error-related alerts."""
        provider = log_entry.provider
        consecutive_failures = self._consecutive_failures.get(provider, 0)
        
        # Consecutive failures alert
        if consecutive_failures >= self.alert_thresholds["consecutive_failures"]:
            await self._create_alert(
                AlertLevel.ERROR,
                "Consecutive Failures Detected",
                f"Provider {provider.value} has {consecutive_failures} consecutive failures",
                {
                    "provider": provider.value,
                    "consecutive_failures": consecutive_failures,
                    "last_error": log_entry.error_message,
                    "error_type": log_entry.error_type
                }
            )
        
        # Check error rate
        provider_stats = self.provider_health[provider]
        total = provider_stats["total_requests"]
        failed = provider_stats["failed_requests"]
        
        if total > 10:  # Only check after reasonable sample size
            error_rate = failed / total
            if error_rate > self.alert_thresholds["error_rate_threshold"]:
                await self._create_alert(
                    AlertLevel.WARNING,
                    "High Error Rate",
                    f"Provider {provider.value} error rate: {error_rate:.1%} "
                    f"(threshold: {self.alert_thresholds['error_rate_threshold']:.1%})",
                    {
                        "provider": provider.value,
                        "error_rate": error_rate,
                        "total_requests": total,
                        "failed_requests": failed
                    }
                )
    
    async def _create_alert(
        self, 
        level: AlertLevel, 
        title: str, 
        message: str,
        context: Dict[str, Any]
    ) -> None:
        """Create and store alert."""
        alert = MonitoringAlert(
            level=level,
            title=title,
            message=message,
            context=context
        )
        
        self.alerts.append(alert)
        
        # Log alert
        print(f"[{level.value.upper()}] {title}: {message}")
        
        
        self.alerts.append(alert)
        
        # Log alert
        print(f"[{level.value.upper()}] {title}: {message}")
        
        # Maintain alert history limit
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]
    
    def _start_background_monitoring(self) -> None:
        """Start background monitoring tasks."""
        if self._monitoring_task is None or self._monitoring_task.done():
            self._monitoring_task = asyncio.create_task(self._background_monitor())
    
    async def _background_monitor(self) -> None:
        """Background monitoring loop."""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                # Health checks
                await self._periodic_health_check()
                
                # Cleanup old data
                await self._cleanup_old_data()
                
            except Exception as e:
                print(f"Background monitoring error: {e}")
                await asyncio.sleep(30)  # Retry after 30 seconds on error
    
    async def _periodic_health_check(self) -> None:
        """Perform periodic health checks."""
        now = datetime.now(timezone.utc)
        
        # Check for inactive providers
        for provider, stats in self.provider_health.items():
            if stats["last_success"]:
                time_since_success = (now - stats["last_success"]).total_seconds()
                if time_since_success > 3600:  # No success in 1 hour
                    await self._create_alert(
                        AlertLevel.WARNING,
                        "Provider Inactive",
                        f"Provider {provider.value} has not succeeded in {time_since_success/60:.1f} minutes",
                        {
                            "provider": provider.value,
                            "minutes_since_success": time_since_success / 60,
                            "last_success": stats["last_success"].isoformat()
                        }
                    )
        
        self._last_health_check = now
    
    async def _cleanup_old_data(self) -> None:
        """Clean up old monitoring data."""
        from datetime import timedelta
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        
        # Remove old alerts
        self.alerts = [
            alert for alert in self.alerts
            if alert.timestamp > cutoff_time
        ]
        
        # Remove old metrics
        self.metrics_window = [
            metric for metric in self.metrics_window
            if metric.get("timestamp", 0) > cutoff_time.timestamp()
        ]
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get comprehensive monitoring summary."""
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        
        # Calculate time-based metrics
        recent_logs = [
            log for log in self.request_logs
            if (now - log.start_time).total_seconds() < 3600  # Last hour
        ]
        
        successful_logs = [log for log in recent_logs if log.success]
        failed_logs = [log for log in recent_logs if not log.success]
        
        # Provider breakdown
        provider_summary = {}
        for provider in self.provider_health:
            provider_logs = [log for log in recent_logs if log.provider == provider]
            provider_summary[provider.value] = {
                "total_requests": len(provider_logs),
                "successful_requests": len([log for log in provider_logs if log.success]),
                "failed_requests": len([log for log in provider_logs if not log.success]),
                "avg_latency_ms": (
                    sum(log.duration_ms or 0 for log in provider_logs if log.duration_ms) /
                    len(provider_logs) if provider_logs else 0
                ),
                "health_status": self.provider_health[provider]
            }
        
        # Recent alerts
        recent_alerts = [
            alert for alert in self.alerts
            if (now - alert.timestamp).total_seconds() < 3600
        ]
        
        return {
            "monitoring_period": {
                "start_time": (now - timedelta(hours=1)).isoformat(),
                "end_time": now.isoformat()
            },
            "request_summary": {
                "total_requests": len(recent_logs),
                "successful_requests": len(successful_logs),
                "failed_requests": len(failed_logs),
                "success_rate": len(successful_logs) / max(len(recent_logs), 1),
                "avg_latency_ms": (
                    sum(log.duration_ms or 0 for log in successful_logs) /
                    max(len(successful_logs), 1)
                )
            },
            "provider_breakdown": provider_summary,
            "active_requests": len(self.active_requests),
            "recent_alerts": {
                "total": len(recent_alerts),
                "by_level": {
                    level.value: len([a for a in recent_alerts if a.level == level])
                    for level in AlertLevel
                }
            },
            "system_health": self._calculate_system_health()
        }


# Global monitoring instance
_monitoring_middleware: Optional[LLMMonitoringMiddleware] = None

def get_monitoring_middleware() -> LLMMonitoringMiddleware:
    """Get global monitoring middleware instance."""
    global _monitoring_middleware
    if _monitoring_middleware is None:
        _monitoring_middleware = LLMMonitoringMiddleware()
    return _monitoring_middleware
