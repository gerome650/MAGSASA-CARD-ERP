#!/usr/bin/env python3
"""
Notion Database Setup Script

This script helps set up the required Notion databases for CI Intelligence
and Engineering Roadmap synchronization.

Stage 7.3.2: Notion Intelligence Sync + Roadmap Automation

Usage:
    python scripts/setup_notion_databases.py --create-databases
    python scripts/setup_notion_databases.py --show-schema
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Any

# Import centralized Notion client
sys.path.append(str(Path(__file__).parent.parent))
from utils.notion_client import NotionClient


class NotionDatabaseSetup:
    """Setup helper for Notion databases."""

    def __init__(self, parent_page_id: str):
        """Initialize setup helper."""
        # Use centralized Notion client
        self.notion_client = NotionClient()
        self.parent_page_id = parent_page_id

    def create_database(
        self, title: str, description: str, properties: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a new Notion database."""
        return self.notion_client.create_database(
            parent_page_id=self.parent_page_id,
            title=title,
            description=description,
            properties=properties,
        )

    def get_ci_reports_schema(self) -> dict[str, Any]:
        """Get schema for CI Reports database."""
        return {
            "Report Name": {"title": {}},
            "Report Date": {"date": {}},
            "Analysis Period": {"number": {"format": "number"}},
            "Total Failures": {"number": {"format": "number"}},
            "Auto-fix Success Rate": {"number": {"format": "percent"}},
            "Average MTTR": {"number": {"format": "number"}},
            "Top Failure Category": {"rich_text": {}},
            "Report Content": {"rich_text": {}},
            "GitHub Link": {"url": {}},
            "Created": {"created_time": {}},
            "Last Modified": {"last_edited_time": {}},
        }

    def get_roadmap_schema(self) -> dict[str, Any]:
        """Get schema for Engineering Roadmap database."""
        return {
            "🧩 Milestone": {"title": {}},
            "📆 Target Date": {"date": {}},
            "✅ Status": {
                "select": {
                    "options": [
                        {"name": "Planned", "color": "gray"},
                        {"name": "In Progress", "color": "blue"},
                        {"name": "Blocked", "color": "red"},
                        {"name": "Completed", "color": "green"},
                    ]
                }
            },
            "📊 Progress": {"number": {"format": "percent"}},
            "📎 Latest CI Health": {
                "relation": {
                    "database_id": ""  # Will be set after CI reports DB is created
                }
            },
            "📦 Related PR": {"url": {}},
            "🧪 Workflow Pass Rate": {"number": {"format": "percent"}},
            "🩹 Auto-Fix Success": {"number": {"format": "percent"}},
            "⏱️ MTTR": {"number": {"format": "number"}},
            "📈 Trend": {
                "select": {
                    "options": [
                        {"name": "Improving", "color": "green"},
                        {"name": "Stable", "color": "blue"},
                        {"name": "Degrading", "color": "red"},
                    ]
                }
            },
            "📝 Notes": {"rich_text": {}},
            "Created": {"created_time": {}},
            "Last Modified": {"last_edited_time": {}},
        }

    def create_ci_reports_database(self) -> dict[str, Any]:
        """Create CI Reports database."""
        schema = self.get_ci_reports_schema()

        result = self.create_database(
            title="CI Intelligence Reports",
            description="Weekly CI intelligence reports with failure analysis and auto-fix metrics",
            properties=schema,
        )

        return result

    def create_roadmap_database(self, ci_reports_db_id: str) -> dict[str, Any]:
        """Create Engineering Roadmap database."""
        schema = self.get_roadmap_schema()

        # Update the relation to point to CI reports database
        schema["📎 Latest CI Health"]["relation"]["database_id"] = ci_reports_db_id

        result = self.create_database(
            title="Engineering Roadmap",
            description="Engineering milestones with CI health metrics and progress tracking",
            properties=schema,
        )

        return result

    def show_schema_documentation(self):
        """Show schema documentation for manual database creation."""
        print("# 📊 Notion Database Schemas\n")

        print("## 🔍 CI Intelligence Reports Database\n")
        print(
            "**Purpose:** Store weekly CI intelligence reports with metrics and analysis\n"
        )
        print("**Properties:**\n")

        ci_schema = self.get_ci_reports_schema()
        for prop_name, prop_config in ci_schema.items():
            prop_type = list(prop_config.keys())[0]
            print(f"- **{prop_name}** ({prop_type})")

        print("\n## 🗺️ Engineering Roadmap Database\n")
        print("**Purpose:** Track engineering milestones with CI health metrics\n")
        print("**Properties:**\n")

        roadmap_schema = self.get_roadmap_schema()
        for prop_name, prop_config in roadmap_schema.items():
            prop_type = list(prop_config.keys())[0]
            if prop_type == "select":
                options = prop_config[prop_type].get("options", [])
                option_names = [opt["name"] for opt in options]
                print(f"- **{prop_name}** ({prop_type}: {', '.join(option_names)})")
            elif prop_type == "relation":
                print(
                    f"- **{prop_name}** ({prop_type}: links to CI Intelligence Reports)"
                )
            else:
                print(f"- **{prop_name}** ({prop_type})")

        print("\n## 🚀 Setup Instructions\n")
        print("### Option 1: Automated Setup\n")
        print("```bash")
        print("# Set your Notion API key and parent page ID")
        print("export NOTION_API_KEY='your_notion_api_key'")
        print("export NOTION_PARENT_PAGE_ID='your_parent_page_id'")
        print("")
        print("# Run automated setup")
        print("python scripts/setup_notion_databases.py --create-databases")
        print("```")

        print("\n### Option 2: Manual Setup\n")
        print("1. Create a new page in Notion for your CI Intelligence workspace")
        print("2. Create two databases using the schemas above:")
        print("   - **CI Intelligence Reports**")
        print("   - **Engineering Roadmap**")
        print("3. Set the relation in Roadmap database to link to CI Reports database")
        print("4. Note down the database IDs from the URLs")
        print("5. Copy env.template to .env and set environment variables:")
        print("```bash")
        print("cp env.template .env")
        print("# Edit .env file with your values:")
        print("NOTION_API_KEY=your_notion_api_key")
        print("MAGSASA_CI_DB_ID=ci_reports_database_id")
        print("MAGSASA_ROADMAP_DB_ID=roadmap_database_id")
        print("```")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup Notion databases for CI Intelligence and Roadmap",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show schema documentation for manual setup
  python scripts/setup_notion_databases.py --show-schema

  # Create databases automatically
  python scripts/setup_notion_databases.py --create-databases
        """,
    )

    parser.add_argument(
        "--create-databases", action="store_true", help="Create databases automatically"
    )
    parser.add_argument(
        "--show-schema",
        action="store_true",
        help="Show database schemas for manual setup",
    )
    # Note: API key is now configured via environment variables
    # See env.template for configuration options
    parser.add_argument(
        "--parent-page-id",
        help="Parent page ID for databases (or set NOTION_PARENT_PAGE_ID env var)",
    )

    args = parser.parse_args()

    if args.show_schema:
        setup = NotionDatabaseSetup("", "")
        setup.show_schema_documentation()
        return

    if args.create_databases:
        # Check for API key (required for centralized client)
        if not os.getenv("NOTION_API_KEY"):
            print("❌ Error: NOTION_API_KEY environment variable is required.")
            print("Please copy env.template to .env and set your Notion API key.")
            sys.exit(1)

        parent_page_id = args.parent_page_id or os.getenv("NOTION_PARENT_PAGE_ID")

        if not parent_page_id:
            print(
                "❌ Error: Parent page ID required. Set NOTION_PARENT_PAGE_ID env var or use --parent-page-id"
            )
            sys.exit(1)

        try:
            # Initialize setup helper (now uses centralized client)
            setup = NotionDatabaseSetup(parent_page_id)

            print("🏗️ Creating Notion databases...\n")

            # Create CI Reports database
            print("📊 Creating CI Intelligence Reports database...")
            ci_reports_result = setup.create_ci_reports_database()
            ci_reports_db_id = ci_reports_result["id"]
            print(f"✅ Created: {ci_reports_result['title'][0]['text']['content']}")
            print(f"   Database ID: {ci_reports_db_id}")
            print(f"   URL: {ci_reports_result['url']}\n")

            # Create Roadmap database
            print("🗺️ Creating Engineering Roadmap database...")
            roadmap_result = setup.create_roadmap_database(ci_reports_db_id)
            roadmap_db_id = roadmap_result["id"]
            print(f"✅ Created: {roadmap_result['title'][0]['text']['content']}")
            print(f"   Database ID: {roadmap_db_id}")
            print(f"   URL: {roadmap_result['url']}\n")

            # Show configuration
            print("🔧 Configuration for your environment:")
            print("```bash")
            print("# Add these to your .env file or export them:")
            print(f"export MAGSASA_CI_DB_ID='{ci_reports_db_id}'")
            print(f"export MAGSASA_ROADMAP_DB_ID='{roadmap_db_id}'")
            print("")
            print("# Legacy compatibility (optional):")
            print(f"export NOTION_CI_REPORTS_DB_ID='{ci_reports_db_id}'")
            print(f"export NOTION_ROADMAP_DB_ID='{roadmap_db_id}'")
            print("```")

            print("\n🎉 Setup complete! You can now use the sync script:")
            print("```bash")
            print(
                "python scripts/sync_ci_report_to_notion.py --sync-notion --include-roadmap --milestone 'Stage 7.3'"
            )
            print("```")

        except Exception as e:
            print(f"❌ Error creating databases: {e}")
            sys.exit(1)

    if not any([args.create_databases, args.show_schema]):
        parser.print_help()


if __name__ == "__main__":
    main()
