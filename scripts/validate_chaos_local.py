#!/usr/bin/env python3
"""
Pre-Push Chaos Validation CLI - Stage 7.2
Validates chaos setup locally before pushing to avoid CI failures.
"""

import argparse
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class ChaosValidator:
    """Pre-push validation tool for chaos engineering setup."""

    def __init__(self, verbose: bool = False, fix_issues: bool = False):
        self.verbose = verbose
        self.fix_issues = fix_issues
        self.logger = self._setup_logging()
        self.issues_found = []
        self.warnings = []
        self.checks_passed = 0
        self.checks_failed = 0

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=level, format="%(asctime)s - [%(levelname)s] - %(message)s"
        )
        return logging.getLogger(__name__)

    def run_check(self, name: str, func) -> bool:
        """Run a validation check and track results."""
        print(f"\n{'='*60}")
        print(f"🔍 {name}")
        print("=" * 60)

        try:
            success = func()

            if success:
                self.checks_passed += 1
                print(f"✅ {name} - PASSED")
            else:
                self.checks_failed += 1
                print(f"❌ {name} - FAILED")

            return success

        except Exception as e:
            self.checks_failed += 1
            self.logger.error(f"Check failed with exception: {e}")
            print(f"❌ {name} - FAILED (Exception: {e})")
            return False

    def check_dependencies(self) -> bool:
        """Check for missing dependencies."""
        print("📦 Checking dependencies...")

        try:
            # Run dependency sentinel
            result = subprocess.run(
                [sys.executable, "scripts/chaos_dependency_sentinel.py", "--dry-run"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                self.issues_found.append("Missing dependencies detected")
                print("⚠️  Missing dependencies found")
                print(result.stdout)

                if self.fix_issues:
                    print("\n🔧 Auto-fixing dependencies...")
                    fix_result = subprocess.run(
                        [
                            sys.executable,
                            "scripts/chaos_dependency_sentinel.py",
                            "--fix",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=60,
                    )

                    if fix_result.returncode == 0:
                        print("✅ Dependencies fixed")
                        return True
                    else:
                        print("❌ Failed to fix dependencies")
                        return False

                return False
            else:
                print("✅ All dependencies present")
                return True

        except Exception as e:
            self.logger.error(f"Dependency check failed: {e}")
            self.issues_found.append(f"Dependency check error: {e}")
            return False

    def check_chaos_configs(self) -> bool:
        """Validate chaos configuration files."""
        print("📋 Validating chaos configurations...")

        config_files = [
            "deploy/chaos_scenarios.yml",
            "configs/slo/health_api_slo.yaml",
            "configs/remediation-rules/auto_restart.yaml",
        ]

        all_valid = True

        for config_file in config_files:
            if not os.path.exists(config_file):
                print(f"⚠️  Config file missing: {config_file}")
                self.warnings.append(f"Missing config: {config_file}")
                continue

            try:
                import yaml

                with open(config_file) as f:
                    yaml.safe_load(f)
                print(f"✅ {config_file}")
            except Exception as e:
                print(f"❌ {config_file}: {e}")
                self.issues_found.append(f"Invalid config: {config_file}")
                all_valid = False

        return all_valid

    def check_chaos_scripts(self) -> bool:
        """Verify chaos scripts are present and importable."""
        print("🐍 Checking chaos scripts...")

        scripts = {
            "deploy/chaos_injector.py": "ChaosInjector",
            "deploy/resilience_validator.py": "ResilienceValidator",
            "deploy/chaos_metrics_exporter.py": "ChaosMetricsExporter",
        }

        all_valid = True

        for script_path, class_name in scripts.items():
            if not os.path.exists(script_path):
                print(f"❌ Missing script: {script_path}")
                self.issues_found.append(f"Missing script: {script_path}")
                all_valid = False
                continue

            # Try to import
            try:
                # Add current directory to Python path for imports
                import sys

                if os.getcwd() not in sys.path:
                    sys.path.insert(0, os.getcwd())

                module_path = script_path.replace("/", ".").replace(".py", "")
                exec(f"from {module_path} import {class_name}")
                print(f"✅ {script_path} ({class_name})")
            except Exception as e:
                print(f"❌ {script_path}: {e}")
                self.issues_found.append(f"Import failed: {script_path}")
                all_valid = False

        return all_valid

    def _create_quick_validation_config(self, output_path: str):
        """Create a minimal chaos config for quick validation."""
        import yaml

        quick_config = {
            "slo_targets": {
                "mttr_seconds": 45,
                "max_error_rate_percent": 8.0,
                "min_availability_percent": 92.0,
                "max_latency_degradation_ms": 800,
                "max_recovery_time_seconds": 15,
                "required_health_checks": 3,
                "health_check_interval_seconds": 2,
            },
            "scenarios": [
                {
                    "name": "Quick CPU Test",
                    "type": "cpu_exhaust",
                    "intensity": "light",
                    "duration": 5,
                    "description": "Quick CPU stress test for validation",
                    "parameters": {"cpu_workers": 1, "expected_impact": "minimal"},
                },
                {
                    "name": "Quick Health Check",
                    "type": "health_check",
                    "intensity": "light",
                    "duration": 3,
                    "description": "Quick health endpoint validation",
                    "parameters": {"endpoint": "/api/health", "expected_status": 200},
                },
            ],
        }

        with open(output_path, "w") as f:
            yaml.dump(quick_config, f, default_flow_style=False)

    def check_chaos_dry_run(self) -> bool:
        """Run chaos injector in dry-run mode."""
        print("🔥 Testing chaos injector (dry-run)...")

        try:
            # Create a quick validation config with only 2 scenarios for faster testing
            quick_config = "/tmp/chaos_quick_validation.yml"
            self._create_quick_validation_config(quick_config)

            result = subprocess.run(
                [
                    sys.executable,
                    "deploy/chaos_injector.py",
                    "--dry-run",
                    "--config",
                    quick_config,
                    "--output",
                    "/tmp/chaos_test_results.json",
                ],
                capture_output=True,
                text=True,
                timeout=15,  # Reduced timeout for quick validation
            )

            if result.returncode != 0:
                print("❌ Chaos injector failed:")
                print(result.stderr)
                self.issues_found.append("Chaos injector dry-run failed")
                return False
            else:
                print("✅ Chaos injector working")
                return True

        except subprocess.TimeoutExpired:
            print("❌ Chaos injector timed out")
            self.issues_found.append("Chaos injector timeout")
            return False
        except Exception as e:
            print(f"❌ Chaos injector error: {e}")
            self.issues_found.append(f"Chaos injector error: {e}")
            return False

    def check_health_endpoint(self) -> bool:
        """Check if health endpoint logic is correct."""
        print("🏥 Validating health endpoint...")

        # Check if health endpoint exists in code
        health_files = [
            "src/routes.py",
            "src/api/health.py",
            "src/main.py",
        ]

        health_endpoint_found = False

        for health_file in health_files:
            if not os.path.exists(health_file):
                continue

            try:
                with open(health_file) as f:
                    content = f.read()
                    if (
                        "/api/health" in content
                        or "@app.route" in content
                        and "health" in content
                    ):
                        health_endpoint_found = True
                        print(f"✅ Health endpoint found in {health_file}")
                        break
            except Exception:
                continue

        if not health_endpoint_found:
            print("⚠️  Could not verify health endpoint")
            self.warnings.append("Health endpoint not verified")
            return True  # Don't fail on this

        return True

    def check_file_permissions(self) -> bool:
        """Check if chaos scripts are executable."""
        print("🔐 Checking file permissions...")

        scripts = [
            "deploy/chaos_injector.py",
            "deploy/resilience_validator.py",
            "scripts/chaos_dependency_sentinel.py",
        ]

        all_ok = True

        for script in scripts:
            if os.path.exists(script):
                if os.access(script, os.X_OK):
                    print(f"✅ {script} is executable")
                else:
                    print(f"⚠️  {script} is not executable")
                    self.warnings.append(f"{script} not executable")

                    if self.fix_issues:
                        try:
                            os.chmod(script, 0o755)
                            print(f"   🔧 Made {script} executable")
                        except Exception as e:
                            print(f"   ❌ Failed to make executable: {e}")
            else:
                print(f"⚠️  {script} not found")

        return all_ok

    def check_github_actions(self) -> bool:
        """Validate GitHub Actions workflows."""
        print("⚙️  Checking GitHub Actions workflows...")

        workflow_dir = ".github/workflows"
        if not os.path.exists(workflow_dir):
            print("⚠️  .github/workflows directory not found")
            self.warnings.append("No GitHub Actions workflows")
            return True  # Don't fail on this

        chaos_workflows = [
            "chaos-engineering.yml",
            "chaos.yml",
        ]

        found_workflows = []
        for workflow in chaos_workflows:
            workflow_path = os.path.join(workflow_dir, workflow)
            if os.path.exists(workflow_path):
                found_workflows.append(workflow)
                print(f"✅ Found {workflow}")

        if not found_workflows:
            print("⚠️  No chaos workflows found")
            self.warnings.append("No chaos workflows configured")

        return True

    def generate_report(self, output_file: str = "reports/chaos_validation_report.md"):
        """Generate a validation report."""
        timestamp = datetime.now().isoformat()

        report = f"""# Pre-Push Chaos Validation Report

**Generated:** {timestamp}
**Checks Passed:** {self.checks_passed}
**Checks Failed:** {self.checks_failed}
**Warnings:** {len(self.warnings)}

## Summary

"""

        if self.checks_failed == 0 and not self.issues_found:
            report += "✅ **All checks passed!** Ready to push.\n\n"
        else:
            report += f"❌ **{self.checks_failed} check(s) failed.** Please fix before pushing.\n\n"

        if self.issues_found:
            report += "## Issues Found\n\n"
            for issue in self.issues_found:
                report += f"- ❌ {issue}\n"
            report += "\n"

        if self.warnings:
            report += "## Warnings\n\n"
            for warning in self.warnings:
                report += f"- ⚠️  {warning}\n"
            report += "\n"

        report += """## Recommendations

"""

        if self.issues_found:
            report += "### Critical Actions\n\n"
            report += "1. Fix all critical issues listed above\n"
            report += "2. Re-run validation: `python scripts/validate_chaos_local.py`\n"
            report += "3. Use `--fix` flag to auto-fix common issues: `python scripts/validate_chaos_local.py --fix`\n\n"

        if self.warnings:
            report += "### Suggested Improvements\n\n"
            report += "1. Review warnings and address as needed\n"
            report += "2. Ensure all configurations are up to date\n\n"

        report += """## Next Steps

- ✅ Commit changes if all checks passed
- 🚀 Push to trigger CI/CD pipeline
- 📊 Monitor chaos validation job in GitHub Actions
"""

        # Save report
        try:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w") as f:
                f.write(report)
            print(f"\n📄 Report saved to: {output_file}")
        except Exception as e:
            self.logger.error(f"Failed to save report: {e}")


def main():
    """Main entry point for chaos validator."""
    parser = argparse.ArgumentParser(
        description="Pre-Push Chaos Validation - Validate chaos setup before pushing"
    )
    parser.add_argument(
        "--fix", action="store_true", help="Automatically fix issues when possible"
    )
    parser.add_argument(
        "--report",
        type=str,
        default="reports/chaos_validation_report.md",
        help="Output file for validation report",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "--skip",
        nargs="+",
        help="Skip specific checks (dependencies, configs, scripts, dry-run, health, permissions, workflows)",
    )

    args = parser.parse_args()

    print("🧪 Pre-Push Chaos Validation - Stage 7.2")
    print("=" * 60)
    print(f"Mode: {'Auto-fix enabled' if args.fix else 'Check only'}")
    print("=" * 60)

    # Create validator
    validator = ChaosValidator(verbose=args.verbose, fix_issues=args.fix)

    # Define checks
    checks = [
        ("Dependency Check", validator.check_dependencies),
        ("Configuration Validation", validator.check_chaos_configs),
        ("Script Verification", validator.check_chaos_scripts),
        ("Chaos Dry-Run Test", validator.check_chaos_dry_run),
        ("Health Endpoint Check", validator.check_health_endpoint),
        ("File Permissions", validator.check_file_permissions),
        ("GitHub Actions Workflows", validator.check_github_actions),
    ]

    # Filter skipped checks
    skip_list = args.skip or []
    checks = [
        (name, func)
        for name, func in checks
        if not any(skip in name.lower() for skip in skip_list)
    ]

    # Run all checks
    for check_name, check_func in checks:
        validator.run_check(check_name, check_func)

    # Generate report
    validator.generate_report(args.report)

    # Print final summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    print(f"✅ Checks Passed: {validator.checks_passed}")
    print(f"❌ Checks Failed: {validator.checks_failed}")
    print(f"⚠️  Warnings: {len(validator.warnings)}")

    if validator.issues_found:
        print("\n❌ Issues Found:")
        for issue in validator.issues_found:
            print(f"   - {issue}")

    if validator.warnings:
        print("\n⚠️  Warnings:")
        for warning in validator.warnings:
            print(f"   - {warning}")

    print("\n" + "=" * 60)

    if validator.checks_failed == 0:
        print("✅ ALL CHECKS PASSED - Ready to push!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ VALIDATION FAILED - Fix issues before pushing")
        print("=" * 60)
        if not args.fix:
            print("\n💡 Tip: Run with --fix to automatically fix common issues")
        sys.exit(1)


if __name__ == "__main__":
    main()
