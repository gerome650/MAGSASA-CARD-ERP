#!/usr/bin/env python3
"""
CI Preflight Validation Script
Runs comprehensive checks before pushing code to ensure CI safety.
"""
import os
import subprocess
import sys
from typing import List, Tuple

# Configure environment
os.environ["PYTHONUNBUFFERED"] = "1"
# Add uv to PATH if not already there
if "/Users/palawan/.local/bin" not in os.environ.get("PATH", ""):
    os.environ["PATH"] = "/Users/palawan/.local/bin:" + os.environ.get("PATH", "")

def run_command(name: str, cmd: List[str], description: str = "") -> Tuple[str, bool]:
    """
    Run a command and return the result.
    
    Args:
        name: Display name for the check
        cmd: Command to run as list of strings
        description: Optional description of what the command does
        
    Returns:
        Tuple of (name, success_boolean)
    """
    print(f"🚀 {name}...")
    if description:
        print(f"   {description}")
    
    try:
        result = subprocess.run(
            cmd, 
            check=True, 
            capture_output=False,  # Let output show in real-time
            text=True
        )
        print(f"   ✅ {name} completed successfully")
        return (name, True)
    except subprocess.CalledProcessError as e:
        print(f"   ❌ {name} failed with exit code {e.returncode}")
        return (name, False)
    except FileNotFoundError:
        print(f"   ❌ {name} failed: command not found")
        return (name, False)

def main():
    """Run all CI preflight checks."""
    print("🔎 Running full CI Preflight Validation...")
    print("=" * 50)
    
    # Define checks in order
    checks = [
        ("Linting", ["uv", "run", "ruff", "check", "."], "Check code style with ruff"),
        ("Black Format", ["uv", "run", "black", "--check", "."], "Check code formatting"),
        ("Type Check", ["uv", "run", "mypy", "."], "Check type annotations"),
        ("Unit Tests", ["uv", "run", "pytest", "--maxfail=1", "--disable-warnings", "-q"], "Run unit tests"),
        ("MCP Validation", ["make", "mcp-check"], "Validate MCP setup"),
        ("Agent Trace", ["make", "agent-run-all"], "Run agent orchestration"),
        ("Build", ["uv", "build"], "Build all packages"),
    ]
    
    results = []
    
    # Run each check
    for name, cmd, description in checks:
        result = run_command(name, cmd, description)
        results.append(result)
        print()  # Add spacing between checks
    
    # Print summary
    print("📊 CI Preflight Results Summary")
    print("=" * 50)
    
    failed_checks = []
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name:<18} {status}")
        if not success:
            failed_checks.append(name)
    
    print("=" * 50)
    
    if failed_checks:
        print(f"🚨 {len(failed_checks)} check(s) failed: {', '.join(failed_checks)}")
        print("💡 Please fix the issues above before pushing.")
        print("🔧 Run individual commands to debug specific failures.")
        sys.exit(1)
    else:
        print("🎉 All checks passed! Safe to push 🚀")
        print("✨ Your code is ready for CI/CD pipeline.")
        sys.exit(0)

if __name__ == "__main__":
    main()

