#!/usr/bin/env python3
"""
Stage 7.3.1 - Notion Sanity Check Script

Comprehensive validation script that performs:
- Environment variable validation
- Notion API connectivity testing
- Database access verification
- Schema property validation
- Dry-run sync simulation
- Detailed reporting with actionable feedback

Usage:
    python scripts/sanity_check_notion.py [--dry-run]
"""

import argparse
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # python-dotenv not available, continue without it
    pass

from scripts.validate_notion_schema import SchemaValidator
from utils.notion_client import NotionClient


@dataclass
class CheckResult:
    """Result from a sanity check operation."""

    name: str
    status: str  # success, failure, warning
    message: str
    details: dict[str, Any] | None = None
    duration_seconds: float = 0.0


class NotionSanityChecker:
    """Comprehensive Notion integration sanity checker."""

    def __init__(self, dry_run: bool = False):
        """
        Initialize the sanity checker.

        Args:
            dry_run: If True, simulate sync operations without actual writes
        """
        self.dry_run = dry_run
        self.results: list[CheckResult] = []
        self.start_time = time.time()

        print("=" * 70)
        print("🔍 Stage 7.3.1 - Notion Sanity Check")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Dry-run mode: {'✅ Enabled' if dry_run else '❌ Disabled'}")
        print()

    def _add_result(
        self,
        name: str,
        status: str,
        message: str,
        details: dict | None = None,
        duration: float = 0.0,
    ):
        """Add a check result."""
        result = CheckResult(name, status, message, details, duration)
        self.results.append(result)

        # Print result with appropriate icon
        icon = {"success": "✅", "failure": "❌", "warning": "⚠️"}.get(status, "ℹ️")
        print(f"{icon} {name}: {message}")

        if details:
            for key, value in details.items():
                print(f"   {key}: {value}")
        print()

    def check_environment_variables(self) -> bool:
        """Check that all required environment variables are set."""
        print("🔑 Checking environment variables...")

        required_vars = {
            "NOTION_API_KEY": "Notion API key",
            "MAGSASA_CI_DB_ID": "MAGSASA CI Reports Database ID",
            "MAGSASA_ROADMAP_DB_ID": "MAGSASA Roadmap Database ID",
            "AI_STUDIO_MILESTONES_DB_ID": "AI Studio Milestones Database ID",
        }

        optional_vars = {
            "CONTROL_CENTER_PAGE_ID": "Control Center Page ID",
            "GITHUB_TOKEN": "GitHub Token",
            "GITHUB_REPOSITORY": "GitHub Repository",
        }

        missing_required = []
        missing_optional = []

        for var, _description in required_vars.items():
            value = os.getenv(var)
            if not value:
                missing_required.append(var)
            else:
                print(
                    f"   ✅ {var}: {value[:20]}..."
                    if len(value) > 20
                    else f"   ✅ {var}: {value}"
                )

        for var, _description in optional_vars.items():
            value = os.getenv(var)
            if not value:
                missing_optional.append(var)
            else:
                print(
                    f"   ✅ {var}: {value[:20]}..."
                    if len(value) > 20
                    else f"   ✅ {var}: {value}"
                )

        if missing_required:
            self._add_result(
                "Environment Variables",
                "failure",
                f"Missing required variables: {', '.join(missing_required)}",
                {
                    "missing_required": missing_required,
                    "missing_optional": missing_optional,
                },
            )
            return False
        else:
            self._add_result(
                "Environment Variables",
                "success",
                "All required variables present",
                {"missing_optional": missing_optional},
            )
            return True

    def check_api_connectivity(self) -> bool:
        """Test Notion API connectivity and authentication."""
        print("🔗 Testing Notion API connectivity...")
        start_time = time.time()

        try:
            client = NotionClient()
            duration = time.time() - start_time

            # Test basic API call
            search_results = client.search(
                query="", filter_params={"value": "database", "property": "object"}
            )

            self._add_result(
                "API Connectivity",
                "success",
                f"Connected successfully in {duration:.2f}s",
                {
                    "accessible_databases": len(search_results),
                    "api_key_prefix": client.api_key[:20] + "...",
                },
            )
            return True

        except Exception as e:
            duration = time.time() - start_time
            self._add_result(
                "API Connectivity",
                "failure",
                f"Connection failed: {str(e)}",
                {"duration": f"{duration:.2f}s", "error_type": type(e).__name__},
            )
            return False

    def check_database_access(self) -> bool:
        """Verify access to all configured databases."""
        print("📊 Checking database access...")

        databases = [
            ("MAGSASA_CI_DB_ID", "CI Reports Database"),
            ("MAGSASA_ROADMAP_DB_ID", "Roadmap Database"),
            ("AI_STUDIO_MILESTONES_DB_ID", "AI Studio Milestones Database"),
        ]

        all_accessible = True
        access_results = {}

        for env_var, db_name in databases:
            db_id = os.getenv(env_var)
            if not db_id:
                self._add_result(
                    f"Database Access - {db_name}",
                    "failure",
                    f"Database ID not set in {env_var}",
                )
                all_accessible = False
                continue

            start_time = time.time()
            try:
                client = NotionClient()
                database = client.get_database(db_id)
                duration = time.time() - start_time

                title = database.get("title", [{}])[0].get("plain_text", "Unknown")
                properties = list(database.get("properties", {}).keys())

                self._add_result(
                    f"Database Access - {db_name}",
                    "success",
                    f"Accessible in {duration:.2f}s",
                    {
                        "title": title,
                        "properties_count": len(properties),
                        "db_id": db_id[:8] + "...",
                    },
                )

                access_results[db_name] = {
                    "accessible": True,
                    "title": title,
                    "properties": properties,
                    "duration": duration,
                }

            except Exception as e:
                duration = time.time() - start_time
                self._add_result(
                    f"Database Access - {db_name}",
                    "failure",
                    f"Access failed: {str(e)}",
                    {"db_id": db_id[:8] + "...", "duration": f"{duration:.2f}s"},
                )
                all_accessible = False
                access_results[db_name] = {"accessible": False, "error": str(e)}

        return all_accessible

    def check_schema_validation(self) -> bool:
        """Validate database schemas against expected definitions."""
        print("🔍 Validating database schemas...")

        try:
            validator = SchemaValidator()
            is_valid = validator.validate_all()

            if is_valid:
                self._add_result(
                    "Schema Validation", "success", "All database schemas are valid"
                )
                return True
            else:
                self._add_result(
                    "Schema Validation",
                    "failure",
                    f"Schema validation failed with {len(validator.errors)} error(s)",
                    {"errors": validator.errors[:5]},  # Show first 5 errors
                )
                return False

        except Exception as e:
            self._add_result(
                "Schema Validation", "failure", f"Validation failed: {str(e)}"
            )
            return False

    def simulate_dry_run_sync(self) -> bool:
        """Simulate a dry-run sync to preview data flow."""
        print("🧪 Simulating dry-run sync...")

        try:
            # Import sync modules
            from scripts.sync_ci_weekly import sync_ci_reports
            from scripts.sync_milestones_weekly import sync_milestones
            from scripts.sync_roadmap_weekly import sync_roadmap

            client = NotionClient()
            sync_results = {}

            # Simulate CI sync
            try:
                print("   📈 Simulating CI reports sync...")
                ci_result = sync_ci_reports(
                    client, os.getenv("MAGSASA_CI_DB_ID"), dry_run=True
                )
                sync_results["CI Reports"] = ci_result.get("records_synced", 0)
                print(f"      ✅ {sync_results['CI Reports']} CI records prepared")
            except Exception as e:
                print(f"      ❌ CI sync simulation failed: {e}")
                sync_results["CI Reports"] = f"Error: {str(e)}"

            # Simulate Roadmap sync
            try:
                print("   🗺️ Simulating roadmap sync...")
                roadmap_result = sync_roadmap(
                    client, os.getenv("MAGSASA_ROADMAP_DB_ID"), dry_run=True
                )
                sync_results["Roadmap"] = roadmap_result.get("records_synced", 0)
                print(f"      ✅ {sync_results['Roadmap']} roadmap milestones updated")
            except Exception as e:
                print(f"      ❌ Roadmap sync simulation failed: {e}")
                sync_results["Roadmap"] = f"Error: {str(e)}"

            # Simulate Milestones sync
            try:
                print("   🚀 Simulating milestones sync...")
                milestones_result = sync_milestones(
                    client, os.getenv("AI_STUDIO_MILESTONES_DB_ID"), dry_run=True
                )
                sync_results["Milestones"] = milestones_result.get("records_synced", 0)
                print(
                    f"      ✅ {sync_results['Milestones']} strategic milestones verified"
                )
            except Exception as e:
                print(f"      ❌ Milestones sync simulation failed: {e}")
                sync_results["Milestones"] = f"Error: {str(e)}"

            # Check if any syncs had errors
            has_errors = any(
                isinstance(v, str) and v.startswith("Error:")
                for v in sync_results.values()
            )

            if has_errors:
                self._add_result(
                    "Dry-run Sync Simulation",
                    "failure",
                    "Some sync simulations failed",
                    sync_results,
                )
                return False
            else:
                total_records = sum(
                    v for v in sync_results.values() if isinstance(v, int)
                )
                self._add_result(
                    "Dry-run Sync Simulation",
                    "success",
                    f"All sync simulations successful - {total_records} total records",
                    sync_results,
                )
                return True

        except Exception as e:
            self._add_result(
                "Dry-run Sync Simulation", "failure", f"Simulation failed: {str(e)}"
            )
            return False

    def generate_summary_report(self) -> dict[str, Any]:
        """Generate a comprehensive summary report."""
        total_duration = time.time() - self.start_time

        successful = [r for r in self.results if r.status == "success"]
        failed = [r for r in self.results if r.status == "failure"]
        warnings = [r for r in self.results if r.status == "warning"]

        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_checks": len(self.results),
            "successful": len(successful),
            "failed": len(failed),
            "warnings": len(warnings),
            "total_duration_seconds": round(total_duration, 2),
            "overall_status": "PASS" if len(failed) == 0 else "FAIL",
            "checks": [
                {
                    "name": r.name,
                    "status": r.status,
                    "message": r.message,
                    "duration": r.duration_seconds,
                }
                for r in self.results
            ],
        }

        return summary

    def print_summary(self, summary: dict[str, Any]):
        """Print a formatted summary report."""
        print("=" * 70)
        print("📊 SANITY CHECK SUMMARY")
        print("=" * 70)

        status_icon = "✅" if summary["overall_status"] == "PASS" else "❌"
        print(f"{status_icon} Overall Status: {summary['overall_status']}")
        print(f"⏱️  Total Duration: {summary['total_duration_seconds']:.2f}s")
        print(
            f"📈 Checks: {summary['successful']} passed, {summary['failed']} failed, {summary['warnings']} warnings"
        )
        print()

        if summary["failed"] > 0:
            print("❌ FAILED CHECKS:")
            for check in summary["checks"]:
                if check["status"] == "failure":
                    print(f"   • {check['name']}: {check['message']}")
            print()

        if summary["warnings"] > 0:
            print("⚠️ WARNINGS:")
            for check in summary["checks"]:
                if check["status"] == "warning":
                    print(f"   • {check['name']}: {check['message']}")
            print()

        print("=" * 70)

        if summary["overall_status"] == "PASS":
            print("🎉 All sanity checks passed! Notion integration is ready.")
            print()
            print("Next steps:")
            print("  1. Run live sync: python scripts/notion_cli.py sync --all")
            print("  2. Enable weekly automation: The GitHub workflow is ready")
            print("  3. Monitor sync logs: Check reports/ directory")
        else:
            print("🚨 Some sanity checks failed. Please address the issues above.")
            print()
            print("Common solutions:")
            print("  1. Check .env file has correct database IDs")
            print("  2. Verify databases are shared with your Notion integration")
            print("  3. Ensure API key has proper permissions")
            print("  4. Fix any schema drift in Notion databases")

        print("=" * 70)

    def run_all_checks(self) -> int:
        """Run all sanity checks and return exit code."""
        checks = [
            ("Environment Variables", self.check_environment_variables),
            ("API Connectivity", self.check_api_connectivity),
            ("Database Access", self.check_database_access),
            ("Schema Validation", self.check_schema_validation),
        ]

        # Add dry-run simulation if requested
        if self.dry_run:
            checks.append(("Dry-run Sync Simulation", self.simulate_dry_run_sync))

        # Run all checks
        for check_name, check_func in checks:
            try:
                check_func()
            except Exception as e:
                self._add_result(
                    check_name, "failure", f"Check failed with exception: {str(e)}"
                )

        # Generate and print summary
        summary = self.generate_summary_report()
        self.print_summary(summary)

        # Save summary to file
        reports_dir = Path(__file__).parent.parent / "reports"
        reports_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = reports_dir / f"sanity-check-{timestamp}.json"

        try:
            import json

            with open(summary_file, "w") as f:
                json.dump(summary, f, indent=2)
            print(f"📄 Summary saved to: {summary_file}")
        except Exception as e:
            print(f"⚠️ Failed to save summary: {e}")

        # Return appropriate exit code
        return 0 if summary["overall_status"] == "PASS" else 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Stage 7.3.1 Notion Sanity Check",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full sanity check
  python scripts/sanity_check_notion.py

  # Include dry-run sync simulation
  python scripts/sanity_check_notion.py --dry-run

  # Quick validation only
  python scripts/sanity_check_notion.py --validate-only
        """,
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Include dry-run sync simulation"
    )
    parser.add_argument(
        "--validate-only", action="store_true", help="Run only schema validation"
    )

    args = parser.parse_args()

    try:
        checker = NotionSanityChecker(dry_run=args.dry_run)

        if args.validate_only:
            # Run only schema validation
            is_valid = checker.check_schema_validation()
            return 0 if is_valid else 1
        else:
            # Run all checks
            return checker.run_all_checks()

    except KeyboardInterrupt:
        print("\n⚠️ Sanity check interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Fatal error during sanity check: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
