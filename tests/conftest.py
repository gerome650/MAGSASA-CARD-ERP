"""
Ensures the project root is in sys.path so imports like `core.*` work.
Fixes `ModuleNotFoundError: No module named 'core'`.
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Ensure packages/core/src is importable for core module tests
CORE_SRC_PATH = os.path.join(PROJECT_ROOT, "packages", "core", "src")
if os.path.exists(CORE_SRC_PATH) and CORE_SRC_PATH not in sys.path:
    sys.path.insert(0, CORE_SRC_PATH)
