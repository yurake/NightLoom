"""
Test axis ID consistency between fallback assets and validation expectations.

This test validates that axis IDs follow the expected axis_1, axis_2, axis_3, axis_4 format
throughout the system, ensuring consistency between fallback assets and OpenAI validation.
"""

import pytest
from app.services.fallback_assets import FallbackAssets
from app.clients.openai_client import OpenAIClient
from app.models.llm_config import ProviderConfig, LLMProvider


class TestAxisIDConsistency:
    """Test axis ID consistency across the system."""

    def test_fallback_axes_use_correct_id_format(self):
        """Test that fallback axes use axis_1, axis_2, axis_3, axis_4 format."""
        fallback_manager = FallbackAssets()
        axes = fallback_manager.get_default_axes()
        
        # Should have exactly 4 axes
        assert len(axes) == 4, f"Expected 4 axes, got {len(axes)}"
        
        # Check that axis IDs follow the expected format
        expected_ids = {"axis_1", "axis_2", "axis_3", "axis_4"}
        actual_ids = {axis.id for axis in axes}
        
        assert actual_ids == expected_ids, f"Expected axis IDs {expected_ids}, got {actual_ids}"
        
        # Verify each axis has the correct ID
        for i, axis in enumerate(axes):
            expected_id = f"axis_{i+1}"
            assert axis.id == expected_id, f"Axis {i} should have ID '{expected_id}', got '{axis.id}'"
    
    def test_fallback_scene_choices_use_correct_axis_ids(self):
        """Test that fallback scene choices reference the correct axis IDs."""
        # Test the convenience function
        from app.services.fallback_assets import get_fallback_scene
        scene = get_fallback_scene(scene_index=1, theme_id="adventure")
        
        # Get the expected axis IDs
        expected_axis_ids = {"axis_1", "axis_2", "axis_3", "axis_4"}
        
        # Check all choice weights use correct axis IDs
        for choice in scene.choices:
            choice_axis_ids = set(choice.get_weights_dict().keys())
            
            # All weight keys should be in the expected format
            unexpected_ids = choice_axis_ids - expected_axis_ids
            assert not unexpected_ids, f"Choice '{choice.id}' has unexpected axis IDs: {unexpected_ids}"
            
            # Should have weights for all axes
            missing_ids = expected_axis_ids - choice_axis_ids
            assert not missing_ids, f"Choice '{choice.id}' missing weights for axes: {missing_ids}"
        
        # Also test the get_fallback_scenes method
        fallback_manager = FallbackAssets()
        scenes = fallback_manager.get_fallback_scenes(theme_id="adventure", selected_keyword="test")
        
        for scene in scenes:
            for choice in scene.choices:
                choice_axis_ids = set(choice.get_weights_dict().keys())
                
                # All weight keys should be in the expected format
                unexpected_ids = choice_axis_ids - expected_axis_ids
                assert not unexpected_ids, f"Scene {scene.sceneIndex} Choice '{choice.id}' has unexpected axis IDs: {unexpected_ids}"
                
                # Should have weights for all axes
                missing_ids = expected_axis_ids - choice_axis_ids
                assert not missing_ids, f"Scene {scene.sceneIndex} Choice '{choice.id}' missing weights for axes: {missing_ids}"
    
    def test_fallback_type_profiles_use_correct_axis_ids(self):
        """Test that fallback type profiles reference the correct axis IDs."""
        fallback_manager = FallbackAssets()
        profiles = fallback_manager.get_fallback_type_profiles()
        
        expected_axis_ids = {"axis_1", "axis_2", "axis_3", "axis_4"}
        
        for profile in profiles:
            # Check dominantAxes use correct format
            for axis_id in profile.dominantAxes:
                assert axis_id in expected_axis_ids, f"Profile '{profile.name}' has invalid dominant axis ID: {axis_id}"
