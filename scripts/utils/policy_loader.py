#!/usr/bin/env python3
"""
🛡️ Governance Policy Loader & Enforcer (Production-Hardened)

Loads merge_policy.yml and enforces quality gates for:
- Code coverage thresholds
- Linting and formatting rules
- Test pass rates
- Branch protection policies
- PR metadata requirements
- Merge readiness scoring
- Schema validation and integrity checks

Usage:
    python scripts/utils/policy_loader.py
    python scripts/utils/policy_loader.py --check-coverage 87.5
    python scripts/utils/policy_loader.py --check-all --coverage 87.5 --tests-passed 50 --tests-total 50
    python scripts/utils/policy_loader.py --validate --verbose
    python scripts/utils/policy_loader.py --json
"""

import argparse
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class PolicyError(Exception):
    """Raised when a policy violation occurs in strict mode."""

    pass


@dataclass
class PolicyViolation:
    """Represents a single policy violation."""

    rule: str
    severity: str  # critical, warning, info
    message: str
    actual: Any
    expected: Any

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.rule}: {self.message} (expected: {self.expected}, actual: {self.actual})"


@dataclass
class MergeScore:
    """Merge readiness score calculation."""

    total_score: float
    passing: bool
    threshold: float
    components: dict[str, float]
    violations: list[PolicyViolation]

    def __str__(self) -> str:
        status = "✅ PASS" if self.passing else "❌ FAIL"
        return f"Merge Score: {self.total_score:.1f}/{100} ({status}, threshold: {self.threshold})"


