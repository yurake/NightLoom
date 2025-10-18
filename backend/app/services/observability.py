"""
Observability service for NightLoom MVP monitoring and metrics.

Provides structured logging, metrics collection, and fallback monitoring
as specified in research.md and plan.md requirements.
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from uuid import UUID


class ObservabilityService:
    """Service for logging, metrics, and monitoring."""
    
    def __init__(self):
        self.metrics_buffer: List[Dict[str, Any]] = []
        self.session_metrics: Dict[str, Dict[str, Any]] = {}
    
    def log_session_start(
        self, 
        session_id: UUID, 
        initial_character: str, 
        theme_id: str,
        fallback_used: bool = False
    ) -> None:
        """Log session bootstrap event."""
        event = {
            "event_type": "session_start",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": str(session_id),
            "initial_character": initial_character,
            "theme_id": theme_id,
            "fallback_used": fallback_used
        }
        
        self._emit_log(event)
        
        # Initialize session metrics
        self.session_metrics[str(session_id)] = {
            "start_time": time.time(),
            "fallback_flags": ["BOOTSTRAP_FALLBACK"] if fallback_used else [],
            "scene_timings": {},
            "api_calls": []
        }
    
    def log_keyword_confirmation(
        self, 
        session_id: UUID, 
        keyword: str, 
        source: str,
        latency_ms: float
    ) -> None:
        """Log keyword confirmation event."""
        event = {
            "event_type": "keyword_confirmation",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": str(session_id),
            "keyword": keyword,
            "source": source,
            "latency_ms": latency_ms
        }
        
        self._emit_log(event)
        self._record_api_timing(str(session_id), "keyword_confirmation", latency_ms)
    
    def log_scene_access(
        self, 
        session_id: UUID, 
        scene_index: int, 
        latency_ms: float,
        fallback_used: bool = False
    ) -> None:
        """Log scene access event."""
        event = {
            "event_type": "scene_access",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": str(session_id),
            "scene_index": scene_index,
            "latency_ms": latency_ms,
            "fallback_used": fallback_used
        }
        
        self._emit_log(event)
        self._record_api_timing(str(session_id), f"scene_{scene_index}", latency_ms)
        
        if fallback_used:
            self._add_fallback_flag(str(session_id), f"SCENE_{scene_index}_FALLBACK")
    
    def log_choice_submission(
        self, 
        session_id: UUID, 
        scene_index: int, 
        choice_id: str,
        latency_ms: float
    ) -> None:
        """Log choice submission event."""
        event = {
            "event_type": "choice_submission",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": str(session_id),
            "scene_index": scene_index,
            "choice_id": choice_id,
            "latency_ms": latency_ms
        }
        
        self._emit_log(event)
        self._record_api_timing(str(session_id), "choice_submission", latency_ms)
    
    def log_result_generation(
        self, 
        session_id: UUID, 
        latency_ms: float,
        fallback_used: bool = False,
        type_count: int = 0
    ) -> None:
        """Log result generation event."""
        event = {
            "event_type": "result_generation",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": str(session_id),
            "latency_ms": latency_ms,
            "fallback_used": fallback_used,
            "type_count": type_count
        }
        
        self._emit_log(event)
        self._record_api_timing(str(session_id), "result_generation", latency_ms)
        
        if fallback_used:
            self._add_fallback_flag(str(session_id), "RESULT_FALLBACK")
    
    def log_session_completion(self, session_id: UUID) -> None:
        """Log session completion and calculate final metrics."""
        session_key = str(session_id)
        metrics = self.session_metrics.get(session_key, {})
        
        if "start_time" in metrics:
            total_duration = (time.time() - metrics["start_time"]) * 1000  # Convert to ms
        else:
            total_duration = 0.0
        
        event = {
            "event_type": "session_completion",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_key,
            "total_duration_ms": total_duration,
            "fallback_flags": metrics.get("fallback_flags", []),
            "api_timings": metrics.get("api_calls", [])
        }
        
        self._emit_log(event)
        
        # Clean up session metrics
        if session_key in self.session_metrics:
            del self.session_metrics[session_key]
    
    def log_llm_request(
        self, 
        session_id: Optional[UUID], 
        endpoint: str, 
        latency_ms: float,
        success: bool,
        retry_count: int = 0,
        fallback_triggered: bool = False
    ) -> None:
        """Log LLM API request details."""
        event = {
            "event_type": "llm_request",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": str(session_id) if session_id else None,
            "endpoint": endpoint,
            "latency_ms": latency_ms,
            "success": success,
            "retry_count": retry_count,
            "fallback_triggered": fallback_triggered
        }
        
        self._emit_log(event)
    
    def log_error(
        self, 
        session_id: Optional[UUID], 
        error_type: str, 
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log error with context."""
        event = {
            "event_type": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": str(session_id) if session_id else None,
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {}
        }
        
        self._emit_log(event)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics summary."""
        # Calculate metrics from recent events
        recent_timings = []
        fallback_count = 0
        total_sessions = len(self.session_metrics)
        
        for session_data in self.session_metrics.values():
            for api_call in session_data.get("api_calls", []):
                recent_timings.append(api_call["latency_ms"])
            
            fallback_count += len(session_data.get("fallback_flags", []))
        
        if recent_timings:
            recent_timings.sort()
            p95_index = int(len(recent_timings) * 0.95)
            p95_latency = recent_timings[p95_index] if p95_index < len(recent_timings) else recent_timings[-1]
            avg_latency = sum(recent_timings) / len(recent_timings)
        else:
            p95_latency = 0.0
            avg_latency = 0.0
        
        return {
            "active_sessions": total_sessions,
            "avg_latency_ms": round(avg_latency, 2),
            "p95_latency_ms": round(p95_latency, 2),
            "fallback_rate": round(fallback_count / max(total_sessions, 1), 3),
            "total_fallbacks": fallback_count
        }
    
    def get_session_metrics(self, session_id: UUID) -> Optional[Dict[str, Any]]:
        """Get metrics for specific session."""
        return self.session_metrics.get(str(session_id))
    
    def _emit_log(self, event: Dict[str, Any]) -> None:
        """Emit log event (currently prints to console)."""
        # In production, this would integrate with proper logging infrastructure
        print(f"[NIGHTLOOM] {json.dumps(event)}")
    
    def _record_api_timing(self, session_id: str, operation: str, latency_ms: float) -> None:
        """Record API timing for session."""
        if session_id in self.session_metrics:
            self.session_metrics[session_id]["api_calls"].append({
                "operation": operation,
                "latency_ms": latency_ms,
                "timestamp": time.time()
            })
    
    def _add_fallback_flag(self, session_id: str, flag: str) -> None:
        """Add fallback flag to session metrics."""
        if session_id in self.session_metrics:
            if flag not in self.session_metrics[session_id]["fallback_flags"]:
                self.session_metrics[session_id]["fallback_flags"].append(flag)
    
    def export_metrics_summary(self) -> Dict[str, Any]:
        """Export comprehensive metrics summary."""
        performance = self.get_performance_metrics()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "performance": performance,
            "active_sessions": len(self.session_metrics),
            "session_details": {
                session_id: {
                    "duration_ms": (time.time() - data["start_time"]) * 1000,
                    "api_calls": len(data.get("api_calls", [])),
                    "fallback_flags": data.get("fallback_flags", [])
                }
                for session_id, data in self.session_metrics.items()
            }
        }


# Global observability instance
observability = ObservabilityService()

# Observability service for API endpoints (alias for compatibility)
observability_service = observability


# Convenience functions
def log_session_event(session_id: UUID, event_type: str, **kwargs) -> None:
    """Log session-related event."""
    if event_type == "start":
        observability.log_session_start(session_id, **kwargs)
    elif event_type == "completion":
        observability.log_session_completion(session_id)
    # Add more event types as needed


def measure_latency(func):
    """Decorator to measure function latency."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            latency_ms = (time.time() - start_time) * 1000
            # Could log this latency if session context is available
    return wrapper


