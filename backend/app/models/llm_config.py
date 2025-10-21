"""
LLM Provider configuration system for NightLoom.

Manages configuration for multiple LLM providers (OpenAI, Anthropic)
with environment-based settings and provider selection logic.
"""

import os
from enum import Enum
from typing import Dict, Optional, List
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MOCK = "mock"


class ProviderConfig(BaseModel):
    """Configuration for a specific LLM provider."""
    provider: LLMProvider
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: str
    max_tokens: int = Field(default=1000, ge=100, le=4000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    timeout_seconds: float = Field(default=5.0, ge=1.0, le=30.0)
    max_retries: int = Field(default=1, ge=0, le=3)
    enabled: bool = Field(default=True)

    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v, info):
        """Validate API key is provided for non-mock providers."""
        if info.data and 'provider' in info.data:
            provider = info.data['provider']
            if provider != LLMProvider.MOCK and not v:
                raise ValueError(f"API key required for provider {provider}")
        return v


class LLMConfig(BaseModel):
    """Master LLM configuration containing all provider configurations."""
    primary_provider: LLMProvider = Field(default=LLMProvider.OPENAI)
    fallback_providers: List[LLMProvider] = Field(default_factory=lambda: [LLMProvider.MOCK])
    providers: Dict[LLMProvider, ProviderConfig] = Field(default_factory=dict)
    
    # Rate limiting configuration
    rate_limit_threshold: float = Field(default=0.95, ge=0.5, le=1.0)
    cost_limit_per_session: float = Field(default=0.05, gt=0.0)
    
    # Quality control
    response_validation_enabled: bool = Field(default=True)
    fallback_on_validation_failure: bool = Field(default=True)

    @field_validator('providers')
    @classmethod
    def validate_providers_exist(cls, v, info):
        """Ensure primary and fallback providers are configured."""
        if info.data:
            primary = info.data.get('primary_provider')
            fallbacks = info.data.get('fallback_providers', [])
            
            all_required = [primary] + fallbacks
            for provider in all_required:
                if provider and provider not in v:
                    raise ValueError(f"Provider {provider} must be configured")
        
        return v

    def get_provider_config(self, provider: LLMProvider) -> Optional[ProviderConfig]:
        """Get configuration for a specific provider."""
        return self.providers.get(provider)

    def get_enabled_providers(self) -> List[LLMProvider]:
        """Get list of enabled providers."""
        return [
            provider for provider, config in self.providers.items() 
            if config.enabled
        ]

    def get_fallback_chain(self) -> List[LLMProvider]:
        """Get ordered list of providers for fallback chain."""
        chain = [self.primary_provider]
        chain.extend([
            provider for provider in self.fallback_providers 
            if provider != self.primary_provider
        ])
        return [p for p in chain if p in self.get_enabled_providers()]


def load_config_from_env() -> LLMConfig:
    """Load LLM configuration from environment variables."""
    
    # Load .env file from project root and current directory
    load_dotenv(dotenv_path="../.env")  # Project root
    load_dotenv(dotenv_path=".env")     # Current directory (backend/)
    
    # Determine primary provider
    primary_provider_name = os.getenv("LLM_PROVIDER", "openai").lower()
    try:
        primary_provider = LLMProvider(primary_provider_name)
    except ValueError:
        primary_provider = LLMProvider.OPENAI

    # Configure providers
    providers = {}
    
    # OpenAI configuration
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        providers[LLMProvider.OPENAI] = ProviderConfig(
            provider=LLMProvider.OPENAI,
            api_key=openai_api_key,
            model_name=os.getenv("OPENAI_MODEL", "gpt-4"),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "1000")),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
            timeout_seconds=float(os.getenv("OPENAI_TIMEOUT", "5.0")),
        )
    
    # Anthropic configuration
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_api_key:
        providers[LLMProvider.ANTHROPIC] = ProviderConfig(
            provider=LLMProvider.ANTHROPIC,
            api_key=anthropic_api_key,
            model_name=os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
            max_tokens=int(os.getenv("ANTHROPIC_MAX_TOKENS", "1000")),
            temperature=float(os.getenv("ANTHROPIC_TEMPERATURE", "0.7")),
            timeout_seconds=float(os.getenv("ANTHROPIC_TIMEOUT", "5.0")),
        )
    
    # Mock provider (always available for fallback)
    providers[LLMProvider.MOCK] = ProviderConfig(
        provider=LLMProvider.MOCK,
        model_name="mock-model",
        max_tokens=1000,
        temperature=0.7,
        timeout_seconds=1.0,
    )
    
    # Determine fallback chain
    fallback_providers = []
    if primary_provider != LLMProvider.OPENAI and LLMProvider.OPENAI in providers:
        fallback_providers.append(LLMProvider.OPENAI)
    if primary_provider != LLMProvider.ANTHROPIC and LLMProvider.ANTHROPIC in providers:
        fallback_providers.append(LLMProvider.ANTHROPIC)
    fallback_providers.append(LLMProvider.MOCK)  # Always include mock as final fallback
    
    return LLMConfig(
        primary_provider=primary_provider,
        fallback_providers=fallback_providers,
        providers=providers,
        rate_limit_threshold=float(os.getenv("LLM_RATE_LIMIT_THRESHOLD", "0.95")),
        cost_limit_per_session=float(os.getenv("LLM_COST_LIMIT_PER_SESSION", "0.05")),
        response_validation_enabled=os.getenv("LLM_RESPONSE_VALIDATION", "true").lower() == "true",
        fallback_on_validation_failure=os.getenv("LLM_FALLBACK_ON_VALIDATION", "true").lower() == "true",
    )


# Global configuration instance
_config: Optional[LLMConfig] = None

def get_llm_config() -> LLMConfig:
    """Get the global LLM configuration instance."""
    global _config
    if _config is None:
        _config = load_config_from_env()
    return _config

def reload_config() -> LLMConfig:
    """Reload configuration from environment variables."""
    global _config
    _config = load_config_from_env()
    return _config
