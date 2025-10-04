#!/usr/bin/env python3
"""
Observability CI Gate - Enforces observability best practices in PRs.

This script checks if code changes include proper observability instrumentation:
- Metrics tracking (metrics_client, Counter, Histogram, etc.)
- Distributed tracing (start_as_current_span, tracer)
- Structured logging (logger.info, logger.error, etc.)

Usage:
    python scripts/check_observability_hooks.py
    python scripts/check_observability_hooks.py --strict  # Fail on any missing hook

Exit codes:
    0: All checks passed or observability hooks found
    1: No observability hooks found (OBSERVABILITY_MISSING)
    2: Script execution error
"""

import os
import sys
import re
import subprocess
import argparse
from typing import List, Tuple, Dict


# Observability hook patterns to search for
OBSERVABILITY_PATTERNS = {
    'metrics': [
        r'metrics_client',
        r'Counter\(',
        r'Histogram\(',
        r'Gauge\(',
        r'Summary\(',
        r'\.inc\(\)',
        r'\.observe\(\)',
        r'track_function_metrics',
    ],
    'tracing': [
        r'start_as_current_span',
        r'get_tracer\(',
        r'add_span_attributes',
        r'add_span_event',
        r'tracer\.start_span',
        r'@trace',
    ],
    'logging': [
        r'logger\.info',
        r'logger\.debug',
        r'logger\.warning',
        r'logger\.error',
        r'logger\.critical',
        r'get_logger\(',
        r'StructuredLogger',
    ]
}

# Files to ignore (config, tests, migrations, etc.)
IGNORE_PATTERNS = [
    r'test_.*\.py$',
    r'.*_test\.py$',
    r'/tests?/',
    r'/migrations/',
    r'setup\.py$',
    r'__init__\.py$',
    r'conftest\.py$',
    r'\.md$',
    r'\.txt$',
    r'\.yml$',
    r'\.yaml$',
    r'\.json$',
    r'requirements.*\.txt$',
]


def should_ignore_file(filepath: str) -> bool:
    """
    Check if a file should be ignored from observability checks.
    
    Args:
        filepath: Path to the file
    
    Returns:
        True if file should be ignored, False otherwise
    """
    for pattern in IGNORE_PATTERNS:
        if re.search(pattern, filepath):
            return True
    return False


