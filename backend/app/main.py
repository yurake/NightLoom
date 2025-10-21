"""FastAPI application entry point.

This file wires up the core routers but leaves the actual business
logic to dedicated service modules. During the backend implementation
phase we will flesh out the bootstrap/keyword endpoints and connect
LLM clients.
"""

import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import ValidationError

from .api import bootstrap, keyword, scenes, choices, results
from .services.observability import observability_service
from .middleware.security import get_security_headers, cleanup_expired_data

# Configure logging
def setup_logging():
    """
    Setup logging configuration for the application.
    
    ログレベル環境変数設定:

    基本設定:
    - LOG_LEVEL: 全体のログレベル (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    個別モジュール設定:
    - OPENAI_LOG_LEVEL: OpenAIクライアントのログレベル
    - LLM_SERVICE_LOG_LEVEL: LLMサービスのログレベル
    - PROMPT_LOG_LEVEL: プロンプトテンプレートのログレベル

    使用例:
      # 開発環境（詳細ログ）
      LOG_LEVEL=DEBUG OPENAI_LOG_LEVEL=DEBUG uvicorn app.main:app --reload
      
      # 本番環境（エラーのみ）
      LOG_LEVEL=ERROR OPENAI_LOG_LEVEL=ERROR uvicorn app.main:app
      
      # 混合設定（OpenAIのみ詳細）
      LOG_LEVEL=INFO OPENAI_LOG_LEVEL=DEBUG uvicorn app.main:app
    """
    # 環境変数からログレベルを取得（デフォルトはINFO）
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # ログレベルの検証
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if log_level not in valid_levels:
        log_level = 'INFO'
    
    # Configure root logger with file output
    log_file = os.getenv("LOG_FILE", "logs/nightloom.log")
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configure logging with both console and file output
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),  # Console output
            logging.FileHandler(log_file, mode='a', encoding='utf-8')  # File output
        ]
    )
    
    # Log the configuration
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: level={log_level}, file={log_file}")
    
    # 個別モジュールのログレベル設定（環境変数で制御）
    openai_log_level = os.getenv('OPENAI_LOG_LEVEL', log_level).upper()
    llm_service_log_level = os.getenv('LLM_SERVICE_LOG_LEVEL', log_level).upper()
    prompt_log_level = os.getenv('PROMPT_LOG_LEVEL', log_level).upper()
    
    # Configure specific loggers with environment variable support
    if openai_log_level in valid_levels:
        logging.getLogger('app.clients.openai_client').setLevel(getattr(logging, openai_log_level))
    else:
        logging.getLogger('app.clients.openai_client').setLevel(logging.DEBUG)
    
    if llm_service_log_level in valid_levels:
        logging.getLogger('app.services.external_llm').setLevel(getattr(logging, llm_service_log_level))
    else:
        logging.getLogger('app.services.external_llm').setLevel(logging.INFO)
    
    if prompt_log_level in valid_levels:
        logging.getLogger('app.services.prompt_template').setLevel(getattr(logging, prompt_log_level))
    else:
        logging.getLogger('app.services.prompt_template').setLevel(logging.DEBUG)
    
    # Keep existing bootstrap logger configuration
    logging.getLogger('app.api.bootstrap').setLevel(logging.INFO)
    
    # Reduce noise from third-party libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    
    # 設定されたログレベルを表示
    logger = logging.getLogger(__name__)
    logger.info(f"Log level configuration:")
    logger.info(f"  Global: {log_level}")
    logger.info(f"  OpenAI Client: {openai_log_level}")
    logger.info(f"  LLM Service: {llm_service_log_level}")
    logger.info(f"  Prompt Template: {prompt_log_level}")

# Initialize logging
setup_logging()

app = FastAPI(
    title="NightLoom Backend",
    version="0.1.0",
    docs_url="/docs" if __debug__ else None,  # Disable docs in production
    redoc_url="/redoc" if __debug__ else None
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "testserver", "*.nightloom.app"]  # Configure for production
)

# Custom error handler for validation errors to include error_code field
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with custom error_code field."""
    errors = exc.errors()
    
    # Extract field information from validation errors
    fields = []
    for error in errors:
        if 'loc' in error and len(error['loc']) > 0:
            field_name = str(error['loc'][-1])  # Get the last part of the location path
            fields.append(field_name)
    
    # Check if this is a UUID validation error (should return 400 instead of 422)
    for error in errors:
        if error.get('type') == 'uuid_parsing' or 'uuid' in error.get('type', '').lower():
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": "VALIDATION_ERROR",
                    "message": "Invalid UUID format",
                    "details": {
                        "field": fields[0] if fields else "session_id",
                        "errors": errors,
                        "timestamp": observability_service.get_current_timestamp()
                    }
                }
            )
    
    return JSONResponse(
        status_code=422,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": "Validation failed",
            "details": {
                "field": fields[0] if fields else "unknown",
                "errors": errors,
                "timestamp": observability_service.get_current_timestamp()
            }
        }
    )

# CORS configuration for frontend-backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Frontend dev server
        "http://127.0.0.1:3000",
        # Add production origins as needed
        # "https://nightloom.app",
        # "https://www.nightloom.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["X-Request-ID"],
    max_age=86400,  # Cache preflight requests for 24 hours
)

# Routers are namespaced for clarity; actual handlers are fully implemented.
app.include_router(bootstrap.router, prefix="/api/sessions", tags=["session"])
app.include_router(keyword.router, prefix="/api/sessions", tags=["session"])
app.include_router(scenes.router, prefix="/api/sessions", tags=["scenes"])
app.include_router(choices.router, prefix="/api/sessions", tags=["choices"])
app.include_router(results.router, prefix="/api/sessions", tags=["results"])


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    
    # Add security headers
    security_headers = get_security_headers()
    for header, value in security_headers.items():
        response.headers[header] = value
    
    return response

@app.middleware("http")
async def cleanup_middleware(request: Request, call_next):
    """Periodic cleanup of expired security data."""
    import random
    
    # Run cleanup on ~1% of requests to avoid performance impact
    if random.random() < 0.01:
        cleanup_expired_data()
    
    response = await call_next(request)
    return response

@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Simple health check endpoint used by monitoring / CI."""
    return {"status": "ok"}

@app.get("/security-stats", tags=["admin"])
async def security_stats():
    """Get security statistics (admin only in production)."""
    from .middleware.security import get_security_stats
    return get_security_stats()
