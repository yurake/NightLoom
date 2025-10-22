"""
Unit tests for evaluation axis generation validation (User Story 2).

Tests axis data structure validation, content quality checks,
and constraint enforcement for dynamically generated axes.
"""

import pytest
from typing import Dict, Any, List

from app.services.external_llm import AxisValidator
from app.clients.llm_client import ValidationError


class TestAxisValidation:
    """Unit tests for axis validation logic."""

    def test_valid_axis_structure(self):
        """Test validation of properly structured axis data."""
        valid_axis = {
            "id": "axis_1",
            "name": "感情表現",
            "description": "感情を表現する傾向の強さ",
            "direction": "表現的 ⟷ 内省的"
        }
        
        validator = AxisValidator()
        # Should not raise any exception
        validator.validate_axis(valid_axis, index=1)

    def test_missing_required_fields(self):
        """Test validation fails when required fields are missing."""
        validator = AxisValidator()
        
        # Missing 'id'
        invalid_axis = {
            "name": "感情表現",
            "description": "感情を表現する傾向の強さ",
            "direction": "表現的 ⟷ 内省的"
        }
        with pytest.raises(ValidationError, match="missing.*id"):
            validator.validate_axis(invalid_axis, index=1)
        
        # Missing 'name'
        invalid_axis = {
            "id": "axis_1",
            "description": "感情を表現する傾向の強さ",
            "direction": "表現的 ⟷ 内省的"
        }
        with pytest.raises(ValidationError, match="missing.*name"):
            validator.validate_axis(invalid_axis, index=1)
        
        # Missing 'description'
        invalid_axis = {
            "id": "axis_1",
            "name": "感情表現",
            "direction": "表現的 ⟷ 内省的"
        }
        with pytest.raises(ValidationError, match="missing.*description"):
            validator.validate_axis(invalid_axis, index=1)
        
        # Missing 'direction'
        invalid_axis = {
            "id": "axis_1",
            "name": "感情表現", 
            "description": "感情を表現する傾向の強さ"
        }
        with pytest.raises(ValidationError, match="missing.*direction"):
            validator.validate_axis(invalid_axis, index=1)

    def test_invalid_field_types(self):
        """Test validation fails when fields have wrong types."""
        validator = AxisValidator()
        
        # Non-string id
        invalid_axis = {
            "id": 123,
            "name": "感情表現",
            "description": "感情を表現する傾向の強さ",
            "direction": "表現的 ⟷ 内省的"
        }
        with pytest.raises(ValidationError, match="id.*string"):
            validator.validate_axis(invalid_axis, index=1)
        
        # Non-string name
        invalid_axis = {
            "id": "axis_1",
            "name": ["感情表現"],
            "description": "感情を表現する傾向の強さ", 
            "direction": "表現的 ⟷ 内省的"
        }
        with pytest.raises(ValidationError, match="name.*string"):
            validator.validate_axis(invalid_axis, index=1)

    def test_empty_field_values(self):
        """Test validation fails when fields are empty."""
        validator = AxisValidator()
        
        # Empty id
        invalid_axis = {
            "id": "",
            "name": "感情表現",
            "description": "感情を表現する傾向の強さ",
            "direction": "表現的 ⟷ 内省的"
        }
        with pytest.raises(ValidationError, match="id.*empty"):
            validator.validate_axis(invalid_axis, index=1)
        
        # Whitespace-only name
        invalid_axis = {
            "id": "axis_1", 
            "name": "   ",
            "description": "感情を表現する傾向の強さ",
            "direction": "表現的 ⟷ 内省的"
        }
        with pytest.raises(ValidationError, match="name.*empty"):
            validator.validate_axis(invalid_axis, index=1)

    def test_direction_format_validation(self):
        """Test validation of axis direction format."""
        validator = AxisValidator()
        
        # Valid direction formats
        valid_directions = [
            "表現的 ⟷ 内省的",
            "積極的⟷消極的",
            "感情重視 ⟷ 論理重視",
            "A ⟷ B"
        ]
        
        for direction in valid_directions:
            axis = {
                "id": "axis_1",
                "name": "テスト軸",
                "description": "テスト用の軸", 
                "direction": direction
            }
            # Should not raise exception
            validator.validate_axis(axis, index=1)
        
        # Invalid direction formats (missing arrow)
        invalid_directions = [
            "表現的 内省的",
            "積極的vs消極的",
            "感情重視から論理重視",
            "単一方向"
        ]
        
        for direction in invalid_directions:
            axis = {
                "id": "axis_1",
                "name": "テスト軸", 
                "description": "テスト用の軸",
                "direction": direction
            }
            with pytest.raises(ValidationError, match="direction.*⟷"):
                validator.validate_axis(axis, index=1)

    def test_axis_id_format_validation(self):
        """Test validation of axis ID format."""
        validator = AxisValidator()
        
        # Valid ID formats
        valid_ids = ["axis_1", "axis_2", "axis_10", "evaluation_axis_1"]
        
        for axis_id in valid_ids:
            axis = {
                "id": axis_id,
                "name": "テスト軸",
                "description": "テスト用の軸",
                "direction": "A ⟷ B"
            }
            # Should not raise exception
            validator.validate_axis(axis, index=1)
        
        # Invalid ID formats
        invalid_ids = ["", "axis-1", "axis 1", "1axis", "軸1"]
        
        for axis_id in invalid_ids:
            axis = {
                "id": axis_id,
                "name": "テスト軸",
                "description": "テスト用の軸", 
                "direction": "A ⟷ B"
            }
            with pytest.raises(ValidationError):
                validator.validate_axis(axis, index=1)

    def test_axis_collection_validation(self):
        """Test validation of complete axis collections."""
        validator = AxisValidator()
        
        # Valid collection (3 axes)
        valid_axes = [
            {
                "id": "axis_1",
                "name": "感情表現",
                "description": "感情を表現する傾向",
                "direction": "表現的 ⟷ 内省的"
            },
            {
                "id": "axis_2", 
                "name": "決断スタイル",
                "description": "決断を下すスタイル",
                "direction": "直感的 ⟷ 分析的"
            },
            {
                "id": "axis_3",
                "name": "社交性",
                "description": "社交的な傾向",
                "direction": "外向的 ⟷ 内向的"
            }
        ]
        
        # Should not raise exception
        validator.validate_axes_collection(valid_axes)

    def test_axis_count_constraints(self):
        """Test that axis count stays within 2-6 range."""
        validator = AxisValidator()
        
        # Too few axes (1)
        single_axis = [{
            "id": "axis_1",
            "name": "テスト軸",
            "description": "テスト用",
            "direction": "A ⟷ B"
        }]
        
        with pytest.raises(ValidationError, match="2-6 axes"):
            validator.validate_axes_collection(single_axis)
        
        # Too many axes (7)
        many_axes = []
        for i in range(1, 8):
            many_axes.append({
                "id": f"axis_{i}",
                "name": f"軸{i}",
                "description": f"テスト軸{i}",
                "direction": "A ⟷ B"
            })
        
        with pytest.raises(ValidationError, match="2-6 axes"):
            validator.validate_axes_collection(many_axes)

    def test_duplicate_axis_ids(self):
        """Test validation fails when axis IDs are duplicated."""
        validator = AxisValidator()
        
        # Duplicate axis IDs
        duplicate_axes = [
            {
                "id": "axis_1",
                "name": "感情表現",
                "description": "感情表現の傾向", 
                "direction": "表現的 ⟷ 内省的"
            },
            {
                "id": "axis_1",  # Duplicate ID
                "name": "決断スタイル",
                "description": "決断スタイル",
                "direction": "直感的 ⟷ 分析的"
            }
        ]
        
        with pytest.raises(ValidationError, match="duplicate.*id"):
            validator.validate_axes_collection(duplicate_axes)

    def test_axis_name_length_validation(self):
        """Test validation of axis name length constraints."""
        validator = AxisValidator()
        
        # Name too long
        long_name_axis = {
            "id": "axis_1",
            "name": "非常に長すぎる軸の名前でありこれは制限を超えている" * 3,
            "description": "テスト用の軸",
            "direction": "A ⟷ B"
        }
        
        with pytest.raises(ValidationError, match="name.*length"):
            validator.validate_axis(long_name_axis, index=1)
        
        # Description too long
        long_desc_axis = {
            "id": "axis_1", 
            "name": "テスト軸",
            "description": "非常に長すぎる説明文でありこれは制限を大幅に超えているテストケースである" * 10,
            "direction": "A ⟷ B"
        }
        
        with pytest.raises(ValidationError, match="description.*length"):
            validator.validate_axis(long_desc_axis, index=1)


