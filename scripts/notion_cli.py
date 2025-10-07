#!/usr/bin/env python3
"""
Stage 7.3.1 - Unified Notion CLI Entry Point

Provides a single command-line interface for all Notion integration operations:
- sanity-check: Full connection + schema + dry-run validation
- validate: Schema validation only
- sync: Live sync operations with various options

Usage:
    python scripts/notion_cli.py sanity-check
    python scripts/notion_cli.py validate
    python scripts/notion_cli.py sync --all
    python scripts/notion_cli.py sync --ci --roadmap --dry-run
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_sanity_check(args):
    """Run the comprehensive sanity check."""
    from scripts.sanity_check_notion import main as sanity_check_main

    # Convert args to sys.argv format for sanity_check_main
    original_argv = sys.argv[:]
    sys.argv = ["sanity_check_notion.py"]

    if args.dry_run:
        sys.argv.append("--dry-run")

    try:
        return sanity_check_main()
    finally:
        sys.argv = original_argv


def run_validate(_args):
    """Run schema validation only."""
    from scripts.sanity_check_notion import main as sanity_check_main

    # Convert args to sys.argv format for sanity_check_main
    original_argv = sys.argv[:]
    sys.argv = ["sanity_check_notion.py", "--validate-only"]

    try:
        return sanity_check_main()
    finally:
        sys.argv = original_argv


def run_sync(args):
    """Run the weekly sync orchestrator."""
    from scripts.notion_weekly_sync import main as sync_main

    # Convert args to sys.argv format for sync_main
    original_argv = sys.argv[:]
    sys.argv = ["notion_weekly_sync.py"]

    # Add sync target flags
    if args.all:
        sys.argv.append("--all")
    if args.ci:
        sys.argv.append("--ci")
    if args.roadmap:
        sys.argv.append("--roadmap")
    if args.milestones:
        sys.argv.append("--milestones")
    if args.kpis:
        sys.argv.append("--kpis")

    # Add options
    if args.dry_run:
        sys.argv.append("--dry-run")
    if args.log_json:
        sys.argv.append("--log-json")

    try:
        return sync_main()
    finally:
        sys.argv = original_argv


def create_sanity_check_parser():
    """Create parser for sanity-check command."""
    parser = argparse.ArgumentParser(
        description="Run comprehensive Notion integration sanity check",
        add_help=False,  # We'll handle help manually
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Include dry-run sync simulation"
    )
    return parser


def create_validate_parser():
    """Create parser for validate command."""
    parser = argparse.ArgumentParser(
        description="Validate Notion database schemas only", add_help=False
    )
    return parser


def create_sync_parser():
    """Create parser for sync command."""
    parser = argparse.ArgumentParser(
        description="Run Notion sync operations", add_help=False
    )

    # Sync target flags
    parser.add_argument("--all", action="store_true", help="Sync all streams")
    parser.add_argument(
        "--ci", action="store_true", help="Sync CI intelligence reports"
    )
    parser.add_argument(
        "--roadmap", action="store_true", help="Sync roadmap milestones"
    )
    parser.add_argument(
        "--milestones", action="store_true", help="Sync AI Studio milestones"
    )
    parser.add_argument("--kpis", action="store_true", help="Sync project KPIs")

    # Options
    parser.add_argument(
        "--dry-run", action="store_true", help="Run without writing to Notion"
    )
    parser.add_argument(
        "--log-json", action="store_true", help="Output structured JSON logs"
    )

    return parser


def print_help():
    """Print comprehensive help message."""
    help_text = """
Stage 7.3.1 - Unified Notion CLI

This CLI provides a single entry point for all Notion integration operations.

COMMANDS:
  sanity-check    Run comprehensive connection + schema + dry-run validation
  validate        Validate database schemas only
  sync            Run live sync operations

EXAMPLES:

  # Full sanity check (recommended first run)
  python scripts/notion_cli.py sanity-check

  # Include dry-run sync simulation
  python scripts/notion_cli.py sanity-check --dry-run

  # Schema validation only
  python scripts/notion_cli.py validate

  # Sync everything
  python scripts/notion_cli.py sync --all

  # Sync specific streams with dry-run
  python scripts/notion_cli.py sync --ci --roadmap --dry-run

  # Sync with JSON logging for CI/CD
  python scripts/notion_cli.py sync --all --log-json

COMMAND DETAILS:

sanity-check:
  Performs comprehensive validation:
  ✅ Environment variable validation
  ✅ Notion API connectivity testing
  ✅ Database access verification
  ✅ Schema property validation
  ✅ Optional dry-run sync simulation

  Options:
    --dry-run    Include dry-run sync simulation

validate:
  Quick schema validation only:
  ✅ Validates all database schemas
  ✅ Checks required properties exist
  ✅ Verifies property types match expectations

sync:
  Live sync operations:
  ✅ CI Intelligence Reports → Notion CI Reports DB
  ✅ Roadmap Milestones → Roadmap DB
  ✅ AI Studio Strategic Milestones → Milestones DB
  ✅ Project Metrics/KPIs rollups → Dashboard properties

  Target options:
    --all        Sync all streams (default)
    --ci         Sync CI intelligence reports
    --roadmap    Sync roadmap milestones
    --milestones Sync AI Studio milestones
    --kpis       Sync project KPIs

  General options:
    --dry-run    Run without writing to Notion
    --log-json   Output structured JSON logs for CI/CD

ENVIRONMENT SETUP:

Before using this CLI, ensure your .env file contains:
  NOTION_API_KEY=secret_ntn_...
  MAGSASA_CI_DB_ID=2822dea9...
  MAGSASA_ROADMAP_DB_ID=2822dea9...
  AI_STUDIO_MILESTONES_DB_ID=27d2dea9...
  CONTROL_CENTER_PAGE_ID=2822dea9... (optional)

TROUBLESHOOTING:

1. First time setup:
   python scripts/notion_cli.py sanity-check

2. Schema issues:
   python scripts/notion_cli.py validate

3. Test sync without writes:
   python scripts/notion_cli.py sync --all --dry-run

4. Live sync:
   python scripts/notion_cli.py sync --all

For more help on a specific command:
  python scripts/notion_cli.py <command> --help
"""
    print(help_text)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print_help()
        return 0

    command = sys.argv[1]
    remaining_args = sys.argv[2:]

    # Handle help requests
    if command in ["-h", "--help", "help"]:
        print_help()
        return 0

    try:
        if command == "sanity-check":
            parser = create_sanity_check_parser()
            args = parser.parse_args(remaining_args)
            return run_sanity_check(args)

        elif command == "validate":
            parser = create_validate_parser()
            args = parser.parse_args(remaining_args)
            return run_validate(args)

        elif command == "sync":
            parser = create_sync_parser()
            args = parser.parse_args(remaining_args)
            return run_sync(args)

        else:
            print(f"❌ Unknown command: {command}")
            print("\nAvailable commands: sanity-check, validate, sync")
            print("Run 'python scripts/notion_cli.py --help' for detailed usage")
            return 1

    except SystemExit as e:
        # argparse raises SystemExit for help/errors, we want to preserve the exit code from None
        return e.code if e.code is not None else 0
    except KeyboardInterrupt:
        print("\n⚠️ Operation interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Error running {command}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
