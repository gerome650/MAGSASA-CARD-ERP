"""
🚫 Regression Guard — Prevent common Python anti-patterns from reappearing

This test ensures that common lint issues don't make it back into the codebase.
It fails CI if any of the specified bad patterns are detected.
"""

import subprocess

import pytest

# Bad patterns to prevent from reappearing
BAD_PATTERNS = [
    "F821",  # undefined name
    "F841",  # unused variable
    "B007",  # unused loop variable
    "SIM117",  # nested with statements
    "SIM105",  # try/except pass
    "SIM222",  # "... or True" expressions
]


@pytest.mark.order(-1)  # Run this test last (after all others)
@pytest.mark.regression
def test_no_common_issues():
    """✅ Ensure none of the common bad patterns are present."""
    cmd = ["ruff", "check", ".", "--select", ",".join(BAD_PATTERNS)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        print("\n" + result.stdout)

    assert result.returncode == 0, (
        "❌ Regression guard failed — fix lint errors above.\n"
        f"Found violations of: {', '.join(BAD_PATTERNS)}"
    )
