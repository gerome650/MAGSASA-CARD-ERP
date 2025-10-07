"""
🧪 Tests for Governance Policy Loader

Tests all aspects of the policy enforcement system:
- Policy file loading and validation
- Coverage enforcement
- Test pass rate checking
- Linting enforcement
- Merge score calculation
- Branch protection
- Violation reporting
"""

import contextlib
import json
import tempfile
from pathlib import Path

import pytest
import yaml

from scripts.utils.policy_loader import (
    MergeScore,
    PolicyError,
    PolicyLoader,
    PolicyViolation,
)


@pytest.fixture
def sample_policy():
    """Sample policy configuration for testing."""
    return {
        "version": "1.0.0",
        "enforcement_mode": "strict",
        "fail_on_violation": True,
        "coverage": {"enabled": True, "minimum": 85, "warning": 90, "target": 95},
        "testing": {"enabled": True, "minimum_pass_rate": 100},
        "linting": {"enabled": True, "tools": {"ruff": {"max_violations": 0}}},
        "branch_protection": {
            "enabled": True,
            "protected_branches": ["main", "master"],
            "require_reviews": 1,
        },
        "merge_score": {
            "enabled": True,
            "passing_threshold": 80,
            "weights": {
                "coverage": 30,
                "tests_passing": 30,
                "linting": 20,
                "reviews": 15,
                "documentation": 5,
            },
            "components": {
                "coverage": {"max_score": 100, "calculation": "linear"},
                "tests_passing": {"max_score": 100, "calculation": "percentage"},
                "linting": {"max_score": 100, "penalty_per_violation": 5},
                "reviews": {"max_score": 100, "score_per_review": 50},
                "documentation": {
                    "max_score": 100,
                    "has_description": 50,
                    "has_changelog": 50,
                },
            },
        },
    }


@pytest.fixture
def temp_policy_file(sample_policy):
    """Create temporary policy file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        yaml.dump(sample_policy, f)
        path = Path(f.name)

    yield path

    # Cleanup
    path.unlink()


class TestPolicyLoader:
    """Tests for PolicyLoader class."""

    def test_load_policy_success(self, temp_policy_file):
        """Test successful policy loading."""
        loader = PolicyLoader(str(temp_policy_file))

        assert loader.policy is not None
        assert loader.policy["version"] == "1.0.0"
        assert loader.enforcement_mode == "strict"
        assert loader.fail_on_violation is True

    def test_load_policy_file_not_found(self):
        """Test error when policy file not found."""
        with pytest.raises(FileNotFoundError):
            PolicyLoader("nonexistent.yml")

    def test_load_policy_missing_required_fields(self):
        """Test error when required fields are missing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump({"version": "1.0.0"}, f)  # Missing required fields
            path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="Missing required field"):
                PolicyLoader(str(path))
        finally:
            path.unlink()

    def test_enforcement_mode_property(self, temp_policy_file):
        """Test enforcement_mode property."""
        loader = PolicyLoader(str(temp_policy_file))
        assert loader.enforcement_mode == "strict"

    def test_fail_on_violation_property(self, temp_policy_file):
        """Test fail_on_violation property."""
        loader = PolicyLoader(str(temp_policy_file))
        assert loader.fail_on_violation is True


class TestCoverageEnforcement:
    """Tests for coverage enforcement."""

    def test_coverage_above_minimum(self, temp_policy_file):
        """Test coverage above minimum threshold."""
        loader = PolicyLoader(str(temp_policy_file))
        loader.check_coverage(90.0)

        assert len(loader.violations) == 0

    def test_coverage_at_minimum(self, temp_policy_file):
        """Test coverage exactly at minimum threshold."""
        loader = PolicyLoader(str(temp_policy_file))
        loader.check_coverage(85.0)

        assert len(loader.violations) == 0

    def test_coverage_below_minimum(self, temp_policy_file):
        """Test coverage below minimum threshold."""
        loader = PolicyLoader(str(temp_policy_file))

        with pytest.raises(PolicyError):
            loader.check_coverage(80.0)

        assert len(loader.violations) == 1
        assert loader.violations[0].severity == "critical"
        assert loader.violations[0].rule == "coverage.minimum"

    def test_coverage_warning_threshold(self, temp_policy_file):
        """Test coverage below warning threshold."""
        loader = PolicyLoader(str(temp_policy_file))
        loader.check_coverage(87.0)  # Between minimum (85) and warning (90)

        assert len(loader.violations) == 1
        assert loader.violations[0].severity == "warning"
        assert loader.violations[0].rule == "coverage.warning"

    def test_coverage_disabled(self, temp_policy_file, sample_policy):
        """Test coverage check when disabled."""
        sample_policy["coverage"]["enabled"] = False

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(sample_policy, f)
            path = Path(f.name)

        try:
            loader = PolicyLoader(str(path))
            loader.check_coverage(50.0)  # Should not raise error
            assert len(loader.violations) == 0
        finally:
            path.unlink()