class PolicyLoader:
    """Load and enforce governance policies from merge_policy.yml with schema validation."""

    DEFAULT_POLICY_PATH = "merge_policy.yml"

    # Policy schema for validation
    POLICY_SCHEMA = {
        "version": str,
        "enforcement_mode": str,
        "fail_on_violation": bool,
        "coverage": {
            "enabled": bool,
            "minimum": (int, float),
            "warning": (int, float),
            "target": (int, float),
            "dev_mode": bool,
            "measurement": str,
            "exclude_patterns": list,
            "report_formats": list,
            "trend_tracking": {"enabled": bool, "history_size": int, "sparkline": bool},
        },
        "testing": {
            "enabled": bool,
            "minimum_pass_rate": (int, float),
            "required_test_types": list,
        },
        "linting": {"enabled": bool, "tools": dict, "auto_fix": bool},
        "merge_score": {
            "enabled": bool,
            "passing_threshold": (int, float),
            "weights": dict,
            "components": dict,
        },
    }

    def __init__(self, policy_path: str | None = None, verbose: bool = False):
        """Initialize policy loader.

        Args:
            policy_path: Path to merge_policy.yml (defaults to repo root)
            verbose: Whether to enable verbose logging
        """
        self.policy_path = Path(policy_path or self.DEFAULT_POLICY_PATH)
        self.policy: dict[str, Any] = {}
        self.violations: list[PolicyViolation] = []
        self.verbose = verbose
        self._load_policy()

    def _load_policy(self) -> None:
        """Load and validate policy file with schema validation."""
        if not self.policy_path.exists():
            raise FileNotFoundError(f"Policy file not found: {self.policy_path}")

        try:
            with open(self.policy_path) as f:
                self.policy = yaml.safe_load(f)

            if self.verbose:
                logger.info(f"Loaded policy from: {self.policy_path}")

            # Validate schema
            self._validate_schema()

            # Validate required fields
            self._validate_required_fields()

            if self.verbose:
                logger.info("Policy validation completed successfully")

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in policy file: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load policy: {e}")

    def _validate_schema(self) -> None:
        """Validate policy against schema."""

        def validate_section(data: Any, schema: Any, path: str = "") -> list[str]:
            errors = []

            if isinstance(schema, dict):
                if not isinstance(data, dict):
                    errors.append(f"{path}: Expected dict, got {type(data).__name__}")
                    return errors

                for key, expected_type in schema.items():
                    if key not in data:
                        continue  # Optional fields

                    field_path = f"{path}.{key}" if path else key
                    errors.extend(
                        validate_section(data[key], expected_type, field_path)
                    )

            elif isinstance(schema, tuple):
                # Multiple allowed types
                if not any(isinstance(data, t) for t in schema):
                    type_names = [t.__name__ for t in schema]
                    errors.append(
                        f"{path}: Expected one of {type_names}, got {type(data).__name__}"
                    )

            elif isinstance(schema, type):
                if not isinstance(data, schema):
                    errors.append(
                        f"{path}: Expected {schema.__name__}, got {type(data).__name__}"
                    )

            return errors

        schema_errors = validate_section(self.policy, self.POLICY_SCHEMA)
        if schema_errors:
            raise ValueError(
                "Policy schema validation failed:\n" + "\n".join(schema_errors)
            )

    def _validate_required_fields(self) -> None:
        """Validate that required fields are present."""
        required_fields = ["version", "enforcement_mode", "coverage", "testing"]
        missing_fields = []

        for field in required_fields:
            if field not in self.policy:
                missing_fields.append(field)

        if missing_fields:
            raise ValueError(
                f"Missing required fields in policy: {', '.join(missing_fields)}"
            )

        # Validate coverage section
        coverage = self.policy.get("coverage", {})
        if not isinstance(coverage.get("minimum"), int | float):
            raise ValueError("Coverage minimum must be a number")

        if coverage.get("minimum", 0) < 0 or coverage.get("minimum", 0) > 100:
            raise ValueError("Coverage minimum must be between 0 and 100")

        # Validate enforcement mode
        valid_modes = ["strict", "warn", "disabled"]
        if self.policy.get("enforcement_mode") not in valid_modes:
            raise ValueError(f"Invalid enforcement_mode. Must be one of: {valid_modes}")

    @property
    def enforcement_mode(self) -> str:
        """Get enforcement mode: strict, warn, or disabled."""
        return self.policy.get("enforcement_mode", "warn")

    @property
    def fail_on_violation(self) -> bool:
        """Whether to fail on policy violations."""
        return self.policy.get("fail_on_violation", False)

    def is_dev_mode_enabled(self) -> bool:
        """Check if development mode is enabled for coverage enforcement.

        Returns:
            True if dev_mode is enabled in coverage policy, False otherwise
        """
        return self.policy.get("coverage", {}).get("dev_mode", False)

    def check_coverage(self, actual_coverage: float) -> None:
        """Check if coverage meets minimum threshold.

        Args:
            actual_coverage: Actual coverage percentage (0-100)

        Raises:
            PolicyError: If coverage is below minimum in strict mode
        """
        if not self.policy.get("coverage", {}).get("enabled", True):
            return

        minimum = self.policy["coverage"]["minimum"]
        warning = self.policy["coverage"].get("warning", minimum)
        self.policy["coverage"].get("target", 100)

        if actual_coverage < minimum:
            violation = PolicyViolation(
                rule="coverage.minimum",
                severity="critical",
                message="Coverage below minimum threshold",
                actual=f"{actual_coverage:.1f}%",
                expected=f">= {minimum}%",
            )
            self.violations.append(violation)

            if self.fail_on_violation:
                raise PolicyError(str(violation))

        elif actual_coverage < warning:
            violation = PolicyViolation(
                rule="coverage.warning",
                severity="warning",
                message="Coverage below warning threshold",
                actual=f"{actual_coverage:.1f}%",
                expected=f">= {warning}%",
            )
            self.violations.append(violation)

    def check_test_pass_rate(self, passed: int, total: int) -> None:
        """Check if test pass rate meets minimum.

        Args:
            passed: Number of tests passed
            total: Total number of tests

        Raises:
            PolicyError: If pass rate is below minimum in strict mode
        """
        if not self.policy.get("testing", {}).get("enabled", True):
            return

        if total == 0:
            violation = PolicyViolation(
                rule="testing.no_tests",
                severity="critical",
                message="No tests found",
                actual=0,
                expected="> 0",
            )
            self.violations.append(violation)

            if self.fail_on_violation:
                raise PolicyError(str(violation))
            return

        pass_rate = (passed / total) * 100
        minimum_pass_rate = self.policy["testing"].get("minimum_pass_rate", 100)

        if pass_rate < minimum_pass_rate:
            violation = PolicyViolation(
                rule="testing.pass_rate",
                severity="critical",
                message="Test pass rate below minimum",
                actual=f"{pass_rate:.1f}% ({passed}/{total})",
                expected=f">= {minimum_pass_rate}%",
            )
            self.violations.append(violation)

            if self.fail_on_violation:
                raise PolicyError(str(violation))

    def check_linting(self, violation_count: int) -> None:
        """Check if linting violations are within acceptable range.

        Args:
            violation_count: Number of linting violations

        Raises:
            PolicyError: If violations exceed maximum in strict mode
        """
        if not self.policy.get("linting", {}).get("enabled", True):
            return

        max_violations = (
            self.policy["linting"]["tools"].get("ruff", {}).get("max_violations", 0)
        )

        if violation_count > max_violations:
            violation = PolicyViolation(
                rule="linting.violations",
                severity="critical",
                message="Linting violations exceed maximum",
                actual=violation_count,
                expected=f"<= {max_violations}",
            )
            self.violations.append(violation)

            if self.fail_on_violation:
                raise PolicyError(str(violation))

    def calculate_merge_score(
        self,
        coverage: float | None = None,
        tests_passed: int | None = None,
        tests_total: int | None = None,
        lint_violations: int | None = None,
        review_count: int | None = None,
        has_description: bool = True,
    ) -> MergeScore:
        """Calculate merge readiness score.

        Args:
            coverage: Coverage percentage (0-100)
            tests_passed: Number of tests passed
            tests_total: Total number of tests
            lint_violations: Number of linting violations
            review_count: Number of reviews
            has_description: Whether PR has description

        Returns:
            MergeScore with total score and component breakdown
        """
        if not self.policy.get("merge_score", {}).get("enabled", False):
            return MergeScore(
                total_score=100.0,
                passing=True,
                threshold=0,
                components={},
                violations=self.violations,
            )

        config = self.policy["merge_score"]
        weights = config["weights"]
        components_config = config["components"]
        threshold = config["passing_threshold"]

        components = {}
        total_score = 0.0

        # Coverage score
        if coverage is not None:
            target = self.policy["coverage"].get("target", 95)
            coverage_score = min((coverage / target) * 100, 100)
            components["coverage"] = coverage_score
            total_score += (coverage_score * weights["coverage"]) / 100

        # Tests passing score
        if tests_passed is not None and tests_total is not None:
            test_score = tests_passed / tests_total * 100 if tests_total > 0 else 0
            components["tests_passing"] = test_score
            total_score += (test_score * weights["tests_passing"]) / 100

        # Linting score
        if lint_violations is not None:
            penalty = components_config["linting"]["penalty_per_violation"]
            lint_score = max(100 - (lint_violations * penalty), 0)
            components["linting"] = lint_score
            total_score += (lint_score * weights["linting"]) / 100

        # Reviews score
        if review_count is not None:
            score_per_review = components_config["reviews"]["score_per_review"]
            review_score = min(review_count * score_per_review, 100)
            components["reviews"] = review_score
            total_score += (review_score * weights["reviews"]) / 100

        # Documentation score
        doc_score = 50 if has_description else 0
        components["documentation"] = doc_score
        total_score += (doc_score * weights["documentation"]) / 100

        passing = total_score >= threshold

        return MergeScore(
            total_score=total_score,
            passing=passing,
            threshold=threshold,
            components=components,
            violations=self.violations,
        )

    def check_branch_protection(self, branch: str, has_reviews: bool = False) -> None:
        """Check branch protection policies.

        Args:
            branch: Branch name
            has_reviews: Whether PR has required reviews

        Raises:
            PolicyError: If branch protection violated in strict mode
        """
        if not self.policy.get("branch_protection", {}).get("enabled", False):
            return

        config = self.policy["branch_protection"]
        protected = config.get("protected_branches", [])

        if (
            branch in protected
            and config.get("require_reviews", 0) > 0
            and not has_reviews
        ):
            violation = PolicyViolation(
                rule="branch_protection.reviews",
                severity="critical",
                message=f"Protected branch {branch} requires reviews",
                actual="no reviews",
                expected=f">= {config['require_reviews']} reviews",
            )
            self.violations.append(violation)

            if self.fail_on_violation:
                raise PolicyError(str(violation))

    def get_violations_summary(self) -> str:
        """Get formatted summary of all violations."""
        if not self.violations:
            return "✅ No policy violations found"

        lines = ["❌ Policy Violations Found:", ""]

        critical = [v for v in self.violations if v.severity == "critical"]
        warnings = [v for v in self.violations if v.severity == "warning"]

        if critical:
            lines.append("🚨 CRITICAL:")
            for v in critical:
                lines.append(f"  - {v}")
            lines.append("")

        if warnings:
            lines.append("⚠️  WARNINGS:")
            for v in warnings:
                lines.append(f"  - {v}")
            lines.append("")

        return "\n".join(lines)

    def export_violations_json(self) -> str:
        """Export violations as JSON."""
        return json.dumps(
            [
                {
                    "rule": v.rule,
                    "severity": v.severity,
                    "message": v.message,
                    "actual": str(v.actual),
                    "expected": str(v.expected),
                }
                for v in self.violations
            ],
            indent=2,
        )

    def validate_policy(self) -> dict[str, Any]:
        """Validate policy configuration and return validation report.

        Returns:
            Dictionary with validation results
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "sections_checked": [],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        try:
            # Check if policy loaded successfully
            if not self.policy:
                validation_result["valid"] = False
                validation_result["errors"].append("Policy not loaded")
                return validation_result

            validation_result["sections_checked"].append("policy_load")

            # Check coverage configuration
            coverage = self.policy.get("coverage", {})
            if coverage.get("enabled", True):
                if coverage.get("minimum", 0) < 50:
                    validation_result["warnings"].append("Coverage minimum below 50%")

                if coverage.get("target", 100) < coverage.get("minimum", 0):
                    validation_result["errors"].append("Coverage target below minimum")
                    validation_result["valid"] = False

                validation_result["sections_checked"].append("coverage")

            # Check testing configuration
            testing = self.policy.get("testing", {})
            if testing.get("enabled", True):
                pass_rate = testing.get("minimum_pass_rate", 100)
                if pass_rate < 80:
                    validation_result["warnings"].append("Test pass rate below 80%")

                validation_result["sections_checked"].append("testing")

            # Check merge score configuration
            merge_score = self.policy.get("merge_score", {})
            if merge_score.get("enabled", False):
                weights = merge_score.get("weights", {})
                total_weight = sum(weights.values())
                if abs(total_weight - 100) > 0.1:
                    validation_result["errors"].append(
                        f"Merge score weights sum to {total_weight}, should be 100"
                    )
                    validation_result["valid"] = False

                validation_result["sections_checked"].append("merge_score")

            # Check enforcement mode
            enforcement_mode = self.policy.get("enforcement_mode", "warn")
            if enforcement_mode not in ["strict", "warn", "disabled"]:
                validation_result["errors"].append(
                    f"Invalid enforcement_mode: {enforcement_mode}"
                )
                validation_result["valid"] = False

            validation_result["sections_checked"].append("enforcement_mode")

        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Validation error: {e}")

        return validation_result


def main():
    """Enhanced CLI entry point with validation and structured reporting."""
    parser = argparse.ArgumentParser(
        description="Governance policy loader and enforcer"
    )
    parser.add_argument("--policy", type=str, help="Path to merge_policy.yml")
    parser.add_argument("--check-coverage", type=float, help="Check coverage threshold")
    parser.add_argument(
        "--check-tests", action="store_true", help="Check test pass rate"
    )
    parser.add_argument("--tests-passed", type=int, help="Number of tests passed")
    parser.add_argument("--tests-total", type=int, help="Total number of tests")
    parser.add_argument(
        "--check-lint", action="store_true", help="Check linting violations"
    )
    parser.add_argument("--lint-violations", type=int, help="Number of lint violations")
    parser.add_argument("--check-all", action="store_true", help="Run all checks")
    parser.add_argument(
        "--calculate-score", action="store_true", help="Calculate merge score"
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validate policy configuration"
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()
    start_time = time.time()

    try:
        # Load policy with verbose logging if requested
        policy = PolicyLoader(args.policy, verbose=args.verbose)

        if not args.json:
            print(f"✅ Loaded policy from: {policy.policy_path}")
            print(f"📋 Enforcement mode: {policy.enforcement_mode}")
            print(f"🎯 Fail on violation: {policy.fail_on_violation}")
            print()

        # Run validation if requested
        if args.validate:
            if args.verbose:
                logger.info("Validating policy configuration...")

            validation_result = policy.validate_policy()

            if args.json:
                print(json.dumps(validation_result, indent=2))
            else:
                print("🔍 Policy Validation Results:")
                print(
                    f"   Status: {'✅ Valid' if validation_result['valid'] else '❌ Invalid'}"
                )

                if validation_result["errors"]:
                    print("   Errors:")
                    for error in validation_result["errors"]:
                        print(f"     - {error}")

                if validation_result["warnings"]:
                    print("   Warnings:")
                    for warning in validation_result["warnings"]:
                        print(f"     - {warning}")

                print(
                    f"   Sections checked: {', '.join(validation_result['sections_checked'])}"
                )
                print()

            if not validation_result["valid"]:
                sys.exit(1)

        # Run checks based on arguments
        if args.check_coverage is not None or args.check_all:
            coverage = args.check_coverage or float(os.getenv("COVERAGE", "0"))
            if not args.json:
                print(f"📊 Checking coverage: {coverage:.1f}%")
            policy.check_coverage(coverage)

        if args.check_tests or args.check_all:
            passed = args.tests_passed or int(os.getenv("TESTS_PASSED", "0"))
            total = args.tests_total or int(os.getenv("TESTS_TOTAL", "0"))
            if not args.json:
                print(f"🧪 Checking tests: {passed}/{total}")
            policy.check_test_pass_rate(passed, total)

        if args.check_lint or args.check_all:
            violations = args.lint_violations or int(os.getenv("LINT_VIOLATIONS", "0"))
            if not args.json:
                print(f"🧹 Checking linting: {violations} violations")
            policy.check_linting(violations)

        if args.calculate_score or args.check_all:
            coverage = args.check_coverage or float(os.getenv("COVERAGE", "0"))
            passed = args.tests_passed or int(os.getenv("TESTS_PASSED", "0"))
            total = args.tests_total or int(os.getenv("TESTS_TOTAL", "0"))
            violations = args.lint_violations or int(os.getenv("LINT_VIOLATIONS", "0"))

            score = policy.calculate_merge_score(
                coverage=coverage,
                tests_passed=passed,
                tests_total=total,
                lint_violations=violations,
                review_count=1,
                has_description=True,
            )

            if not args.json:
                print()
                print(f"🎯 {score}")
                print("   Components:")
                for component, value in score.components.items():
                    print(f"     - {component}: {value:.1f}")

        if not args.json:
            print()

        # Output violations
        if args.json:
            output = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration": time.time() - start_time,
                "policy_path": str(policy.policy_path),
                "enforcement_mode": policy.enforcement_mode,
                "fail_on_violation": policy.fail_on_violation,
                "violations": [
                    {
                        "rule": v.rule,
                        "severity": v.severity,
                        "message": v.message,
                        "actual": str(v.actual),
                        "expected": str(v.expected),
                    }
                    for v in policy.violations
                ],
            }
            print(json.dumps(output, indent=2))
        else:
            print(policy.get_violations_summary())

        # Exit with appropriate code
        if policy.violations and policy.fail_on_violation:
            critical_violations = [
                v for v in policy.violations if v.severity == "critical"
            ]
            if critical_violations:
                sys.exit(1)

        sys.exit(0)

    except PolicyError as e:
        error_msg = f"Policy Error: {e}"
        logger.error(error_msg)
        if not args.json:
            print(f"❌ {error_msg}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        error_msg = f"Error: {e}"
        logger.error(error_msg)
        if args.verbose:
            import traceback

            traceback.print_exc()
        if not args.json:
            print(f"❌ {error_msg}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
