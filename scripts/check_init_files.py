#!/usr/bin/env python3
"""
🔍 __init__.py Checker/Creator

Ensures all Python packages under `core/` have __init__.py files.
Can run in check-only mode for CI or auto-create mode locally.

Usage:
    python scripts/check_init_files.py              # Auto-create missing __init__.py
    python scripts/check_init_files.py --check-only # CI mode - fail if missing
"""

import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CORE_DIR = os.path.join(ROOT_DIR, "packages", "core", "src", "core")

missing = []


def check_init_files():
    """Walk the core directory and find missing __init__.py files."""
    if not os.path.exists(CORE_DIR):
        print(f"⚠️  Core directory not found: {CORE_DIR}")
        print("   This is okay if you don't have a core package yet.")
        return []

    missing_files = []
    for dirpath, dirnames, filenames in os.walk(CORE_DIR):
        # Skip __pycache__ and other special directories
        if "__pycache__" in dirpath or ".git" in dirpath:
            continue

        # Check if directory contains Python files or subdirectories (making it a potential package)
        has_py_files = any(f.endswith(".py") for f in filenames)
        has_subdirs = len([d for d in dirnames if not d.startswith(".")]) > 0

        if (has_py_files or has_subdirs) and "__init__.py" not in filenames:
            init_path = os.path.join(dirpath, "__init__.py")
            missing_files.append(init_path)

    return missing_files


def main():
    """Main entry point for the checker/creator."""
    check_only = "--check-only" in sys.argv

    missing = check_init_files()

    if check_only:
        if missing:
            print("❌ Missing __init__.py files:")
            for m in missing:
                print(f"   {m}")
            print("\n💡 Run without --check-only to auto-create these files.")
            sys.exit(1)
        else:
            print("✅ All packages have __init__.py")
            sys.exit(0)

    # Auto-create mode
    if not missing:
        print("✅ All packages already have __init__.py files")
        sys.exit(0)

    print(f"🔧 Creating {len(missing)} missing __init__.py file(s)...")
    for m in missing:
        try:
            with open(m, "w") as f:
                f.write("# Auto-created by check_init_files.py\n")
            print(f"  ✅ Created: {m}")
        except Exception as e:
            print(f"  ❌ Failed to create {m}: {e}")
            sys.exit(1)

    print("✨ Done. All __init__.py files present.")


if __name__ == "__main__":
    main()