class TestTestPassRate:
    """Tests for test pass rate enforcement."""

    def test_all_tests_pass(self, temp_policy_file):
        """Test when all tests pass."""
        loader = PolicyLoader(str(temp_policy_file))
        loader.check_test_pass_rate(50, 50)

        assert len(loader.violations) == 0

    def test_some_tests_fail(self, temp_policy_file):
        """Test when some tests fail."""
        loader = PolicyLoader(str(temp_policy_file))

        with pytest.raises(PolicyError):
            loader.check_test_pass_rate(45, 50)

        assert len(loader.violations) == 1
        assert loader.violations[0].severity == "critical"
        assert loader.violations[0].rule == "testing.pass_rate"

    def test_no_tests(self, temp_policy_file):
        """Test when no tests exist."""
        loader = PolicyLoader(str(temp_policy_file))

        with pytest.raises(PolicyError):
            loader.check_test_pass_rate(0, 0)

        assert len(loader.violations) == 1
        assert loader.violations[0].rule == "testing.no_tests"


class TestLintingEnforcement:
    """Tests for linting enforcement."""

    def test_no_violations(self, temp_policy_file):
        """Test when no linting violations."""
        loader = PolicyLoader(str(temp_policy_file))
        loader.check_linting(0)

        assert len(loader.violations) == 0

    def test_with_violations(self, temp_policy_file):
        """Test when linting violations exist."""
        loader = PolicyLoader(str(temp_policy_file))

        with pytest.raises(PolicyError):
            loader.check_linting(5)

        assert len(loader.violations) == 1
        assert loader.violations[0].severity == "critical"
        assert loader.violations[0].rule == "linting.violations"


class TestMergeScore:
    """Tests for merge score calculation."""

    def test_perfect_score(self, temp_policy_file):
        """Test perfect merge score."""
        loader = PolicyLoader(str(temp_policy_file))

        score = loader.calculate_merge_score(
            coverage=95.0,
            tests_passed=50,
            tests_total=50,
            lint_violations=0,
            review_count=2,
            has_description=True,
        )

        assert score.total_score >= 95
        assert score.passing is True
        assert "coverage" in score.components
        assert "tests_passing" in score.components

    def test_failing_score(self, temp_policy_file):
        """Test failing merge score."""
        loader = PolicyLoader(str(temp_policy_file))

        score = loader.calculate_merge_score(
            coverage=70.0,
            tests_passed=40,
            tests_total=50,
            lint_violations=10,
            review_count=0,
            has_description=False,
        )

        assert score.total_score < 80
        assert score.passing is False

    def test_score_components(self, temp_policy_file):
        """Test individual score components."""
        loader = PolicyLoader(str(temp_policy_file))

        score = loader.calculate_merge_score(
            coverage=90.0,
            tests_passed=50,
            tests_total=50,
            lint_violations=2,
            review_count=1,
            has_description=True,
        )

        # Check components exist
        assert "coverage" in score.components
        assert "tests_passing" in score.components
        assert "linting" in score.components
        assert "reviews" in score.components
        assert "documentation" in score.components

        # Coverage should be high
        assert score.components["coverage"] >= 90

        # Tests should be 100%
        assert score.components["tests_passing"] == 100

        # Linting should have penalty
        assert score.components["linting"] == 90  # 100 - (2 * 5)

    def test_score_disabled(self, temp_policy_file, sample_policy):
        """Test score calculation when disabled."""
        sample_policy["merge_score"]["enabled"] = False

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(sample_policy, f)
            path = Path(f.name)

        try:
            loader = PolicyLoader(str(path))
            score = loader.calculate_merge_score(coverage=50.0)

            assert score.total_score == 100.0
            assert score.passing is True
            assert len(score.components) == 0
        finally:
            path.unlink()


