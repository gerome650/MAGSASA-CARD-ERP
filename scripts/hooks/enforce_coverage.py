#!/usr/bin/env python3
"""
📊 Coverage Enforcement Hook (Production-Hardened)

Parses coverage reports and enforces minimum thresholds from merge_policy.yml.
Exits with non-zero status if coverage is below minimum.
Enhanced with structured logging, error tolerance, and CI-safe behavior.

Supports development mode for local flexibility while maintaining strict CI enforcement.

Usage:
    python scripts/hooks/enforce_coverage.py
    python scripts/hooks/enforce_coverage.py --coverage-file coverage.json
    python scripts/hooks/enforce_coverage.py --format xml --coverage-file coverage.xml
    python scripts/hooks/enforce_coverage.py --verbose --json
    python scripts/hooks/enforce_coverage.py --dry-run
    python scripts/hooks/enforce_coverage.py --allow-dev  # Allow dev mode (warn only)
    python scripts/hooks/enforce_coverage.py --strict     # Force strict mode (override dev_mode)
"""

import argparse
import json
import logging
import os
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.policy_loader import PolicyError, PolicyLoader

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


@dataclass
class CoverageReport:
    """Coverage enforcement report."""

    timestamp: str
    coverage_value: float
    source: str
    minimum_threshold: float
    warning_threshold: float
    target_threshold: float
    status: str  # "pass", "warning", "fail"
    violations: list[str]
    duration: float
    policy_loaded: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_coverage_json(filepath: Path, verbose: bool = False) -> tuple[float, str]:
    """Parse coverage from coverage.json file with error tolerance.

    Args:
        filepath: Path to coverage.json
        verbose: Whether to enable verbose logging

    Returns:
        Tuple of (coverage percentage, source description)

    Raises:
        ValueError: If file format is unknown or invalid
    """
    try:
        with open(filepath) as f:
            data = json.load(f)

        # Coverage.py JSON format
        if "totals" in data:
            coverage = data["totals"].get("percent_covered", 0.0)
            if verbose:
                logger.info(f"Parsed coverage from coverage.py format: {coverage:.2f}%")
            return coverage, f"coverage.py JSON ({filepath})"

        # Alternative format
        if "coverage" in data:
            coverage = float(data["coverage"])
            if verbose:
                logger.info(f"Parsed coverage from alternative format: {coverage:.2f}%")
            return coverage, f"alternative JSON ({filepath})"

        # Try to find coverage in nested structure
        if "coverage" in str(data).lower():
            logger.warning(f"Found 'coverage' in data but couldn't parse: {filepath}")

        raise ValueError(f"Unknown coverage JSON format in {filepath}")

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {filepath}: {e}")
    except OSError as e:
        raise ValueError(f"Could not read {filepath}: {e}")


def parse_coverage_xml(filepath: Path, verbose: bool = False) -> tuple[float, str]:
    """Parse coverage from coverage.xml file (Cobertura format) with error tolerance.

    Args:
        filepath: Path to coverage.xml
        verbose: Whether to enable verbose logging

    Returns:
        Tuple of (coverage percentage, source description)

    Raises:
        ValueError: If file format is unknown or invalid
    """
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()

        # Cobertura format: <coverage line-rate="0.87" ...>
        line_rate = root.get("line-rate")
        if line_rate:
            coverage = float(line_rate) * 100
            if verbose:
                logger.info(f"Parsed coverage from Cobertura XML: {coverage:.2f}%")
            return coverage, f"Cobertura XML ({filepath})"

        # Try alternative XML formats
        for attr in ["line-rate", "lines-covered", "lines-valid"]:
            if root.get(attr) and verbose:
                logger.warning(f"Found {attr} but not line-rate in {filepath}")

        raise ValueError(f"Could not find coverage data in {filepath}")

    except ET.ParseError as e:
        raise ValueError(f"Invalid XML in {filepath}: {e}")
    except OSError as e:
        raise ValueError(f"Could not read {filepath}: {e}")
    except ValueError as e:
        if "could not convert" in str(e).lower():
            raise ValueError(f"Invalid numeric value in {filepath}: {e}")
        raise


