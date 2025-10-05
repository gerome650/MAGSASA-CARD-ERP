#!/usr/bin/env python3
"""
Stage 7.3.1 Weekly Notion Sync - Master Orchestrator

This script coordinates all weekly Notion sync operations across:
- CI Intelligence Reports → Notion CI Reports DB
- Roadmap Milestones → Roadmap DB
- AI Studio Strategic Milestones → Milestones DB
- Project Metrics/KPIs rollups → Dashboard properties

Features:
- Dry-run mode for safe testing
- JSON logging for CI/CD integration
- Selective sync (individual streams or all)
- Control Center summary updates
- Comprehensive error handling

Usage:
    # Sync everything
    python scripts/notion_weekly_sync.py --all

    # Dry-run mode (no writes)
    python scripts/notion_weekly_sync.py --all --dry-run

    # Sync specific streams
    python scripts/notion_weekly_sync.py --ci --roadmap

    # With JSON logging
    python scripts/notion_weekly_sync.py --all --log-json
"""

import argparse
import json
import logging
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.notion_client import NotionClient


@dataclass
class SyncResult:
    """Result from a sync operation."""

    component: str
    status: str  # success, failure, skipped
    records_synced: int
    errors: list[str]
    duration_seconds: float
    timestamp: str


class WeeklySyncOrchestrator:
    """Orchestrates all weekly Notion sync operations."""

    def __init__(self, dry_run: bool = False, log_json: bool = False):
        """
        Initialize the sync orchestrator.

        Args:
            dry_run: If True, skip actual writes to Notion
            log_json: If True, output structured JSON logs
        """
        self.dry_run = dry_run
        self.log_json = log_json
        self.results: list[SyncResult] = []

        # Setup logging
        log_level = logging.INFO
        logging.basicConfig(
            level=log_level,
            format=(
                "%(message)s"
                if log_json
                else "%(asctime)s - %(levelname)s - %(message)s"
            ),
        )
        self.logger = logging.getLogger(__name__)

        # Initialize Notion client
        try:
            self.notion_client = NotionClient()
            self.log_event("init", "success", "Notion client initialized")
        except Exception as e:
            self.log_event(
                "init", "failure", f"Failed to initialize Notion client: {e}"
            )
            raise

        # Load configuration
        self.config = self._load_config()
        self._validate_config()

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from environment variables."""
        config = {
            "magsasa_ci_db_id": os.getenv("MAGSASA_CI_DB_ID", ""),
            "magsasa_roadmap_db_id": os.getenv("MAGSASA_ROADMAP_DB_ID", ""),
            "ai_studio_milestones_db_id": os.getenv("AI_STUDIO_MILESTONES_DB_ID", ""),
            "control_center_page_id": os.getenv("CONTROL_CENTER_PAGE_ID", ""),
            "github_token": os.getenv("GITHUB_TOKEN", ""),
            "github_repository": os.getenv("GITHUB_REPOSITORY", ""),
            "github_run_id": os.getenv("GITHUB_RUN_ID", ""),
        }
        return config

    def _validate_config(self):
        """Validate required configuration."""
        required = {
            "magsasa_ci_db_id": "MAGSASA_CI_DB_ID",
            "magsasa_roadmap_db_id": "MAGSASA_ROADMAP_DB_ID",
            "ai_studio_milestones_db_id": "AI_STUDIO_MILESTONES_DB_ID",
        }

        missing = []
        for key, env_var in required.items():
            if not self.config.get(key):
                missing.append(env_var)

        if missing:
            error_msg = (
                f"❌ Missing required environment variables: {', '.join(missing)}"
            )
            self.logger.error(error_msg)
            self.log_event("validation", "failure", error_msg)
            raise ValueError(error_msg)

        self.log_event("validation", "success", "Configuration validated")

    def log_event(self, component: str, status: str, message: str, **kwargs):
        """
        Log an event in JSON or text format.

        Args:
            component: Component name (e.g., 'ci_sync', 'roadmap_sync')
            status: Status (success, failure, warning)
            message: Log message
            **kwargs: Additional structured data
        """
        if self.log_json:
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "component": component,
                "status": status,
                "message": message,
                **kwargs,
            }
            print(json.dumps(log_data))
        else:
            icon = {"success": "✅", "failure": "❌", "warning": "⚠️", "info": "ℹ️"}.get(
                status, ""
            )
            self.logger.info(f"{icon} [{component}] {message}")

    def sync_ci_reports(self) -> SyncResult:
        """Sync CI intelligence reports to Notion."""
        start_time = datetime.utcnow()
        component = "ci_sync"

        try:
            self.log_event(component, "info", "Starting CI reports sync...")

            # Import and run CI sync
            from scripts.sync_ci_weekly import sync_ci_reports

            result = sync_ci_reports(
                self.notion_client,
                self.config["magsasa_ci_db_id"],
                dry_run=self.dry_run,
            )

            duration = (datetime.utcnow() - start_time).total_seconds()
            sync_result = SyncResult(
                component=component,
                status="success",
                records_synced=result.get("records_synced", 0),
                errors=[],
                duration_seconds=duration,
                timestamp=datetime.utcnow().isoformat(),
            )

            self.log_event(
                component,
                "success",
                f"Synced {sync_result.records_synced} CI report(s)",
                duration=duration,
            )
            return sync_result

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            error_msg = str(e)
            self.log_event(
                component, "failure", f"Failed: {error_msg}", duration=duration
            )

            return SyncResult(
                component=component,
                status="failure",
                records_synced=0,
                errors=[error_msg],
                duration_seconds=duration,
                timestamp=datetime.utcnow().isoformat(),
            )

    def sync_roadmap(self) -> SyncResult:
        """Sync roadmap milestones to Notion."""
        start_time = datetime.utcnow()
        component = "roadmap_sync"

        try:
            self.log_event(component, "info", "Starting roadmap sync...")

            # Import and run roadmap sync
            from scripts.sync_roadmap_weekly import sync_roadmap

            result = sync_roadmap(
                self.notion_client,
                self.config["magsasa_roadmap_db_id"],
                dry_run=self.dry_run,
            )

            duration = (datetime.utcnow() - start_time).total_seconds()
            sync_result = SyncResult(
                component=component,
                status="success",
                records_synced=result.get("records_synced", 0),
                errors=[],
                duration_seconds=duration,
                timestamp=datetime.utcnow().isoformat(),
            )

            self.log_event(
                component,
                "success",
                f"Synced {sync_result.records_synced} roadmap item(s)",
                duration=duration,
            )
            return sync_result

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            error_msg = str(e)
            self.log_event(
                component, "failure", f"Failed: {error_msg}", duration=duration
            )

            return SyncResult(
                component=component,
                status="failure",
                records_synced=0,
                errors=[error_msg],
                duration_seconds=duration,
                timestamp=datetime.utcnow().isoformat(),
            )

    def sync_milestones(self) -> SyncResult:
        """Sync AI Studio milestones to Notion."""
        start_time = datetime.utcnow()
        component = "milestones_sync"

        try:
            self.log_event(component, "info", "Starting milestones sync...")

            # Import and run milestones sync
            from scripts.sync_milestones_weekly import sync_milestones

            result = sync_milestones(
                self.notion_client,
                self.config["ai_studio_milestones_db_id"],
                dry_run=self.dry_run,
            )

            duration = (datetime.utcnow() - start_time).total_seconds()
            sync_result = SyncResult(
                component=component,
                status="success",
                records_synced=result.get("records_synced", 0),
                errors=[],
                duration_seconds=duration,
                timestamp=datetime.utcnow().isoformat(),
            )

            self.log_event(
                component,
                "success",
                f"Synced {sync_result.records_synced} milestone(s)",
                duration=duration,
            )
            return sync_result

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            error_msg = str(e)
            self.log_event(
                component, "failure", f"Failed: {error_msg}", duration=duration
            )

            return SyncResult(
                component=component,
                status="failure",
                records_synced=0,
                errors=[error_msg],
                duration_seconds=duration,
                timestamp=datetime.utcnow().isoformat(),
            )

    def sync_kpis(self) -> SyncResult:
        """Sync project KPIs to Notion."""
        start_time = datetime.utcnow()
        component = "kpis_sync"

        try:
            self.log_event(component, "info", "Starting KPIs sync...")

            # Import and run KPIs sync
            from scripts.sync_kpis_weekly import sync_kpis

            result = sync_kpis(
                self.notion_client,
                self.config["magsasa_ci_db_id"],  # Use CI DB for summary row
                dry_run=self.dry_run,
            )

            duration = (datetime.utcnow() - start_time).total_seconds()
            sync_result = SyncResult(
                component=component,
                status="success",
                records_synced=result.get("records_synced", 0),
                errors=[],
                duration_seconds=duration,
                timestamp=datetime.utcnow().isoformat(),
            )

            self.log_event(
                component,
                "success",
                f"Synced {sync_result.records_synced} KPI record(s)",
                duration=duration,
            )
            return sync_result

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            error_msg = str(e)
            self.log_event(
                component, "failure", f"Failed: {error_msg}", duration=duration
            )

            return SyncResult(
                component=component,
                status="failure",
                records_synced=0,
                errors=[error_msg],
                duration_seconds=duration,
                timestamp=datetime.utcnow().isoformat(),
            )

    def generate_summary(self) -> dict[str, Any]:
        """Generate a summary of all sync operations."""
        total_records = sum(r.records_synced for r in self.results)
        total_duration = sum(r.duration_seconds for r in self.results)

        successful = [r for r in self.results if r.status == "success"]
        failed = [r for r in self.results if r.status == "failure"]

        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "dry_run": self.dry_run,
            "total_components": len(self.results),
            "successful": len(successful),
            "failed": len(failed),
            "total_records_synced": total_records,
            "total_duration_seconds": round(total_duration, 2),
            "components": [asdict(r) for r in self.results],
        }

        return summary

    def write_summary_to_control_center(self, summary: dict[str, Any]):
        """Write sync summary to Control Center page."""
        if not self.config.get("control_center_page_id"):
            self.log_event(
                "control_center", "info", "No Control Center page configured, skipping"
            )
            return

        if self.dry_run:
            self.log_event(
                "control_center",
                "info",
                "Dry-run: Would write summary to Control Center",
            )
            return

        try:
            # Format summary as markdown
            status_icon = "✅" if summary["failed"] == 0 else "⚠️"
            summary_text = f"""
