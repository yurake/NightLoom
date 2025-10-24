"""
Prompt template management system for NightLoom LLM integration.

Manages Jinja2 templates for different LLM tasks with template loading,
caching, and rendering capabilities.
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound, TemplateSyntaxError

from ..clients.llm_client import LLMTaskType


class TemplateError(Exception):
    """Base exception for template errors."""
    pass


class TemplateNotFoundError(TemplateError):
    """Raised when template file is not found."""
    pass


class TemplateRenderError(TemplateError):
    """Raised when template rendering fails."""
    pass


class PromptTemplateManager:
    """Manages prompt templates for LLM operations."""
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize template manager.
        
        Args:
            templates_dir: Path to templates directory. Defaults to backend/templates/prompts/
        """
        if templates_dir is None:
            # Default to backend/templates/prompts/ relative to backend root
            backend_root = Path(__file__).parent.parent.parent
            templates_dir = backend_root / "templates" / "prompts"
        
        self.templates_dir = Path(templates_dir)
        self._env: Optional[Environment] = None
        self._template_cache: Dict[str, Template] = {}
        self._last_modified: Dict[str, float] = {}
        self._cache_enabled = True
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # Template file mappings
        self._template_files = {
            LLMTaskType.KEYWORD_GENERATION: "keyword_generation.jinja2",
            LLMTaskType.AXIS_GENERATION: "axis_creation.jinja2",
            LLMTaskType.SCENARIO_GENERATION: "scenario_generation.j2",
            LLMTaskType.RESULT_ANALYSIS: "result_analysis.j2"
        }
    
    def _ensure_environment(self) -> Environment:
        """Ensure Jinja2 environment is initialized."""
        if self._env is None:
            if not self.templates_dir.exists():
                raise TemplateError(f"Templates directory not found: {self.templates_dir}")
            
            self._env = Environment(
                loader=FileSystemLoader(str(self.templates_dir)),
                trim_blocks=True,
                lstrip_blocks=True,
                keep_trailing_newline=False
            )
            
            # Add custom filters if needed
            self._env.filters['japanese_format'] = self._japanese_format_filter
            
        return self._env
    
    async def render_template(
        self, 
        task_type: LLMTaskType, 
        template_data: Dict[str, Any],
        template_name: Optional[str] = None
    ) -> str:
        """
        Render template for specific task type.
        
        Args:
            task_type: Type of LLM task
            template_ Data to render in template
            template_name: Optional custom template name
            
        Returns:
            Rendered prompt string
            
        Raises:
            TemplateNotFoundError: If template file doesn't exist
            TemplateRenderError: If template rendering fails
        """
        try:
            # Log template rendering start
            template_name_used = template_name or self._template_files.get(task_type, "unknown")
            self.logger.debug(f"[PromptTemplate] Starting template rendering for {task_type} using {template_name_used}")
            
            template = await self._get_template(task_type, template_name)
            rendered = template.render(**template_data)
            rendered_stripped = rendered.strip()
            
            # Log rendered result
            self.logger.debug(f"[PromptTemplate] Rendered {template_name_used}: {rendered_stripped}")
            
            return rendered_stripped
            
        except TemplateNotFound as e:
            self.logger.error(f"[PromptTemplate] Template not found: {e}")
            raise TemplateNotFoundError(f"Template not found: {e}")
        except Exception as e:
            self.logger.error(f"[PromptTemplate] Template rendering failed: {e}")
            raise TemplateRenderError(f"Template rendering failed: {e}")
    
    async def _get_template(self, task_type: LLMTaskType, template_name: Optional[str] = None) -> Template:
        """Get template with caching support."""
        if template_name is None:
            template_name = self._template_files.get(task_type)
            if not template_name:
                raise TemplateNotFoundError(f"No template configured for task type: {task_type}")
        
        cache_key = f"{task_type}:{template_name}"
        
        # Check cache if enabled
        if self._cache_enabled:
            cached_template = self._template_cache.get(cache_key)
            if cached_template and not await self._is_template_modified(template_name):
                return cached_template
        
        # Load template
        env = self._ensure_environment()
        template = env.get_template(template_name)
        
        # Cache template
        if self._cache_enabled:
            self._template_cache[cache_key] = template
            template_path = self.templates_dir / template_name
            if template_path.exists():
                self._last_modified[template_name] = template_path.stat().st_mtime
        
        return template
    
    async def _is_template_modified(self, template_name: str) -> bool:
        """Check if template file has been modified since last cache."""
        template_path = self.templates_dir / template_name
        if not template_path.exists():
            return True
        
        last_modified = self._last_modified.get(template_name, 0)
        current_modified = template_path.stat().st_mtime
        
        return current_modified > last_modified
    
    def _japanese_format_filter(self, value: Any) -> str:
        """Custom Jinja2 filter for Japanese text formatting."""
        if isinstance(value, list):
            if len(value) <= 2:
                return "、".join(value)
            else:
                return "、".join(value[:-1]) + "、および" + value[-1]
        return str(value)
    
    async def validate_template(self, task_type: LLMTaskType, template_name: Optional[str] = None) -> bool:
        """
        Validate template syntax and required variables.
        
        Args:
            task_type: Type of LLM task
            template_name: Optional custom template name
            
        Returns:
            True if template is valid
            
        Raises:
            TemplateNotFoundError: If template doesn't exist
            TemplateError: If template has syntax errors
        """
        try:
            template = await self._get_template(task_type, template_name)
            
            # Check for required variables based on task type
            required_vars = self._get_required_variables(task_type)
            template_vars = self._extract_template_variables(template)
            
            missing_vars = required_vars - template_vars
            if missing_vars:
                raise TemplateError(f"Template missing required variables: {missing_vars}")
            
            return True
            
        except TemplateSyntaxError as e:
            raise TemplateError(f"Template syntax error: {e}")
    
    def _get_required_variables(self, task_type: LLMTaskType) -> set:
        """Get required variables for each task type."""
        required_vars = {
            LLMTaskType.KEYWORD_GENERATION: {"initial_character", "count"},
            LLMTaskType.AXIS_GENERATION: {"keyword", "min_axes", "max_axes"},
            LLMTaskType.SCENARIO_GENERATION: {"keyword", "axes", "scene_index"},
            LLMTaskType.RESULT_ANALYSIS: {"keyword", "axes", "scores", "choices"}
        }
        return required_vars.get(task_type, set())
    
    def _extract_template_variables(self, template: Template) -> set:
        """Extract variables used in template."""
        # This is a simplified extraction - in production you might want 
        # to use ast.parse on the template source for more accurate detection
        source = template.source
        variables = set()
        
        # Simple regex-based extraction for {{ variable }} patterns
        import re
        pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(pattern, source)
        variables.update(matches)
        
        return variables
    
    async def list_templates(self) -> Dict[LLMTaskType, str]:
        """List all available templates."""
        templates = {}
        for task_type, template_file in self._template_files.items():
            template_path = self.templates_dir / template_file
            if template_path.exists():
                templates[task_type] = template_file
        return templates
    
    async def reload_templates(self) -> None:
        """Clear template cache and reload all templates."""
        self._template_cache.clear()
        self._last_modified.clear()
        self._env = None
    
    def enable_cache(self, enabled: bool = True) -> None:
        """Enable or disable template caching."""
        self._cache_enabled = enabled
        if not enabled:
            self._template_cache.clear()
    
    def get_template_info(self, task_type: LLMTaskType) -> Dict[str, Any]:
        """Get information about a template."""
        template_name = self._template_files.get(task_type)
        if not template_name:
            return {"exists": False, "error": "No template configured"}
        
        template_path = self.templates_dir / template_name
        if not template_path.exists():
            return {"exists": False, "error": "Template file not found"}
        
        stat = template_path.stat()
        return {
            "exists": True,
            "name": template_name,
            "path": str(template_path),
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "cached": f"{task_type}:{template_name}" in self._template_cache
        }


# Global template manager instance
_template_manager: Optional[PromptTemplateManager] = None

def get_template_manager() -> PromptTemplateManager:
    """Get global template manager instance."""
    global _template_manager
    if _template_manager is None:
        _template_manager = PromptTemplateManager()
    return _template_manager

async def render_prompt(
    task_type: LLMTaskType, 
    template_data: Dict[str, Any],
    template_name: Optional[str] = None
) -> str:
    """Convenience function to render a prompt template."""
    manager = get_template_manager()
    return await manager.render_template(task_type, template_data, template_name)

async def validate_all_templates() -> Dict[LLMTaskType, bool]:
    """Validate all configured templates."""
    manager = get_template_manager()
    results = {}
    
    for task_type in LLMTaskType:
        try:
            results[task_type] = await manager.validate_template(task_type)
        except Exception:
            results[task_type] = False
    
    return results