def find_coverage_file(format_type: str = "json") -> Path | None:
    """Find coverage file in common locations.

    Args:
        format_type: "json" or "xml"

    Returns:
        Path to coverage file or None if not found
    """
    repo_root = Path(__file__).parent.parent.parent

    if format_type == "json":
        candidates = [
            repo_root / "coverage.json",
            repo_root / ".coverage.json",
            repo_root / "reports" / "coverage.json",
        ]
    else:  # xml
        candidates = [
            repo_root / "coverage.xml",
            repo_root / "reports" / "coverage.xml",
            repo_root / "htmlcov" / "coverage.xml",
        ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return None


def is_ci_environment() -> bool:
    """Detect if running in a CI/CD environment.

    Returns:
        True if running in CI, False otherwise
    """
    ci_indicators = [
        "CI",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "CIRCLECI",
        "TRAVIS",
        "JENKINS_URL",
        "BUILDKITE",
        "DRONE",
        "SEMAPHORE",
        "BITBUCKET_PIPELINES",
    ]

    return any(os.getenv(indicator) for indicator in ci_indicators)


def get_coverage_from_env() -> float | None:
    """Get coverage from environment variable.

    Returns:
        Coverage percentage or None if not set
    """
    coverage_str = os.getenv("COVERAGE")
    if coverage_str:
        try:
            return float(coverage_str)
        except ValueError:
            pass
    return None


def get_coverage(
    coverage_file: Path | None = None, format_type: str = "json", verbose: bool = False
) -> tuple[float, str]:
    """Get coverage from file or environment.

    Args:
        coverage_file: Path to coverage file (optional)
        format_type: "json" or "xml"
        verbose: Whether to enable verbose logging

    Returns:
        Tuple of (coverage percentage, source description)

    Raises:
        FileNotFoundError: If no coverage data found
    """
    # Try environment variable first
    env_coverage = get_coverage_from_env()
    if env_coverage is not None:
        if verbose:
            logger.info(f"Using coverage from environment: {env_coverage:.2f}%")
        return env_coverage, "environment variable"

    # Try specified file
    if coverage_file:
        if not coverage_file.exists():
            raise FileNotFoundError(f"Coverage file not found: {coverage_file}")

        if format_type == "json":
            coverage, source = parse_coverage_json(coverage_file, verbose)
        else:
            coverage, source = parse_coverage_xml(coverage_file, verbose)

        return coverage, source

    # Try to find coverage file automatically
    found_file = find_coverage_file(format_type)
    if found_file:
        if format_type == "json":
            coverage, source = parse_coverage_json(found_file, verbose)
        else:
            coverage, source = parse_coverage_xml(found_file, verbose)

        return coverage, source

    raise FileNotFoundError(
        f"No coverage data found. Checked:\n"
        f"  - Environment variable: COVERAGE\n"
        f"  - coverage.{format_type} in repo root\n"
        f"  - coverage.{format_type} in reports/\n"
        f"Run tests with coverage first: pytest --cov --cov-report={format_type}"
    )


def main():
    """Enhanced CLI entry point with structured reporting and dev mode support."""
    parser = argparse.ArgumentParser(description="Enforce coverage thresholds")
    parser.add_argument(
        "--coverage-file",
        type=Path,
        help="Path to coverage file (auto-detected if not specified)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "xml"],
        default="json",
        help="Coverage file format (default: json)",
    )
    parser.add_argument(
        "--policy", type=str, help="Path to merge_policy.yml (default: repo root)"
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument(
        "--dry-run", action="store_true", help="Simulate without enforcing"
    )
    parser.add_argument(
        "--allow-dev",
        action="store_true",
        help="Allow development mode (warn only if coverage below minimum)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Force strict enforcement (override dev_mode from policy)",
    )

    args = parser.parse_args()
    start_time = time.time()

    try:
        # Detect CI environment
        in_ci = is_ci_environment()

        # Load policy
        if args.verbose:
            logger.info("Loading policy configuration...")

        try:
            policy = PolicyLoader(args.policy)
            policy_loaded = True
            if args.verbose:
                logger.info(f"Policy loaded from: {policy.policy_path}")
        except Exception as e:
            logger.error(f"Failed to load policy: {e}")
            policy_loaded = False
            if not args.dry_run:
                raise

        # Determine enforcement mode
        dev_mode_from_policy = policy.is_dev_mode_enabled() if policy_loaded else False

        # Final enforcement decision:
        # 1. If --strict flag is set, always enforce strictly
        # 2. If in CI, always enforce strictly
        # 3. If --allow-dev flag is set AND dev_mode enabled in policy, allow dev mode
        # 4. Otherwise, use policy default
        if args.strict:
            enforce_strictly = True
            enforcement_mode = "STRICT MODE (--strict flag)"
        elif in_ci:
            enforce_strictly = True
            enforcement_mode = "CI MODE (strict enforcement)"
        elif args.allow_dev and dev_mode_from_policy:
            enforce_strictly = False
            enforcement_mode = "DEVELOPMENT MODE (relaxed enforcement)"
        elif dev_mode_from_policy and not in_ci:
            # Dev mode is enabled in policy, and we're not in CI, but --allow-dev wasn't explicitly set
            # Be conservative and still enforce, but mention dev mode is available
            enforce_strictly = True
            enforcement_mode = (
                "STRICT MODE (use --allow-dev to enable relaxed enforcement)"
            )
        else:
            enforce_strictly = True
            enforcement_mode = "STRICT MODE (policy default)"

        if (args.verbose or not args.json) and not args.json:
            print(f"🔧 Enforcement Mode: {enforcement_mode}")
            if in_ci:
                print("🏗️  CI Environment Detected: Full enforcement active")
            print()

        # Get coverage data
        if args.verbose:
            logger.info("Reading coverage data...")

        coverage, source = get_coverage(args.coverage_file, args.format, args.verbose)

        # Get thresholds
        if policy_loaded:
            minimum = policy.policy["coverage"]["minimum"]
            warning = policy.policy["coverage"].get("warning", minimum)
            target = policy.policy["coverage"].get("target", 100)
        else:
            # Default thresholds if policy fails
            minimum = 85.0
            warning = 90.0
            target = 95.0
            if args.verbose:
                logger.warning("Using default thresholds due to policy load failure")

        # Check against policy (if loaded)
        violations = []
        if policy_loaded and not args.dry_run:
            try:
                policy.check_coverage(coverage)
                violations = [str(v) for v in policy.violations]
            except PolicyError as e:
                violations = [str(e)]

        # Determine status
        if coverage >= target:
            status = "pass"
            status_msg = f"Excellent! Coverage {coverage:.1f}% exceeds target {target}%"
        elif coverage >= warning:
            status = "pass"
            status_msg = (
                f"Good! Coverage {coverage:.1f}% meets warning threshold {warning}%"
            )
        elif coverage >= minimum:
            status = "warning"
            status_msg = f"Warning: Coverage {coverage:.1f}% is below warning threshold {warning}%"
        else:
            # Coverage below minimum
            if not enforce_strictly:
                # In dev mode, convert failure to warning
                status = "warning"
                status_msg = (
                    f"⚠️  DEV MODE: Coverage {coverage:.1f}% is below minimum threshold {minimum}% "
                    f"(would fail in CI/strict mode)"
                )
            else:
                status = "fail"
                status_msg = f"FAIL: Coverage {coverage:.1f}% is below minimum threshold {minimum}%"

        total_duration = time.time() - start_time

        # Create report
        report = CoverageReport(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            coverage_value=coverage,
            source=source,
            minimum_threshold=minimum,
            warning_threshold=warning,
            target_threshold=target,
            status=status,
            violations=violations,
            duration=total_duration,
            policy_loaded=policy_loaded,
        )

        # Output results
        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            if args.verbose:
                print("📊 Coverage Enforcement")
                print(f"   Source: {source}")
                print(f"   Coverage: {coverage:.2f}%")
                print(
                    f"   Thresholds: Min={minimum}%, Warn={warning}%, Target={target}%"
                )
                print()

            # Display status
            if status == "pass":
                print(f"✅ {status_msg}")
            elif status == "warning":
                print(f"⚠️  {status_msg}")
                if not args.dry_run:
                    print(f"   Minimum: {minimum}%, Target: {target}%")
                if not enforce_strictly and coverage < minimum:
                    print("   💡 Tip: Run with --strict to test CI enforcement locally")
            else:  # fail
                print(f"❌ {status_msg}")
                if not args.dry_run:
                    print(f"   Required: >={minimum}%, Target: {target}%")

            # Display violations
            if violations:
                print()
                print("Policy Violations:")
                for violation in violations:
                    print(f"  - {violation}")

                # Exit with error if critical violations in strict mode
                if policy_loaded and not args.dry_run and policy.fail_on_violation:
                    critical = [
                        v for v in policy.violations if v.severity == "critical"
                    ]
                    if critical:
                        if not args.json:
                            print("\n🚨 Critical violations found in strict mode!")
                        sys.exit(1)

            if args.dry_run:
                print("\n🔍 DRY RUN: No enforcement applied")

        # Exit with appropriate code
        # In dev mode (not enforce_strictly), warnings don't fail
        # In strict mode or CI, warnings pass but failures fail
        if args.dry_run:
            exit_code = 0  # Never fail in dry run mode
        elif status == "fail":
            exit_code = 1
        else:
            exit_code = 0  # pass or warning

        sys.exit(exit_code)

    except FileNotFoundError as e:
        error_msg = f"Coverage file not found: {e}"
        logger.error(error_msg)
        if args.json:
            # Create error report
            report = CoverageReport(
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                coverage_value=0.0,
                source="error",
                minimum_threshold=0.0,
                warning_threshold=0.0,
                target_threshold=0.0,
                status="fail",
                violations=[error_msg],
                duration=time.time() - start_time,
                policy_loaded=False,
            )
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print(f"❌ {error_msg}", file=sys.stderr)
        sys.exit(1)
    except PolicyError as e:
        error_msg = f"Policy Error: {e}"
        logger.error(error_msg)
        if not args.json:
            print(f"❌ {error_msg}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        logger.error(error_msg)
        if args.verbose:
            import traceback

            traceback.print_exc()
        if not args.json:
            print(f"❌ {error_msg}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