def get_git_diff() -> str:
    """
    Get the git diff for the current changes.
    
    Returns:
        Git diff output as string
    """
    try:
        # Try to get diff from HEAD (for CI environments)
        result = subprocess.run(
            ['git', 'diff', 'HEAD^', 'HEAD'],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0 or not result.stdout.strip():
            # Fallback: get diff of staged changes
            result = subprocess.run(
                ['git', 'diff', '--cached'],
                capture_output=True,
                text=True,
                check=False
            )
        
        if result.returncode != 0 or not result.stdout.strip():
            # Fallback: get diff of unstaged changes
            result = subprocess.run(
                ['git', 'diff'],
                capture_output=True,
                text=True,
                check=False
            )
        
        return result.stdout
    except Exception as e:
        print(f"⚠️  Warning: Could not get git diff: {e}")
        return ""


def get_changed_files() -> List[str]:
    """
    Get list of Python files changed in the current commit/PR.
    
    Returns:
        List of changed Python file paths
    """
    try:
        # Try to get changed files from HEAD
        result = subprocess.run(
            ['git', 'diff', '--name-only', 'HEAD^', 'HEAD'],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0 or not result.stdout.strip():
            # Fallback: get staged files
            result = subprocess.run(
                ['git', 'diff', '--name-only', '--cached'],
                capture_output=True,
                text=True,
                check=False
            )
        
        if result.returncode != 0 or not result.stdout.strip():
            # Fallback: get unstaged files
            result = subprocess.run(
                ['git', 'diff', '--name-only'],
                capture_output=True,
                text=True,
                check=False
            )
        
        files = result.stdout.strip().split('\n')
        python_files = [
            f for f in files 
            if f.endswith('.py') and not should_ignore_file(f) and os.path.exists(f)
        ]
        
        return python_files
    except Exception as e:
        print(f"⚠️  Warning: Could not get changed files: {e}")
        return []


def check_file_for_hooks(filepath: str) -> Dict[str, List[str]]:
    """
    Check a file for observability hooks.
    
    Args:
        filepath: Path to the file to check
    
    Returns:
        Dictionary of found hooks by category
    """
    found_hooks = {
        'metrics': [],
        'tracing': [],
        'logging': []
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for category, patterns in OBSERVABILITY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, content):
                    found_hooks[category].append(pattern)
        
    except Exception as e:
        print(f"⚠️  Warning: Could not read file {filepath}: {e}")
    
    return found_hooks


def check_diff_for_hooks(diff: str) -> Dict[str, List[str]]:
    """
    Check git diff for observability hooks.
    
    Args:
        diff: Git diff output
    
    Returns:
        Dictionary of found hooks by category
    """
    found_hooks = {
        'metrics': [],
        'tracing': [],
        'logging': []
    }
    
    # Only check added lines (starting with +)
    added_lines = [line for line in diff.split('\n') if line.startswith('+')]
    diff_content = '\n'.join(added_lines)
    
    for category, patterns in OBSERVABILITY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, diff_content):
                found_hooks[category].append(pattern)
    
    return found_hooks


def print_results(
    changed_files: List[str],
    hooks_found: Dict[str, List[str]],
    strict: bool = False
) -> bool:
    """
    Print results of observability check.
    
    Args:
        changed_files: List of changed Python files
        hooks_found: Dictionary of found hooks by category
        strict: Whether to enforce strict mode
    
    Returns:
        True if checks passed, False otherwise
    """
    print("\n" + "="*70)
    print("🔍 OBSERVABILITY CI GATE REPORT")
    print("="*70 + "\n")
    
    if not changed_files:
        print("ℹ️  No Python files changed in this commit/PR")
        print("✅ Observability check: SKIPPED (no Python changes)\n")
        return True
    
    print(f"📝 Changed Python files ({len(changed_files)}):")
    for filepath in changed_files[:10]:  # Show max 10 files
        print(f"   - {filepath}")
    if len(changed_files) > 10:
        print(f"   ... and {len(changed_files) - 10} more")
    print()
    
    # Check what hooks were found
    has_metrics = len(hooks_found['metrics']) > 0
    has_tracing = len(hooks_found['tracing']) > 0
    has_logging = len(hooks_found['logging']) > 0
    has_any_hooks = has_metrics or has_tracing or has_logging
    
    print("🎯 Observability Hooks Found:")
    print(f"   {'✅' if has_metrics else '❌'} Metrics:  {len(hooks_found['metrics'])} patterns")
    print(f"   {'✅' if has_tracing else '❌'} Tracing:  {len(hooks_found['tracing'])} patterns")
    print(f"   {'✅' if has_logging else '❌'} Logging:  {len(hooks_found['logging'])} patterns")
    print()
    
    if has_any_hooks:
        print("📊 Details:")
        for category, patterns in hooks_found.items():
            if patterns:
                print(f"\n   {category.upper()}:")
                unique_patterns = list(set(patterns))
                for pattern in unique_patterns[:5]:  # Show max 5 patterns
                    print(f"      - {pattern}")
                if len(unique_patterns) > 5:
                    print(f"      ... and {len(unique_patterns) - 5} more")
        print()
    
    # Determine pass/fail
    if not has_any_hooks:
        print("❌ OBSERVABILITY_MISSING")
        print("\n⚠️  No observability hooks found in this PR!")
        print("\nPlease ensure your changes include:")
        print("   • Metrics tracking (metrics_client, Counter, Histogram)")
        print("   • Distributed tracing (start_as_current_span)")
        print("   • Structured logging (logger.info, logger.error)")
        print("\nSee observability/README.md for guidelines.\n")
        return False
    
    if strict and not (has_metrics and has_tracing and has_logging):
        print("❌ STRICT MODE: Missing some observability categories")
        print("\n⚠️  Strict mode requires ALL three categories:")
        print(f"   {'✅' if has_metrics else '❌'} Metrics")
        print(f"   {'✅' if has_tracing else '❌'} Tracing")
        print(f"   {'✅' if has_logging else '❌'} Logging")
        print("\nSee observability/README.md for guidelines.\n")
        return False
    
    print("✅ OBSERVABILITY CHECK PASSED")
    print("\n🎉 Great job! Your changes include observability instrumentation.\n")
    return True


def main():
    """Main entry point for the observability check script."""
    parser = argparse.ArgumentParser(
        description="Check PR changes for observability hooks"
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Require all three observability categories (metrics, tracing, logging)'
    )
    parser.add_argument(
        '--files',
        nargs='+',
        help='Specific files to check (instead of git diff)'
    )
    args = parser.parse_args()
    
    try:
        # Get changed files
        if args.files:
            changed_files = [f for f in args.files if f.endswith('.py') and not should_ignore_file(f)]
        else:
            changed_files = get_changed_files()
        
        # Check for observability hooks
        hooks_found = {
            'metrics': [],
            'tracing': [],
            'logging': []
        }
        
        # Method 1: Check diff for hooks
        if not args.files:
            diff = get_git_diff()
            if diff:
                diff_hooks = check_diff_for_hooks(diff)
                for category in hooks_found:
                    hooks_found[category].extend(diff_hooks[category])
        
        # Method 2: Check individual files
        for filepath in changed_files:
            file_hooks = check_file_for_hooks(filepath)
            for category in hooks_found:
                hooks_found[category].extend(file_hooks[category])
        
        # Print results and determine exit code
        passed = print_results(changed_files, hooks_found, args.strict)
        
        sys.exit(0 if passed else 1)
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == '__main__':
    main()