## {status_icon} Weekly Notion Sync - {datetime.utcnow().strftime('%Y-%m-%d')}

**Status**: {'Success' if summary['failed'] == 0 else f"{summary['failed']} component(s) failed"}
**Duration**: {summary['total_duration_seconds']:.2f}s
**Records Synced**: {summary['total_records_synced']}

### Component Results
"""

            for component in summary["components"]:
                icon = "✅" if component["status"] == "success" else "❌"
                summary_text += f"- {icon} **{component['component']}**: {component['records_synced']} records ({component['duration_seconds']:.2f}s)\n"

            if summary["failed"] > 0:
                summary_text += "\n### Errors\n"
                for component in summary["components"]:
                    if component["errors"]:
                        summary_text += f"**{component['component']}**:\n"
                        for error in component["errors"]:
                            summary_text += f"  - {error}\n"

            # Note: Actual block append would require page block API
            # For now, we log that we would write it
            self.log_event(
                "control_center", "success", "Summary prepared for Control Center"
            )

        except Exception as e:
            self.log_event("control_center", "failure", f"Failed to write summary: {e}")

    def save_logs(self, summary: dict[str, Any]):
        """Save sync logs to reports directory."""
        reports_dir = Path(__file__).parent.parent / "reports"
        reports_dir.mkdir(exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        log_file = reports_dir / f"notion-weekly-sync-{timestamp}.json"

        try:
            with open(log_file, "w") as f:
                json.dump(summary, f, indent=2)

            self.log_event("logging", "success", f"Logs saved to {log_file}")
        except Exception as e:
            self.log_event("logging", "failure", f"Failed to save logs: {e}")

    def run(self, streams: list[str]) -> int:
        """
        Run the weekly sync for specified streams.

        Args:
            streams: List of stream names to sync ('ci', 'roadmap', 'milestones', 'kpis', 'all')

        Returns:
            Exit code (0 for success, 1 for any failures)
        """
        if self.dry_run:
            self.log_event(
                "orchestrator",
                "warning",
                "🔸 Running in DRY-RUN mode - no writes will be performed",
            )

        self.log_event(
            "orchestrator",
            "info",
            f"Starting weekly sync for streams: {', '.join(streams)}",
        )

        # Expand 'all' to individual streams
        if "all" in streams:
            streams = ["ci", "roadmap", "milestones", "kpis"]

        # Run each stream sync
        if "ci" in streams:
            self.results.append(self.sync_ci_reports())

        if "roadmap" in streams:
            self.results.append(self.sync_roadmap())

        if "milestones" in streams:
            self.results.append(self.sync_milestones())

        if "kpis" in streams:
            self.results.append(self.sync_kpis())

        # Generate and save summary
        summary = self.generate_summary()
        self.save_logs(summary)
        self.write_summary_to_control_center(summary)

        # Report final status
        if summary["failed"] == 0:
            self.log_event(
                "orchestrator",
                "success",
                f"✅ All {summary['successful']} component(s) synced successfully",
            )
            return 0
        else:
            self.log_event(
                "orchestrator",
                "failure",
                f"❌ {summary['failed']} component(s) failed, {summary['successful']} succeeded",
            )
            return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Stage 7.3.1 Weekly Notion Sync Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sync everything
  python scripts/notion_weekly_sync.py --all

  # Dry-run mode (no writes)
  python scripts/notion_weekly_sync.py --all --dry-run

  # Sync specific streams
  python scripts/notion_weekly_sync.py --ci --roadmap

  # With JSON logging for CI/CD
  python scripts/notion_weekly_sync.py --all --log-json
        """,
    )

    # Sync target flags
    parser.add_argument("--all", action="store_true", help="Sync all streams (default)")
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

    args = parser.parse_args()

    # Determine which streams to sync
    streams = []
    if args.all or not any([args.ci, args.roadmap, args.milestones, args.kpis]):
        streams = ["all"]
    else:
        if args.ci:
            streams.append("ci")
        if args.roadmap:
            streams.append("roadmap")
        if args.milestones:
            streams.append("milestones")
        if args.kpis:
            streams.append("kpis")

    # Run orchestrator
    try:
        orchestrator = WeeklySyncOrchestrator(
            dry_run=args.dry_run, log_json=args.log_json
        )
        exit_code = orchestrator.run(streams)
        sys.exit(exit_code)
    except Exception as e:
        print(f"❌ Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
