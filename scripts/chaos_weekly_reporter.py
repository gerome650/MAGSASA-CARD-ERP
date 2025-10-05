#!/usr/bin/env python3
"""
Chaos Weekly Reporter - Stage 7.2
Generates weekly intelligence reports on chaos validation health.
"""

import argparse
import json
import logging
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path


class ChaosWeeklyReporter:
    """Generate weekly chaos validation health reports."""

    def __init__(
        self, db_path: str = "reports/chaos_history.db", lookback_days: int = 7
    ):
        self.db_path = db_path
        self.lookback_days = lookback_days
        self.logger = self._setup_logging()
        self._init_database()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s"
        )
        return logging.getLogger(__name__)

    def _init_database(self):
        """Initialize SQLite database for storing chaos history."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create tables if they don't exist
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chaos_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                status TEXT NOT NULL,
                total_scenarios INTEGER,
                successful_scenarios INTEGER,
                failed_scenarios INTEGER,
                duration_seconds REAL
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chaos_failures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER,
                timestamp TEXT NOT NULL,
                category TEXT NOT NULL,
                message TEXT,
                fixed BOOLEAN DEFAULT 0,
                FOREIGN KEY(run_id) REFERENCES chaos_runs(id)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS dependency_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                package_name TEXT NOT NULL,
                version TEXT,
                action TEXT NOT NULL
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS healing_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                failure_category TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                details TEXT
            )
        """
        )

        conn.commit()
        conn.close()

        self.logger.debug(f"Database initialized: {self.db_path}")

    def record_chaos_run(
        self, status: str, total: int, successful: int, failed: int, duration: float
    ):
        """Record a chaos validation run."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO chaos_runs (timestamp, status, total_scenarios,
                                  successful_scenarios, failed_scenarios, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (datetime.now().isoformat(), status, total, successful, failed, duration),
        )

        conn.commit()
        run_id = cursor.lastrowid
        conn.close()

        return run_id

    def record_failure(
        self, run_id: int, category: str, message: str, fixed: bool = False
    ):
        """Record a chaos validation failure."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO chaos_failures (run_id, timestamp, category, message, fixed)
            VALUES (?, ?, ?, ?, ?)
        """,
            (run_id, datetime.now().isoformat(), category, message, fixed),
        )

        conn.commit()
        conn.close()

    def record_dependency_change(self, package_name: str, version: str, action: str):
        """Record a dependency change (add/update/remove)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO dependency_changes (timestamp, package_name, version, action)
            VALUES (?, ?, ?, ?)
        """,
            (datetime.now().isoformat(), package_name, version, action),
        )

        conn.commit()
        conn.close()

    def record_healing_attempt(self, category: str, success: bool, details: str = ""):
        """Record an auto-healing attempt."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO healing_attempts (timestamp, failure_category, success, details)
            VALUES (?, ?, ?, ?)
        """,
            (datetime.now().isoformat(), category, success, details),
        )

        conn.commit()
        conn.close()

    def get_runs_in_period(self) -> list[dict]:
        """Get all chaos runs in the lookback period."""
        cutoff_date = (datetime.now() - timedelta(days=self.lookback_days)).isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, timestamp, status, total_scenarios, successful_scenarios,
                   failed_scenarios, duration_seconds
            FROM chaos_runs
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        """,
            (cutoff_date,),
        )

        runs = []
        for row in cursor.fetchall():
            runs.append(
                {
                    "id": row[0],
                    "timestamp": row[1],
                    "status": row[2],
                    "total_scenarios": row[3],
                    "successful_scenarios": row[4],
                    "failed_scenarios": row[5],
                    "duration_seconds": row[6],
                }
            )

        conn.close()
        return runs

    def get_failures_in_period(self) -> list[dict]:
        """Get all failures in the lookback period."""
        cutoff_date = (datetime.now() - timedelta(days=self.lookback_days)).isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, run_id, timestamp, category, message, fixed
            FROM chaos_failures
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        """,
            (cutoff_date,),
        )

        failures = []
        for row in cursor.fetchall():
            failures.append(
                {
                    "id": row[0],
                    "run_id": row[1],
                    "timestamp": row[2],
                    "category": row[3],
                    "message": row[4],
                    "fixed": bool(row[5]),
                }
            )

        conn.close()
        return failures

    def get_dependency_changes_in_period(self) -> list[dict]:
        """Get all dependency changes in the lookback period."""
        cutoff_date = (datetime.now() - timedelta(days=self.lookback_days)).isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT timestamp, package_name, version, action
            FROM dependency_changes
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        """,
            (cutoff_date,),
        )

        changes = []
        for row in cursor.fetchall():
            changes.append(
                {
                    "timestamp": row[0],
                    "package_name": row[1],
                    "version": row[2],
                    "action": row[3],
                }
            )

        conn.close()
        return changes

    def get_healing_attempts_in_period(self) -> list[dict]:
        """Get all healing attempts in the lookback period."""
        cutoff_date = (datetime.now() - timedelta(days=self.lookback_days)).isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT timestamp, failure_category, success, details
            FROM healing_attempts
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        """,
            (cutoff_date,),
        )

        attempts = []
        for row in cursor.fetchall():
            attempts.append(
                {
                    "timestamp": row[0],
                    "failure_category": row[1],
                    "success": bool(row[2]),
                    "details": row[3],
                }
            )

        conn.close()
        return attempts

    def calculate_metrics(
        self, runs: list[dict], failures: list[dict], healing_attempts: list[dict]
    ) -> dict:
        """Calculate key metrics for the report."""
        metrics = {
            "total_runs": len(runs),
            "successful_runs": sum(1 for r in runs if r["status"] == "success"),
            "failed_runs": sum(1 for r in runs if r["status"] == "failed"),
            "success_rate": 0.0,
            "avg_duration": 0.0,
            "total_failures": len(failures),
            "failures_by_category": {},
            "auto_healed_count": sum(1 for f in failures if f["fixed"]),
            "healing_success_rate": 0.0,
            "most_common_failures": [],
        }

        if runs:
            metrics["success_rate"] = (
                metrics["successful_runs"] / metrics["total_runs"]
            ) * 100

            durations = [r["duration_seconds"] for r in runs if r["duration_seconds"]]
            if durations:
                metrics["avg_duration"] = sum(durations) / len(durations)

        # Failures by category
        category_counter = Counter(f["category"] for f in failures)
        metrics["failures_by_category"] = dict(category_counter)

        # Most common failure messages
        message_counter = Counter(f["message"] for f in failures)
        metrics["most_common_failures"] = message_counter.most_common(5)

        # Healing success rate
        if healing_attempts:
            successful_healings = sum(1 for a in healing_attempts if a["success"])
            metrics["healing_success_rate"] = (
                successful_healings / len(healing_attempts)
            ) * 100

        return metrics

    def generate_markdown_report(
        self, output_file: str = "reports/chaos_weekly_report.md"
    ):
        """Generate a markdown report."""
        start_date = datetime.now() - timedelta(days=self.lookback_days)
        end_date = datetime.now()

        # Fetch data
        runs = self.get_runs_in_period()
        failures = self.get_failures_in_period()
        dep_changes = self.get_dependency_changes_in_period()
        healing_attempts = self.get_healing_attempts_in_period()

        # Calculate metrics
        metrics = self.calculate_metrics(runs, failures, healing_attempts)

        # Generate report
        report = f"""# Chaos Validation Weekly Intelligence Report

