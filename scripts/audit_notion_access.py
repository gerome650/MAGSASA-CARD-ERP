#!/usr/bin/env python3
"""
Stage 7.3.1 - Notion Access Audit Utility

This script performs comprehensive diagnostics on Notion API access:
- Verifies all required environment variables
- Tests API connectivity and authentication
- Lists all accessible databases and pages
- Validates that required databases are visible to the integration
- Provides actionable remediation steps for access issues

Usage:
    python scripts/audit_notion_access.py
    python scripts/audit_notion_access.py --json
    python scripts/audit_notion_access.py --auto-fix
"""

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
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
    print("⚠️  python-dotenv not installed, relying on existing environment variables")
    pass


@dataclass
class DatabaseInfo:
    """Information about a Notion database."""

    name: str
    id: str
    id_prefix: str
    accessible: bool
    workspace: str
    properties_count: int
    last_edited: str
    error: str | None = None


@dataclass
class AuditResult:
    """Complete audit result."""

    timestamp: str
    overall_status: str
    api_key_valid: bool
    api_key_prefix: str
    total_accessible_databases: int
    total_accessible_pages: int
    required_databases: list[dict[str, Any]]
    accessible_databases: list[dict[str, Any]]
    missing_databases: list[str]
    errors: list[str]
    warnings: list[str]
    remediation_steps: list[str]