class AxisValidator:
    """Axis validation utility class."""
    
    def validate_axis(self, axis: Dict[str, Any], index: int) -> None:
        """Validate single axis structure and content."""
        if not isinstance(axis, dict):
            raise ValidationError(f"Axis {index} must be an object")
        
        # Check required fields
        required_fields = ["id", "name", "description", "direction"]
        for field in required_fields:
            if field not in axis:
                raise ValidationError(f"Axis {index} missing required field: {field}")
            
            if not isinstance(axis[field], str):
                raise ValidationError(f"Axis {index} field '{field}' must be a string")
            
            if not axis[field].strip():
                raise ValidationError(f"Axis {index} field '{field}' cannot be empty")
        
        # Validate ID format (alphanumeric + underscore)
        axis_id = axis["id"]
        if not axis_id.replace("_", "").replace("-", "").isalnum():
            if not all(c.isalnum() or c == "_" for c in axis_id):
                raise ValidationError(f"Axis {index} ID contains invalid characters")
        
        # Validate direction format (must contain ⟷)
        direction = axis["direction"]
        if "⟷" not in direction:
            raise ValidationError(f"Axis {index} direction must contain '⟷' separator")
        
        # Validate length constraints
        if len(axis["name"]) > 50:
            raise ValidationError(f"Axis {index} name too long (max 50 characters)")
        
        if len(axis["description"]) > 200:
            raise ValidationError(f"Axis {index} description too long (max 200 characters)")
    
    def validate_axes_collection(self, axes: List[Dict[str, Any]]) -> None:
        """Validate collection of axes."""
        if not isinstance(axes, list):
            raise ValidationError("Axes must be a list")
        
        # Check count constraints
        if len(axes) < 2 or len(axes) > 6:
            raise ValidationError(f"Expected 2-6 axes, got {len(axes)}")
        
        # Validate each axis
        axis_ids = set()
        for i, axis in enumerate(axes):
            self.validate_axis(axis, i + 1)
            
            # Check for duplicate IDs
            axis_id = axis["id"]
            if axis_id in axis_ids:
                raise ValidationError(f"Duplicate axis ID: {axis_id}")
            axis_ids.add(axis_id)
