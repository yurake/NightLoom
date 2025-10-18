"""
Security middleware for NightLoom MVP.

Provides input validation, rate limiting, and request security
for API endpoints.
"""

import time
import hashlib
from typing import Dict, List, Optional, Tuple
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field, field_validator
import re
from datetime import datetime, timedelta
from collections import defaultdict, deque

# Rate limiting storage (in production, use Redis or similar)
rate_limit_storage: Dict[str, deque] = defaultdict(deque)
blocked_ips: Dict[str, datetime] = {}

class SecurityConfig:
    """Security configuration constants."""
    
    # Rate limiting
    MAX_REQUESTS_PER_MINUTE = 60
    MAX_REQUESTS_PER_HOUR = 500
    BLOCK_DURATION_MINUTES = 15
    
    # Input validation
    MAX_KEYWORD_LENGTH = 100
    MAX_SESSION_ID_LENGTH = 36
    ALLOWED_CHARACTERS = re.compile(r'^[a-zA-Z0-9\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\u3400-\u4DBF.,!?-]+$')
    
    # Session security
    SESSION_TIMEOUT_HOURS = 2
    MAX_ACTIVE_SESSIONS_PER_IP = 10

class InputSanitizer:
    """Input sanitization and validation utilities."""
    
    @staticmethod
    def sanitize_keyword(keyword: str) -> str:
        """Sanitize user keyword input."""
        if not keyword:
            raise ValueError("Keyword cannot be empty")
        
        # Remove leading/trailing whitespace
        keyword = keyword.strip()
        
        # Check length
        if len(keyword) > SecurityConfig.MAX_KEYWORD_LENGTH:
            raise ValueError(f"Keyword too long (max {SecurityConfig.MAX_KEYWORD_LENGTH} characters)")
        
        # Check for allowed characters (including Japanese)
        if not SecurityConfig.ALLOWED_CHARACTERS.match(keyword):
            raise ValueError("Keyword contains invalid characters")
        
        # Remove potentially dangerous patterns
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>.*?</iframe>',
        ]
        
        for pattern in dangerous_patterns:
            keyword = re.sub(pattern, '', keyword, flags=re.IGNORECASE)
        
        return keyword
    
    @staticmethod
    def validate_session_id(session_id: str) -> bool:
        """Validate session ID format."""
        if not session_id:
            return False
        
        if len(session_id) != SecurityConfig.MAX_SESSION_ID_LENGTH:
            return False
        
        # UUID format validation
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        
        return bool(uuid_pattern.match(session_id))
    
    @staticmethod
    def sanitize_choice_id(choice_id: str) -> str:
        """Sanitize choice ID input."""
        if not choice_id:
            raise ValueError("Choice ID cannot be empty")
        
        # Only allow alphanumeric and underscore
        if not re.match(r'^[a-zA-Z0-9_]+$', choice_id):
            raise ValueError("Invalid choice ID format")
        
        return choice_id