class NotionAccessAuditor:
    """Comprehensive Notion access auditor."""

    def __init__(self, export_json: bool = False, auto_fix: bool = False):
        """
        Initialize the auditor.

        Args:
            export_json: If True, export results to JSON file
            auto_fix: If True, attempt to run sanity check after successful audit
        """
        self.export_json = export_json
        self.auto_fix = auto_fix
        self.errors = []
        self.warnings = []
        self.remediation_steps = []

        print("=" * 80)
        print("🔍 Stage 7.3.1 - Notion Access Audit")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

    def check_environment_variables(self) -> tuple[bool, dict[str, str]]:
        """
        Check and validate all environment variables.

        Returns:
            Tuple of (success, env_vars_dict)
        """
        print("🔑 Step 1: Environment Variable Verification")
        print("-" * 80)

        required_vars = {
            "NOTION_API_KEY": "Notion API Key",
            "MAGSASA_CI_DB_ID": "MAGSASA CI Reports Database ID",
            "MAGSASA_ROADMAP_DB_ID": "MAGSASA Roadmap Database ID",
            "AI_STUDIO_MILESTONES_DB_ID": "AI Studio Milestones Database ID",
        }

        optional_vars = {
            "CONTROL_CENTER_PAGE_ID": "Control Center Page ID",
            "GITHUB_TOKEN": "GitHub Token",
            "GITHUB_REPOSITORY": "GitHub Repository",
        }

        env_values = {}
        missing_required = []
        missing_optional = []

        # Check required variables
        for var, _description in required_vars.items():
            value = os.getenv(var)
            if not value or not value.strip():
                missing_required.append(var)
                print(f"❌ {var}: NOT SET")
                self.errors.append(f"Missing required variable: {var}")
            else:
                env_values[var] = value
                # Mask sensitive values
                if "API_KEY" in var or "TOKEN" in var:
                    display_value = value[:20] + "..." + value[-4:]
                elif "ID" in var:
                    display_value = value[:20] + "..." if len(value) > 20 else value
                else:
                    display_value = value
                print(f"✅ {var}: {display_value}")

        # Check optional variables
        for var, _description in optional_vars.items():
            value = os.getenv(var)
            if not value or not value.strip():
                missing_optional.append(var)
                print(f"⚠️  {var}: NOT SET (optional)")
                self.warnings.append(f"Optional variable not set: {var}")
            else:
                env_values[var] = value
                if "API_KEY" in var or "TOKEN" in var:
                    display_value = (
                        value[:20] + "..." + value[-4:] if len(value) > 24 else "***"
                    )
                else:
                    display_value = value[:20] + "..." if len(value) > 20 else value
                print(f"✅ {var}: {display_value}")

        print()

        if missing_required:
            print(f"❌ Missing {len(missing_required)} required variable(s)")
            self.remediation_steps.append("Set missing required variables in .env file")
            self.remediation_steps.append("Copy env.template to .env if needed")
            return False, env_values
        else:
            print("✅ All required variables present")
            if missing_optional:
                print(f"⚠️  {len(missing_optional)} optional variable(s) not set")
            return True, env_values

    def test_api_connectivity(self, api_key: str) -> tuple[bool, Any | None]:
        """
        Test Notion API connectivity and authentication.

        Args:
            api_key: The Notion API key to test

        Returns:
            Tuple of (success, client_or_error)
        """
        print("\n🔗 Step 2: Notion API Connectivity Test")
        print("-" * 80)

        try:
            import requests

            # Test API with search endpoint
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28",
            }

            print("Testing connection to Notion API...")
            response = requests.post(
                "https://api.notion.com/v1/search",
                headers=headers,
                json={"page_size": 1},
            )

            if response.status_code == 401:
                error_data = response.json()
                error_msg = error_data.get("message", "Unauthorized")
                print(f"❌ 401 Unauthorized: {error_msg}")
                self.errors.append(f"API authentication failed: {error_msg}")

                # Provide detailed remediation
                self.remediation_steps.extend(
                    [
                        "Verify NOTION_API_KEY is correct in .env file",
                        "Ensure you're using an Internal Integration, not OAuth",
                        "Check that the integration hasn't been revoked in Notion settings",
                        "Go to https://www.notion.so/my-integrations to verify your integration",
                    ]
                )
                return False, error_msg

            elif response.status_code == 403:
                print("❌ 403 Forbidden: Integration has no access permissions")
                self.errors.append("Integration lacks necessary permissions")
                self.remediation_steps.extend(
                    [
                        "Grant integration access to workspaces in Notion",
                        "Share databases with the integration using 'Add Connections' in Notion",
                    ]
                )
                return False, "Forbidden"

            elif response.status_code != 200:
                print(f"❌ API Error {response.status_code}: {response.text}")
                self.errors.append(f"API returned status {response.status_code}")
                return False, response.text

            data = response.json()
            results = data.get("results", [])

            print("✅ Successfully connected to Notion API")
            print(f"   API Key: {api_key[:20]}...{api_key[-4:]}")
            print(f"   Accessible items: {len(results)}")
            print()

            return True, headers

        except requests.exceptions.RequestException as e:
            print(f"❌ Connection failed: {e}")
            self.errors.append(f"Network error: {str(e)}")
            self.remediation_steps.append("Check your internet connection")
            return False, str(e)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            self.errors.append(f"Unexpected error: {str(e)}")
            return False, str(e)

    def list_accessible_resources(self, headers: dict) -> tuple[list[dict], list[dict]]:
        """
        List all accessible databases and pages.

        Args:
            headers: API request headers

        Returns:
            Tuple of (databases_list, pages_list)
        """
        print("📊 Step 3: Listing Accessible Resources")
        print("-" * 80)

        try:
            import requests

            # Search for all databases
            print("Searching for databases...")
            response = requests.post(
                "https://api.notion.com/v1/search",
                headers=headers,
                json={
                    "filter": {"value": "database", "property": "object"},
                    "page_size": 100,
                },
            )

            databases = []
            pages = []

            if response.status_code == 200:
                data = response.json()
                databases = data.get("results", [])
                print(f"✅ Found {len(databases)} accessible database(s)")
            else:
                print(f"⚠️  Database search returned status {response.status_code}")
                self.warnings.append(
                    f"Could not list databases: {response.status_code}"
                )

            # Search for pages
            print("Searching for pages...")
            response = requests.post(
                "https://api.notion.com/v1/search",
                headers=headers,
                json={
                    "filter": {"value": "page", "property": "object"},
                    "page_size": 100,
                },
            )

            if response.status_code == 200:
                data = response.json()
                pages = data.get("results", [])
                print(f"✅ Found {len(pages)} accessible page(s)")
            else:
                print(f"⚠️  Page search returned status {response.status_code}")
                self.warnings.append(f"Could not list pages: {response.status_code}")

            print()
            return databases, pages

        except Exception as e:
            print(f"❌ Failed to list resources: {e}")
            self.errors.append(f"Resource listing failed: {str(e)}")
            return [], []

    def verify_required_databases(
        self, headers: dict, env_vars: dict, accessible_dbs: list[dict]
    ) -> list[DatabaseInfo]:
        """
        Verify that all required databases are accessible.

        Args:
            headers: API request headers
            env_vars: Environment variables
            accessible_dbs: List of accessible databases from search

        Returns:
            List of DatabaseInfo objects
        """
        print("🎯 Step 4: Verifying Required Database Access")
        print("-" * 80)

        required_dbs = [
            ("MAGSASA_CI_DB_ID", "CI Intelligence Reports"),
            ("MAGSASA_ROADMAP_DB_ID", "MAGSASA-CARD ERP Roadmap"),
            ("AI_STUDIO_MILESTONES_DB_ID", "AI Studio Strategic Milestones"),
        ]

        database_infos = []

        # Create a map of accessible database IDs
        accessible_db_ids = {}
        for db in accessible_dbs:
            db_id = db.get("id", "")
            # Remove hyphens for comparison
            clean_id = db_id.replace("-", "")
            title = ""
            if "title" in db and db["title"]:
                title = db["title"][0].get("plain_text", "Unknown")
            accessible_db_ids[clean_id] = {
                "id": db_id,
                "title": title,
                "last_edited": db.get("last_edited_time", "Unknown"),
            }

        for env_var, expected_name in required_dbs:
            db_id = env_vars.get(env_var, "")

            if not db_id:
                print(f"❌ {expected_name}: Database ID not set")
                database_infos.append(
                    DatabaseInfo(
                        name=expected_name,
                        id="NOT_SET",
                        id_prefix="N/A",
                        accessible=False,
                        workspace="N/A",
                        properties_count=0,
                        last_edited="N/A",
                        error="Database ID not set in environment",
                    )
                )
                self.errors.append(f"{expected_name}: ID not configured")
                continue

            # Clean the database ID (remove hyphens and query params)
            clean_db_id = db_id.split("?")[0].replace("-", "")

            try:
                import requests

                # Try to get the database directly
                response = requests.get(
                    f"https://api.notion.com/v1/databases/{clean_db_id}",
                    headers=headers,
                )

                if response.status_code == 200:
                    db_data = response.json()
                    title = ""
                    if "title" in db_data and db_data["title"]:
                        title = db_data["title"][0].get("plain_text", expected_name)

                    properties = db_data.get("properties", {})
                    last_edited = db_data.get("last_edited_time", "Unknown")

                    # Try to determine workspace (from parent)
                    workspace = "AI Studio Workspace"  # Default assumption

                    print(f"✅ {expected_name}")
                    print(f"   Title: {title}")
                    print(f"   ID: {clean_db_id[:8]}...{clean_db_id[-8:]}")
                    print(f"   Properties: {len(properties)}")
                    print(f"   Last edited: {last_edited}")

                    database_infos.append(
                        DatabaseInfo(
                            name=expected_name,
                            id=clean_db_id,
                            id_prefix=clean_db_id[:12],
                            accessible=True,
                            workspace=workspace,
                            properties_count=len(properties),
                            last_edited=last_edited,
                        )
                    )

                elif response.status_code == 401:
                    print(f"❌ {expected_name}: 401 Unauthorized")
                    print(f"   ID: {clean_db_id[:8]}...")
                    database_infos.append(
                        DatabaseInfo(
                            name=expected_name,
                            id=clean_db_id,
                            id_prefix=clean_db_id[:12],
                            accessible=False,
                            workspace="Unknown",
                            properties_count=0,
                            last_edited="N/A",
                            error="401 Unauthorized - API key invalid or expired",
                        )
                    )
                    self.errors.append(f"{expected_name}: 401 Unauthorized")

                elif response.status_code == 404:
                    print(f"❌ {expected_name}: 404 Not Found")
                    print(f"   ID: {clean_db_id[:8]}...")
                    database_infos.append(
                        DatabaseInfo(
                            name=expected_name,
                            id=clean_db_id,
                            id_prefix=clean_db_id[:12],
                            accessible=False,
                            workspace="Unknown",
                            properties_count=0,
                            last_edited="N/A",
                            error="404 Not Found - Database doesn't exist or integration not connected",
                        )
                    )
                    self.errors.append(f"{expected_name}: Not accessible (404)")
                    self.remediation_steps.append(
                        f"Share '{expected_name}' with your integration in Notion:\n"
                        f"   1. Open the database in Notion\n"
                        f"   2. Click '...' menu → 'Add connections'\n"
                        f"   3. Select your integration"
                    )

                else:
                    print(f"❌ {expected_name}: HTTP {response.status_code}")
                    print(f"   ID: {clean_db_id[:8]}...")
                    database_infos.append(
                        DatabaseInfo(
                            name=expected_name,
                            id=clean_db_id,
                            id_prefix=clean_db_id[:12],
                            accessible=False,
                            workspace="Unknown",
                            properties_count=0,
                            last_edited="N/A",
                            error=f"HTTP {response.status_code}",
                        )
                    )
                    self.errors.append(f"{expected_name}: Error {response.status_code}")

            except Exception as e:
                print(f"❌ {expected_name}: Error - {str(e)}")
                database_infos.append(
                    DatabaseInfo(
                        name=expected_name,
                        id=clean_db_id if db_id else "NOT_SET",
                        id_prefix=clean_db_id[:12] if db_id else "N/A",
                        accessible=False,
                        workspace="Unknown",
                        properties_count=0,
                        last_edited="N/A",
                        error=str(e),
                    )
                )
                self.errors.append(f"{expected_name}: {str(e)}")

        print()
        return database_infos

    def print_access_table(self, database_infos: list[DatabaseInfo]):
        """
        Print a formatted table of database access status.

        Args:
            database_infos: List of database information
        """
        print("=" * 80)
        print("📊 DATABASE ACCESS SUMMARY")
        print("=" * 80)
        print()

        # Print table header
        print(
            f"{'Database Name':<35} {'ID Prefix':<15} {'Access':<10} {'Workspace':<20}"
        )
        print("-" * 80)

        # Print each database
        for db_info in database_infos:
            access_icon = "✅ Yes" if db_info.accessible else "❌ No"
            print(
                f"{db_info.name:<35} {db_info.id_prefix:<15} {access_icon:<10} {db_info.workspace:<20}"
            )
            if db_info.error and not db_info.accessible:
                print(f"{'':>35} Error: {db_info.error}")

        print()

    def print_remediation_steps(self):
        """Print remediation steps if there are errors."""
        if not self.errors:
            return

        print("=" * 80)
        print("🔧 REMEDIATION STEPS")
        print("=" * 80)
        print()
        print("To fix the access issues, follow these steps:")
        print()

        for i, step in enumerate(self.remediation_steps, 1):
            print(f"{i}. {step}")

        print()
        print("General troubleshooting:")
        print(
            "  • Verify your Notion integration at: https://www.notion.so/my-integrations"
        )
        print("  • Ensure each database is shared with your integration:")
        print("    - Open database in Notion")
        print("    - Click '...' → 'Add connections'")
        print("    - Select 'AI Studio Master Automation'")
        print("  • Check that database IDs in .env match the actual databases")
        print("  • Ensure you're using an Internal Integration, not OAuth")
        print()

    def generate_audit_result(
        self,
        env_vars: dict,
        database_infos: list[DatabaseInfo],
        total_dbs: int,
        total_pages: int,
    ) -> AuditResult:
        """
        Generate the complete audit result.

        Args:
            env_vars: Environment variables
            database_infos: Database information list
            total_dbs: Total accessible databases
            total_pages: Total accessible pages

        Returns:
            AuditResult object
        """
        sum(1 for db in database_infos if db.accessible)
        missing = [db.name for db in database_infos if not db.accessible]

        overall_status = "PASS" if len(self.errors) == 0 else "FAIL"

        api_key = env_vars.get("NOTION_API_KEY", "")
        api_key_prefix = api_key[:20] + "..." if api_key else "NOT_SET"

        return AuditResult(
            timestamp=datetime.now().isoformat(),
            overall_status=overall_status,
            api_key_valid=len(self.errors) == 0
            or not any("401" in e for e in self.errors),
            api_key_prefix=api_key_prefix,
            total_accessible_databases=total_dbs,
            total_accessible_pages=total_pages,
            required_databases=[
                {
                    "name": db.name,
                    "accessible": db.accessible,
                    "id_prefix": db.id_prefix,
                    "properties_count": db.properties_count,
                    "error": db.error,
                }
                for db in database_infos
            ],
            accessible_databases=[
                {"name": db.name, "id": db.id_prefix, "properties": db.properties_count}
                for db in database_infos
                if db.accessible
            ],
            missing_databases=missing,
            errors=self.errors,
            warnings=self.warnings,
            remediation_steps=self.remediation_steps,
        )

    def export_to_json(self, audit_result: AuditResult):
        """
        Export audit results to JSON file.

        Args:
            audit_result: The audit result to export
        """
        reports_dir = Path(__file__).parent.parent / "reports"
        reports_dir.mkdir(exist_ok=True)

        output_file = reports_dir / "notion-access-audit.json"

        try:
            with open(output_file, "w") as f:
                json.dump(asdict(audit_result), f, indent=2)
            print(f"📄 Audit results exported to: {output_file}")
        except Exception as e:
            print(f"⚠️  Failed to export JSON: {e}")

    def run_audit(self) -> int:
        """
        Run the complete audit process.

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        # Step 1: Check environment variables
        env_ok, env_vars = self.check_environment_variables()
        if not env_ok:
            print(
                "\n❌ Environment check failed. Please fix the issues above and try again.\n"
            )
            return 1

        # Step 2: Test API connectivity
        api_ok, headers_or_error = self.test_api_connectivity(
            env_vars["NOTION_API_KEY"]
        )
        if not api_ok:
            self.print_remediation_steps()
            return 1

        headers = headers_or_error

        # Step 3: List accessible resources
        accessible_dbs, accessible_pages = self.list_accessible_resources(headers)

        # Step 4: Verify required databases
        database_infos = self.verify_required_databases(
            headers, env_vars, accessible_dbs
        )

        # Print summary table
        self.print_access_table(database_infos)

        # Generate audit result
        audit_result = self.generate_audit_result(
            env_vars, database_infos, len(accessible_dbs), len(accessible_pages)
        )

        # Export to JSON if requested
        if self.export_json:
            self.export_to_json(audit_result)

        # Print remediation if needed
        if self.errors:
            self.print_remediation_steps()
            print("=" * 80)
            print("❌ AUDIT FAILED")
            print("=" * 80)
            print(
                f"Found {len(self.errors)} error(s) and {len(self.warnings)} warning(s)"
            )
            print("Please follow the remediation steps above to fix the issues.")
            print("=" * 80)
            return 1
        else:
            print("=" * 80)
            print("✅ AUDIT PASSED")
            print("=" * 80)
            print("All required databases are accessible!")
            print(
                f"Total accessible resources: {len(accessible_dbs)} databases, {len(accessible_pages)} pages"
            )

            if self.warnings:
                print(
                    f"\n⚠️  {len(self.warnings)} warning(s) - these are optional issues"
                )

            print()
            print("Next steps:")
            print(
                "  1. Run full sanity check: python scripts/notion_cli.py sanity-check"
            )
            print(
                "  2. Test sync (dry-run): python scripts/notion_cli.py sync --all --dry-run"
            )
            print("  3. Run live sync: python scripts/notion_cli.py sync --all")
            print("=" * 80)

            # Auto-run sanity check if requested
            if self.auto_fix:
                print("\n🚀 Running sanity check automatically...\n")
                try:
                    from scripts.sanity_check_notion import main as sanity_check_main

                    return sanity_check_main()
                except Exception as e:
                    print(f"⚠️  Auto-run failed: {e}")
                    print(
                        "Please run manually: python scripts/notion_cli.py sanity-check"
                    )
                    return 0

            return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Stage 7.3.1 - Notion Access Audit Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run basic audit
  python scripts/audit_notion_access.py

  # Export results to JSON
  python scripts/audit_notion_access.py --json

  # Audit and auto-run sanity check if successful
  python scripts/audit_notion_access.py --auto-fix

This script helps diagnose 401 Unauthorized errors and database access issues.
        """,
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Export audit results to reports/notion-access-audit.json",
    )
    parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="Automatically run sanity check if audit passes",
    )

    args = parser.parse_args()

    try:
        auditor = NotionAccessAuditor(export_json=args.json, auto_fix=args.auto_fix)
        return auditor.run_audit()
    except KeyboardInterrupt:
        print("\n⚠️  Audit interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Fatal error during audit: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
