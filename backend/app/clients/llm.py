"""
LLM Service abstraction with retry and timeout for NightLoom MVP.

Provides high-level interface for LLM operations with automatic fallback
to static assets when external LLM services are unavailable.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from app.clients.base import LLMHTTPClient, MockLLMClient, HTTPClientError, RetryExhaustedError
from app.models.session import Axis, Scene, TypeProfile
from app.services.fallback_assets import (
    get_fallback_axes, 
    get_fallback_keywords, 
    get_fallback_scenes, 
    get_fallback_types
)


class LLMServiceError(Exception):
    """Base exception for LLM service errors."""
    pass


class LLMService(ABC):
    """Abstract base class for LLM service implementations."""
    
    @abstractmethod
    async def generate_bootstrap_data(self, initial_character: str) -> Tuple[List[Axis], List[str], str, bool]:
        """
        Generate initial session data.
        
        Returns:
            - axes: List of evaluation axes
            - keywords: List of keyword candidates  
            - theme_id: Selected theme identifier
            - fallback_used: Whether fallback was used
        """
        pass
    
    @abstractmethod
    async def generate_scenes(
        self, 
        axes: List[Axis], 
        selected_keyword: str, 
        theme_id: str
    ) -> Tuple[List[Scene], bool]:
        """
        Generate all 4 scenes for the diagnosis.
        
        Returns:
            - scenes: List of Scene objects
            - fallback_used: Whether fallback was used
        """
        pass
    
    @abstractmethod
    async def generate_type_profiles(
        self, 
        axes: List[Axis], 
        raw_scores: Dict[str, float],
        selected_keyword: str
    ) -> Tuple[List[TypeProfile], bool]:
        """
        Generate type profiles based on user's scores.
        
        Returns:
            - type_profiles: List of TypeProfile objects
            - fallback_used: Whether fallback was used
        """
        pass


class ExternalLLMService(LLMService):
    """LLM service using external API with fallback support."""
    
    def __init__(
        self, 
        base_url: str, 
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 1
    ):
        self.client = LLMHTTPClient(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries
        )
    
    async def generate_bootstrap_data(self, initial_character: str) -> Tuple[List[Axis], List[str], str, bool]:
        """Generate bootstrap data with fallback on failure."""
        try:
            async with self.client:
                response = await self.client.post("/bootstrap", {
                    "initial_character": initial_character
                })
                
                # Parse response into proper objects
                axes = [
                    Axis(
                        id=axis_data["id"],
                        name=axis_data["name"], 
                        description=axis_data["description"],
                        direction=axis_data["direction"]
                    )
                    for axis_data in response.get("axes", [])
                ]
                
                keywords = response.get("keywords", [])
                theme_id = response.get("theme", "serene")
                
                return axes, keywords, theme_id, False
                
        except (HTTPClientError, RetryExhaustedError, KeyError) as e:
            # Fallback to static assets
            axes = get_fallback_axes()
            keywords = get_fallback_keywords(initial_character)
            theme_id = "fallback"
            
            return axes, keywords, theme_id, True
    
    async def generate_scenes(
        self, 
        axes: List[Axis], 
        selected_keyword: str, 
        theme_id: str
    ) -> Tuple[List[Scene], bool]:
        """Generate scenes with fallback on failure."""
        try:
            async with self.client:
                response = await self.client.post("/scenes", {
                    "axes": [{"id": axis.id, "name": axis.name} for axis in axes],
                    "keyword": selected_keyword,
                    "theme_id": theme_id
                })
                
                # Parse response into Scene objects
                scenes = []
                for scene_data in response.get("scenes", []):
                    scene = Scene(
                        sceneIndex=scene_data["sceneIndex"],
                        themeId=scene_data["themeId"],
                        narrative=scene_data["narrative"],
                        choices=scene_data["choices"]  # Assumes proper Choice format
                    )
                    scenes.append(scene)
                
                return scenes, False
                
        except (HTTPClientError, RetryExhaustedError, KeyError) as e:
            # Fallback to static scenes
            scenes = get_fallback_scenes(theme_id, selected_keyword)
            return scenes, True
    
    async def generate_type_profiles(
        self, 
        axes: List[Axis], 
        raw_scores: Dict[str, float],
        selected_keyword: str
    ) -> Tuple[List[TypeProfile], bool]:
        """Generate type profiles with fallback on failure."""
        try:
            async with self.client:
                response = await self.client.post("/types", {
                    "axes": [{"id": axis.id, "name": axis.name} for axis in axes],
                    "scores": raw_scores,
                    "keyword": selected_keyword
                })
                
                # Parse response into TypeProfile objects
                profiles = []
                for profile_data in response.get("profiles", []):
                    profile = TypeProfile(
                        name=profile_data["name"],
                        description=profile_data["description"],
                        keywords=profile_data.get("keywords", []),
                        dominantAxes=profile_data["dominantAxes"],
                        polarity=profile_data["polarity"],
                        meta=profile_data.get("meta", {})
                    )
                    profiles.append(profile)
                
                return profiles, False
                
        except (HTTPClientError, RetryExhaustedError, KeyError) as e:
            # Fallback to static profiles
            profiles = get_fallback_types()
            return profiles, True


class MockLLMService(LLMService):
    """Mock LLM service for testing and development."""
    
    def __init__(self, simulate_failures: bool = False):
        self.simulate_failures = simulate_failures
        self._failure_count = 0
    
    async def generate_bootstrap_data(self, initial_character: str) -> Tuple[List[Axis], List[str], str, bool]:
        """Mock bootstrap generation with optional failure simulation."""
        await asyncio.sleep(0.1)  # Simulate processing time
        
        if self.simulate_failures and self._failure_count < 2:
            self._failure_count += 1
            raise LLMServiceError("Simulated LLM failure")
        
        # Use fallback assets as mock data
        axes = get_fallback_axes()
        keywords = get_fallback_keywords(initial_character)
        theme_id = "serene"
        
        return axes, keywords, theme_id, False
    
    async def generate_scenes(
        self, 
        axes: List[Axis], 
        selected_keyword: str, 
        theme_id: str
    ) -> Tuple[List[Scene], bool]:
        """Mock scene generation."""
        await asyncio.sleep(0.2)  # Simulate processing time
        
        scenes = get_fallback_scenes(theme_id, selected_keyword)
        return scenes, False
    
    async def generate_type_profiles(
        self, 
        axes: List[Axis], 
        raw_scores: Dict[str, float],
        selected_keyword: str
    ) -> Tuple[List[TypeProfile], bool]:
        """Mock type profile generation."""
        await asyncio.sleep(0.1)  # Simulate processing time
        
        profiles = get_fallback_types()
        return profiles, False


# Service factory
def create_llm_service(
    service_type: str = "mock",
    **kwargs
) -> LLMService:
    """Create LLM service instance based on configuration."""
    if service_type == "external":
        return ExternalLLMService(**kwargs)
    elif service_type == "mock":
        return MockLLMService(**kwargs)
    else:
        raise ValueError(f"Unknown LLM service type: {service_type}")


# Default service instance for MVP
default_llm_service = create_llm_service("mock")