# Additional methods needed by API endpoints
class ObservabilityServiceAPI:
    """Extended observability service with additional API methods."""
    
    def __init__(self, base_service: ObservabilityService):
        self.base = base_service
    
    def start_timer(self, operation: str) -> float:
        """Start a timer for an operation."""
        return time.time()
    
    def increment_counter(self, metric_name: str) -> None:
        """Increment a counter metric."""
        # Simple implementation - could be enhanced with actual metrics storage
        print(f"[METRIC] Counter {metric_name} incremented")
    
    def record_latency(self, operation: str, start_time: float) -> None:
        """Record latency for an operation."""
        latency_ms = (time.time() - start_time) * 1000
        print(f"[METRIC] {operation} latency: {latency_ms:.2f}ms")
    
    def get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()
    
    def get_elapsed_time(self, start_time: float) -> float:
        """Get elapsed time in milliseconds."""
        return (time.time() - start_time) * 1000
    
    def log_info(self, message: str, context: Dict[str, Any] = None) -> None:
        """Log info message with context."""
        event = {
            "level": "info",
            "message": message,
            "timestamp": self.get_current_timestamp(),
            **(context or {})
        }
        print(f"[INFO] {json.dumps(event)}")
    
    def log_error(self, message: str, context: Dict[str, Any] = None) -> None:
        """Log error message with context."""
        event = {
            "level": "error",
            "message": message,
            "timestamp": self.get_current_timestamp(),
            **(context or {})
        }
        print(f"[ERROR] {json.dumps(event)}")


# Enhanced observability service instance for API usage
observability_service = ObservabilityServiceAPI(observability)
