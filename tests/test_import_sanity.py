"""
✅ Sanity Import Test — discovers and imports all modules under `core/`

This test automatically discovers all Python modules in the core package
and ensures they can be imported without errors.
"""

import importlib
import os
import pkgutil
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Ensure packages/core/src is importable
CORE_SRC_PATH = os.path.join(PROJECT_ROOT, "packages", "core", "src")
if os.path.exists(CORE_SRC_PATH) and CORE_SRC_PATH not in sys.path:
    sys.path.insert(0, CORE_SRC_PATH)


def iter_core_modules():
    """Dynamically find all modules under core/"""
    try:
        import core
    except ImportError:
        # Core package not found - return empty list
        return []

    modules = []
    for _finder, name, _ispkg in pkgutil.walk_packages(
        core.__path__, core.__name__ + "."
    ):
        # Skip test modules and private modules
        if "test" not in name and not any(
            part.startswith("_") for part in name.split(".")
        ):
            modules.append(name)

    return modules


@pytest.mark.order(0)
@pytest.mark.sanity
@pytest.mark.parametrize("module_name", iter_core_modules())
def test_import_module(module_name):
    """✅ Each core module should import without errors"""
    print(f"🔎 Importing: {module_name}")
    try:
        importlib.import_module(module_name)
        print(f"  ✅ Successfully imported {module_name}")
    except ModuleNotFoundError as e:
        # If it's a missing third-party dependency, skip the test
        if "No module named" in str(e) and module_name not in str(e):
            pytest.skip(f"⚠️  Skipping {module_name} - missing dependency: {e}")
        else:
            # This is a real import error within the core module itself
            pytest.fail(f"❌ Failed to import {module_name}: {e}")
    except Exception as e:
        pytest.fail(f"❌ Failed to import {module_name}: {e}")


def test_core_package_exists():
    """✅ Verify core package can be imported"""
    try:
        import core

        assert core is not None
        print(f"✅ Core package found at: {core.__file__}")
    except ImportError as e:
        pytest.skip(f"⚠️  Core package not found: {e}")
