#!/usr/bin/env python3
"""
🔧 Development Dependencies Installer

Ensures all development and testing dependencies are properly installed.
Checks for virtual environment and provides helpful guidance.

Usage:
    python scripts/setup/install_dev_dependencies.py
    python scripts/setup/install_dev_dependencies.py --check-only
"""

import os
import subprocess
import sys
from pathlib import Path


def is_in_venv() -> bool:
    """Check if running inside a virtual environment."""
    return (
        hasattr(sys, "real_prefix")
        or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
        or os.environ.get("VIRTUAL_ENV") is not None
    )


def get_venv_path() -> Path | None:
    """Get the path to the virtual environment if it exists."""
    repo_root = Path(__file__).parent.parent.parent
    venv_paths = [
        repo_root / ".venv",
        repo_root / "venv",
    ]

    for venv_path in venv_paths:
        if venv_path.exists():
            return venv_path

    return None


def check_pip() -> bool:
    """Check if pip is available and working."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


def ensure_pip():
    """Ensure pip is installed."""
    if not check_pip():
        print("📦 pip not found, installing...")
        try:
            subprocess.run([sys.executable, "-m", "ensurepip", "--upgrade"], check=True)
            print("✅ pip installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install pip: {e}")
            sys.exit(1)


def install_requirements(requirements_file: Path, check_only: bool = False) -> bool:
    """Install dependencies from requirements file.

    Args:
        requirements_file: Path to requirements file
        check_only: If True, only check if installed (don't install)

    Returns:
        True if successful
    """
    if not requirements_file.exists():
        print(f"❌ Requirements file not found: {requirements_file}")
        return False

    if check_only:
        print(f"🔍 Checking dependencies from {requirements_file.name}...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "check"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                print("✅ All dependencies satisfied")
                return True
            else:
                print("⚠️  Some dependencies missing or broken:")
                print(result.stdout)
                return False
        except Exception as e:
            print(f"❌ Failed to check dependencies: {e}")
            return False

    print(f"📦 Installing dependencies from {requirements_file.name}...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
            check=True,
        )
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def install_uv_dependencies() -> bool:
    """Install dependencies using uv (if available)."""
    try:
        # Check if uv is available
        result = subprocess.run(
            ["uv", "--version"], capture_output=True, text=True, check=False
        )

        if result.returncode == 0:
            print("🚀 Installing dependencies with uv...")
            subprocess.run(["uv", "sync"], check=True)
            print("✅ uv sync completed")
            return True
    except FileNotFoundError:
        pass
    except subprocess.CalledProcessError:
        pass

    return False


def main():
    """Main installation logic."""
    print("=" * 70)
    print("🔧 Development Dependencies Installer")
    print("=" * 70)
    print()

    # Parse arguments
    check_only = "--check-only" in sys.argv

    # Check virtual environment
    in_venv = is_in_venv()
    venv_path = get_venv_path()

    print("📋 Environment Check:")
    print(f"   Python: {sys.version.split()[0]}")
    print(f"   Location: {sys.executable}")
    print(f"   Virtual Env: {'✅ Active' if in_venv else '❌ Not Active'}")

    if venv_path:
        print(f"   Venv Path: {venv_path}")

    print()

    if not in_venv:
        print("⚠️  WARNING: Not running in a virtual environment!")
        print()
        print("💡 It's recommended to use a virtual environment:")
        print()
        if venv_path:
            print("   # Activate existing venv:")
            print(f"   source {venv_path}/bin/activate")
        else:
            print("   # Create and activate venv:")
            print("   python3 -m venv .venv")
            print("   source .venv/bin/activate")
        print()

        if not check_only:
            response = input("Continue without venv? (y/N): ").strip().lower()
            if response != "y":
                print("Exiting. Please activate venv and try again.")
                sys.exit(1)
        else:
            print("   (Skipping prompt in check-only mode)")
            print()

    # Ensure pip is available
    ensure_pip()
    print()

    # Try uv first (faster)
    repo_root = Path(__file__).parent.parent.parent
    if not check_only and install_uv_dependencies():
        print()
        print("=" * 70)
        print("✅ Dependencies installed successfully with uv!")
        print("=" * 70)
        return 0

    # Fall back to pip + requirements-dev.txt
    requirements_file = repo_root / "requirements-dev.txt"

    success = install_requirements(requirements_file, check_only=check_only)

    if success:
        # Verify installation
        print()
        print("🔍 Verifying critical dependencies...")
        critical_deps = ["aiohttp", "pytest", "ruff", "black", "pyyaml"]

        all_ok = True
        for dep in critical_deps:
            try:
                __import__(dep)
                print(f"   ✅ {dep}")
            except ImportError:
                print(f"   ❌ {dep} - NOT FOUND")
                all_ok = False

        print()
        print("=" * 70)

        if all_ok:
            print("✅ All dependencies installed and verified!")
            print()
            print("🚀 Next steps:")
            print("   make verify-all     # Run all checks")
            print("   make test           # Run tests")
            print("=" * 70)
            return 0
        else:
            print("⚠️  Some dependencies failed to install")
            print()
            print("💡 Try:")
            print(f"   pip install -r {requirements_file}")
            print("=" * 70)
            return 1
    else:
        print()
        print("=" * 70)
        print("❌ Installation failed")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