**Report Period:** {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Lookback Period:** {self.lookback_days} days

## Executive Summary

- **Total Validation Runs:** {metrics['total_runs']}
- **Success Rate:** {metrics['success_rate']:.1f}%
- **Average Duration:** {metrics['avg_duration']:.1f}s
- **Total Failures:** {metrics['total_failures']}
- **Auto-Healed:** {metrics['auto_healed_count']} ({metrics['healing_success_rate']:.1f}% success rate)

## Validation Runs Trend

"""

        if runs:
            report += (
                "| Timestamp | Status | Scenarios | Success | Failed | Duration |\n"
            )
            report += (
                "|-----------|--------|-----------|---------|--------|----------|\n"
            )
            for run in runs[:10]:  # Show last 10 runs
                report += f"| {run['timestamp'][:19]} | {run['status']} | {run['total_scenarios']} | {run['successful_scenarios']} | {run['failed_scenarios']} | {run['duration_seconds']:.1f}s |\n"
        else:
            report += "*No validation runs in this period*\n"

        report += "\n## Failure Analysis\n\n"

        if failures:
            report += "### Failures by Category\n\n"
            for category, count in metrics["failures_by_category"].items():
                percentage = (count / metrics["total_failures"]) * 100
                report += f"- **{category}**: {count} ({percentage:.1f}%)\n"

            report += "\n### Most Common Failures\n\n"
            for message, count in metrics["most_common_failures"]:
                report += f"- `{message[:100]}...` ({count} occurrences)\n"
        else:
            report += "✅ **No failures detected in this period!**\n"

        report += "\n## Auto-Healing Performance\n\n"

        if healing_attempts:
            report += f"**Total Healing Attempts:** {len(healing_attempts)}  \n"
            report += f"**Success Rate:** {metrics['healing_success_rate']:.1f}%  \n\n"

            # Group by category
            healing_by_category = defaultdict(list)
            for attempt in healing_attempts:
                healing_by_category[attempt["failure_category"]].append(attempt)

            report += "### Healing by Category\n\n"
            for category, attempts in healing_by_category.items():
                successes = sum(1 for a in attempts if a["success"])
                success_rate = (successes / len(attempts)) * 100
                report += f"- **{category}**: {successes}/{len(attempts)} ({success_rate:.1f}%)\n"
        else:
            report += "*No auto-healing attempts in this period*\n"

        report += "\n## Dependency Changes\n\n"

        if dep_changes:
            report += "| Timestamp | Package | Version | Action |\n"
            report += "|-----------|---------|---------|--------|\n"
            for change in dep_changes:
                report += f"| {change['timestamp'][:19]} | {change['package_name']} | {change['version']} | {change['action']} |\n"
        else:
            report += "*No dependency changes in this period*\n"

        report += "\n## Recommendations\n\n"

        # Generate recommendations based on data
        if metrics["success_rate"] < 80:
            report += "### 🚨 Critical\n\n"
            report += f"- Success rate ({metrics['success_rate']:.1f}%) is below 80%. Investigate recurring failures.\n"

        if metrics["failures_by_category"].get("dependency", 0) > 0:
            report += (
                "- **Dependency issues detected.** Run dependency sentinel regularly.\n"
            )

        if metrics["failures_by_category"].get("health_check", 0) > 0:
            report += "- **Health check failures detected.** Consider increasing startup wait time.\n"

        if metrics["healing_success_rate"] < 50 and healing_attempts:
            report += "- **Low healing success rate.** Review auto-healing logic.\n"

        if not dep_changes:
            report += "- ✅ No dependency churn - system is stable.\n"

        if metrics["success_rate"] >= 95:
            report += "### ✅ Excellent\n\n"
            report += f"- High success rate ({metrics['success_rate']:.1f}%). System is very stable.\n"

        report += "\n## Next Steps\n\n"
        report += "1. Review failed scenarios and fix root causes\n"
        report += "2. Update chaos scenarios if needed\n"
        report += "3. Monitor dependency changes\n"
        report += "4. Enhance auto-healing logic for common failures\n"

        report += "\n---\n\n"
        report += (
            "*This report is automatically generated by the Chaos Weekly Reporter*\n"
        )

        # Save report
        try:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w") as f:
                f.write(report)
            self.logger.info(f"📄 Weekly report saved to: {output_file}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save report: {e}")
            return False

    def import_from_json(self, json_file: str) -> bool:
        """Import chaos run data from JSON file."""
        try:
            with open(json_file) as f:
                data = json.load(f)

            # Determine data type and import accordingly
            if "total_scenarios" in data:
                # Chaos results
                run_id = self.record_chaos_run(
                    status="success" if data.get("failed", 0) == 0 else "failed",
                    total=data.get("total_scenarios", 0),
                    successful=data.get("successful", 0),
                    failed=data.get("failed", 0),
                    duration=0,  # Not in the JSON
                )
                self.logger.info(f"Imported chaos run (ID: {run_id})")

            elif "attempts" in data:
                # Healing attempts
                for attempt in data.get("attempts", []):
                    self.record_healing_attempt(
                        category=attempt.get("type", "unknown"),
                        success=attempt.get("success", False),
                        details=json.dumps(attempt),
                    )
                self.logger.info(
                    f"Imported {len(data.get('attempts', []))} healing attempts"
                )

            return True

        except Exception as e:
            self.logger.error(f"Failed to import from {json_file}: {e}")
            return False


def main():
    """Main entry point for weekly reporter."""
    parser = argparse.ArgumentParser(
        description="Chaos Weekly Reporter - Generate weekly intelligence reports"
    )
    parser.add_argument(
        "--db",
        type=str,
        default="reports/chaos_history.db",
        help="SQLite database path",
    )
    parser.add_argument(
        "--lookback-days", type=int, default=7, help="Number of days to look back"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="reports/chaos_weekly_report.md",
        help="Output markdown file",
    )
    parser.add_argument("--import-json", type=str, help="Import data from JSON file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print("📊 Chaos Weekly Reporter - Stage 7.2")
    print("=" * 60)

    # Create reporter
    reporter = ChaosWeeklyReporter(db_path=args.db, lookback_days=args.lookback_days)

    # Import data if requested
    if args.import_json:
        print(f"📥 Importing data from {args.import_json}...")
        if reporter.import_from_json(args.import_json):
            print("✅ Import successful")
        else:
            print("❌ Import failed")
            sys.exit(1)

    # Generate report
    print(f"📝 Generating weekly report (last {args.lookback_days} days)...")
    if reporter.generate_markdown_report(args.output):
        print(f"✅ Report generated: {args.output}")
        sys.exit(0)
    else:
        print("❌ Failed to generate report")
        sys.exit(1)


if __name__ == "__main__":
    main()