class TestBranchProtection:
    """Tests for branch protection."""

    def test_protected_branch_with_reviews(self, temp_policy_file):
        """Test protected branch with required reviews."""
        loader = PolicyLoader(str(temp_policy_file))
        loader.check_branch_protection("main", has_reviews=True)

        assert len(loader.violations) == 0

    def test_protected_branch_without_reviews(self, temp_policy_file):
        """Test protected branch without required reviews."""
        loader = PolicyLoader(str(temp_policy_file))

        with pytest.raises(PolicyError):
            loader.check_branch_protection("main", has_reviews=False)

        assert len(loader.violations) == 1
        assert loader.violations[0].rule == "branch_protection.reviews"

    def test_unprotected_branch(self, temp_policy_file):
        """Test unprotected branch."""
        loader = PolicyLoader(str(temp_policy_file))
        loader.check_branch_protection("feature/test", has_reviews=False)

        assert len(loader.violations) == 0


class TestViolationReporting:
    """Tests for violation reporting."""

    def test_violations_summary_empty(self, temp_policy_file):
        """Test violations summary when no violations."""
        loader = PolicyLoader(str(temp_policy_file))
        summary = loader.get_violations_summary()

        assert "No policy violations" in summary

    def test_violations_summary_with_violations(self, temp_policy_file):
        """Test violations summary with violations."""
        loader = PolicyLoader(str(temp_policy_file))

        with contextlib.suppress(PolicyError):
            loader.check_coverage(80.0)

        summary = loader.get_violations_summary()

        assert "Policy Violations Found" in summary
        assert "CRITICAL" in summary

    def test_violations_json_export(self, temp_policy_file):
        """Test JSON export of violations."""
        loader = PolicyLoader(str(temp_policy_file))

        with contextlib.suppress(PolicyError):
            loader.check_coverage(80.0)

        json_str = loader.export_violations_json()
        violations = json.loads(json_str)

        assert len(violations) == 1
        assert violations[0]["rule"] == "coverage.minimum"
        assert violations[0]["severity"] == "critical"


class TestPolicyViolation:
    """Tests for PolicyViolation dataclass."""

    def test_violation_str(self):
        """Test string representation of violation."""
        violation = PolicyViolation(
            rule="test.rule",
            severity="critical",
            message="Test message",
            actual="50%",
            expected=">=85%",
        )

        str_repr = str(violation)

        assert "CRITICAL" in str_repr
        assert "test.rule" in str_repr
        assert "Test message" in str_repr
        assert "50%" in str_repr
        assert ">=85%" in str_repr


class TestMergeScoreDataclass:
    """Tests for MergeScore dataclass."""

    def test_merge_score_str_pass(self):
        """Test string representation of passing score."""
        score = MergeScore(
            total_score=85.0, passing=True, threshold=80.0, components={}, violations=[]
        )

        str_repr = str(score)

        assert "85.0" in str_repr
        assert "PASS" in str_repr
        assert "80" in str_repr

    def test_merge_score_str_fail(self):
        """Test string representation of failing score."""
        score = MergeScore(
            total_score=75.0,
            passing=False,
            threshold=80.0,
            components={},
            violations=[],
        )

        str_repr = str(score)

        assert "75.0" in str_repr
        assert "FAIL" in str_repr


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_full_quality_check_pass(self, temp_policy_file):
        """Test full quality check that passes."""
        loader = PolicyLoader(str(temp_policy_file))

        # Run all checks
        loader.check_coverage(90.0)
        loader.check_test_pass_rate(50, 50)
        loader.check_linting(0)
        loader.check_branch_protection("main", has_reviews=True)

        score = loader.calculate_merge_score(
            coverage=90.0,
            tests_passed=50,
            tests_total=50,
            lint_violations=0,
            review_count=1,
            has_description=True,
        )

        assert len(loader.violations) == 0
        assert score.passing is True

    def test_full_quality_check_fail(self, temp_policy_file):
        """Test full quality check that fails."""
        loader = PolicyLoader(str(temp_policy_file))

        # Run checks (some will fail)
        with contextlib.suppress(PolicyError):
            loader.check_coverage(80.0)

        with contextlib.suppress(PolicyError):
            loader.check_test_pass_rate(45, 50)

        with contextlib.suppress(PolicyError):
            loader.check_linting(5)

        score = loader.calculate_merge_score(
            coverage=80.0,
            tests_passed=45,
            tests_total=50,
            lint_violations=5,
            review_count=0,
            has_description=False,
        )

        assert len(loader.violations) > 0
        assert score.passing is False

        # Check violations summary
        summary = loader.get_violations_summary()
        assert "CRITICAL" in summary
