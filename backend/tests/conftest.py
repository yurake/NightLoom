"""Test configuration for backend package."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure `import app` resolves to the backend application package when tests run
# via uv / pytest in isolated environments.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