class RateLimiter:
    """Rate limiting functionality."""
    
    @staticmethod
    def get_client_identifier(request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Use X-Forwarded-For if available (behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP from the chain
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        # Hash IP for privacy (in production)
        return hashlib.sha256(client_ip.encode()).hexdigest()[:16]
    
    @staticmethod
    def is_blocked(client_id: str) -> bool:
        """Check if client is currently blocked."""
        if client_id in blocked_ips:
            block_time = blocked_ips[client_id]
            if datetime.now() - block_time < timedelta(minutes=SecurityConfig.BLOCK_DURATION_MINUTES):
                return True
            else:
                # Remove expired block
                del blocked_ips[client_id]
        return False
    
    @staticmethod
    def check_rate_limit(client_id: str) -> Tuple[bool, Dict[str, int]]:
        """Check if client has exceeded rate limits."""
        now = time.time()
        client_requests = rate_limit_storage[client_id]
        
        # Clean old requests (older than 1 hour)
        while client_requests and now - client_requests[0] > 3600:
            client_requests.popleft()
        
        # Count requests in different time windows
        requests_last_minute = sum(1 for req_time in client_requests if now - req_time <= 60)
        requests_last_hour = len(client_requests)
        
        # Check limits
        if requests_last_minute >= SecurityConfig.MAX_REQUESTS_PER_MINUTE:
            return False, {
                "requests_last_minute": requests_last_minute,
                "requests_last_hour": requests_last_hour,
                "limit_minute": SecurityConfig.MAX_REQUESTS_PER_MINUTE,
                "limit_hour": SecurityConfig.MAX_REQUESTS_PER_HOUR
            }
        
        if requests_last_hour >= SecurityConfig.MAX_REQUESTS_PER_HOUR:
            # Block client for excessive requests
            blocked_ips[client_id] = datetime.now()
            return False, {
                "requests_last_minute": requests_last_minute,
                "requests_last_hour": requests_last_hour,
                "limit_minute": SecurityConfig.MAX_REQUESTS_PER_MINUTE,
                "limit_hour": SecurityConfig.MAX_REQUESTS_PER_HOUR,
                "blocked_until": (datetime.now() + timedelta(minutes=SecurityConfig.BLOCK_DURATION_MINUTES)).isoformat()
            }
        
        return True, {
            "requests_last_minute": requests_last_minute,
            "requests_last_hour": requests_last_hour,
            "limit_minute": SecurityConfig.MAX_REQUESTS_PER_MINUTE,
            "limit_hour": SecurityConfig.MAX_REQUESTS_PER_HOUR
        }
    
    @staticmethod
    def record_request(client_id: str):
        """Record a request for rate limiting."""
        rate_limit_storage[client_id].append(time.time())

def get_rate_limiter(request: Request):
    """FastAPI dependency for rate limiting."""
    client_id = RateLimiter.get_client_identifier(request)
    
    # Check if client is blocked
    if RateLimiter.is_blocked(client_id):
        raise HTTPException(
            status_code=429,
            detail={
                "error_code": "RATE_LIMITED",
                "message": "Too many requests. Client temporarily blocked.",
                "retry_after": SecurityConfig.BLOCK_DURATION_MINUTES * 60
            }
        )
    
    # Check rate limits
    allowed, stats = RateLimiter.check_rate_limit(client_id)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "error_code": "RATE_LIMITED", 
                "message": "Rate limit exceeded",
                "stats": stats
            }
        )
    
    # Record this request
    RateLimiter.record_request(client_id)
    return client_id

class SecureKeywordRequest(BaseModel):
    """Secure keyword request with validation."""
    keyword: str = Field(..., min_length=1, max_length=SecurityConfig.MAX_KEYWORD_LENGTH)
    source: str = Field(..., pattern=r'^(suggestion|manual)$')
    
    @field_validator('keyword')
    def validate_keyword(cls, v):
        return InputSanitizer.sanitize_keyword(v)

class SecureChoiceRequest(BaseModel):
    """Secure choice request with validation."""
    choiceId: str = Field(..., min_length=1, max_length=50)
    
    @field_validator('choiceId')
    def validate_choice_id(cls, v):
        return InputSanitizer.sanitize_choice_id(v)

def validate_session_id(session_id: str) -> str:
    """Validate session ID parameter."""
    if not InputSanitizer.validate_session_id(session_id):
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_SESSION_ID",
                "message": "Invalid session ID format"
            }
        )
    return session_id

def get_security_headers():
    """Get security headers for responses."""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    }

# Security utilities for cleanup
def cleanup_expired_data():
    """Clean up expired rate limiting data."""
    now = time.time()
    
    # Clean rate limiting storage
    for client_id in list(rate_limit_storage.keys()):
        requests = rate_limit_storage[client_id]
        while requests and now - requests[0] > 3600:
            requests.popleft()
        
        # Remove empty entries
        if not requests:
            del rate_limit_storage[client_id]
    
    # Clean expired blocks
    now_dt = datetime.now()
    for client_id in list(blocked_ips.keys()):
        block_time = blocked_ips[client_id]
        if now_dt - block_time >= timedelta(minutes=SecurityConfig.BLOCK_DURATION_MINUTES):
            del blocked_ips[client_id]

def get_security_stats() -> Dict:
    """Get security statistics."""
    return {
        "active_rate_limits": len(rate_limit_storage),
        "blocked_clients": len(blocked_ips),
        "total_requests_tracked": sum(len(requests) for requests in rate_limit_storage.values())
    }
