#!/usr/bin/env python3
"""
CI Health Report Generator

Generates daily CI health reports with:
- Workflow success rate
- Top failing jobs
- Average duration
- Readiness trend analysis

Usage:
    python scripts/ci_health_report.py [--verbose]
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from github import Github
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()


class CIHealthReporter:
    """Generates comprehensive CI health reports."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.github_repo = os.getenv(
            "GITHUB_REPOSITORY", "MAGSASA-CARD-ERP/MAGSASA-CARD-ERP"
        )

        if not self.github_token:
            console.print("[red]❌ GITHUB_TOKEN environment variable not set[/red]")
            sys.exit(1)

        self.github = Github(self.github_token)
        self.repo = self.github.get_repo(self.github_repo)

    def log(self, message: str, level: str = "info"):
        """Log message with appropriate level."""
        if self.verbose or level in ["error", "warning"]:
            if level == "error":
                console.print(f"[red]❌ {message}[/red]")
            elif level == "warning":
                console.print(f"[yellow]⚠️  {message}[/yellow]")
            elif level == "success":
                console.print(f"[green]✅ {message}[/green]")
            else:
                console.print(f"[blue]ℹ️  {message}[/blue]")

    def fetch_workflow_runs(self, days: int = 7) -> list[dict[str, Any]]:
        """Fetch workflow runs from the last N days."""
        self.log(f"Fetching workflow runs from last {days} days...")

        since = datetime.now() - timedelta(days=days)
        runs = []

        try:
            # Get all workflows
            workflows = self.repo.get_workflows()

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Fetching workflow runs...", total=None)

                for workflow in workflows:
                    progress.update(task, description=f"Processing {workflow.name}...")

                    # Get runs for this workflow
                    workflow_runs = workflow.get_runs(created=f">={since.isoformat()}")

                    for run in workflow_runs:
                        run_data = {
                            "id": run.id,
                            "name": run.name,
                            "status": run.status,
                            "conclusion": run.conclusion,
                            "created_at": run.created_at.isoformat(),
                            "updated_at": run.updated_at.isoformat(),
                            "duration": None,
                            "jobs": [],
                        }

                        # Calculate duration
                        if run.created_at and run.updated_at:
                            duration = (run.updated_at - run.created_at).total_seconds()
                            run_data["duration"] = duration

                        # Get job details
                        try:
                            jobs = run.get_jobs()
                            for job in jobs:
                                job_data = {
                                    "name": job.name,
                                    "status": job.status,
                                    "conclusion": job.conclusion,
                                    "duration": None,
                                }

                                if job.started_at and job.completed_at:
                                    job_duration = (
                                        job.completed_at - job.started_at
                                    ).total_seconds()
                                    job_data["duration"] = job_duration

                                run_data["jobs"].append(job_data)
                        except Exception as e:
                            self.log(
                                f"Error fetching jobs for run {run.id}: {e}", "warning"
                            )

                        runs.append(run_data)

            self.log(f"Fetched {len(runs)} workflow runs", "success")
            return runs

        except Exception as e:
            self.log(f"Error fetching workflow runs: {e}", "error")
            return []

    def analyze_runs(self, runs: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze workflow runs and generate statistics."""
        self.log("Analyzing workflow runs...")

        if not runs:
            return {"error": "No workflow runs found"}

        total_runs = len(runs)
        successful_runs = sum(1 for run in runs if run["conclusion"] == "success")
        failed_runs = sum(1 for run in runs if run["conclusion"] == "failure")
        cancelled_runs = sum(1 for run in runs if run["conclusion"] == "cancelled")

        success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0

        # Calculate average duration
        durations = [run["duration"] for run in runs if run["duration"] is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Find top failing jobs
        job_failures = {}
        for run in runs:
            if run["conclusion"] == "failure":
                for job in run["jobs"]:
                    if job["conclusion"] == "failure":
                        job_name = job["name"]
                        job_failures[job_name] = job_failures.get(job_name, 0) + 1

        top_failing_jobs = sorted(
            job_failures.items(), key=lambda x: x[1], reverse=True
        )[:5]

        # Calculate trend (compare last 3 days vs previous 3 days)
        midpoint = len(runs) // 2
        recent_runs = runs[:midpoint] if midpoint > 0 else runs
        older_runs = runs[midpoint:] if midpoint > 0 else []

        recent_success_rate = 0
        older_success_rate = 0

        if recent_runs:
            recent_successful = sum(
                1 for run in recent_runs if run["conclusion"] == "success"
            )
            recent_success_rate = recent_successful / len(recent_runs) * 100

        if older_runs:
            older_successful = sum(
                1 for run in older_runs if run["conclusion"] == "success"
            )
            older_success_rate = older_successful / len(older_runs) * 100

        trend = "improving" if recent_success_rate > older_success_rate else "declining"
        if abs(recent_success_rate - older_success_rate) < 5:
            trend = "stable"

        return {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "cancelled_runs": cancelled_runs,
            "success_rate": round(success_rate, 2),
            "average_duration_minutes": round(avg_duration / 60, 2),
            "top_failing_jobs": top_failing_jobs,
            "trend": trend,
            "recent_success_rate": round(recent_success_rate, 2),
            "older_success_rate": round(older_success_rate, 2),
            "generated_at": datetime.now().isoformat(),
        }

    def generate_markdown_report(self, analysis: dict[str, Any]) -> str:
        """Generate markdown report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        report = f"""# CI Health Report

**Generated:** {timestamp}  
**Repository:** {self.github_repo}

## 📊 Overall Health

| Metric | Value |
|--------|-------|
| **Total Runs (7 days)** | {analysis.get('total_runs', 0)} |
| **Success Rate** | {analysis.get('success_rate', 0)}% |
| **Failed Runs** | {analysis.get('failed_runs', 0)} |
| **Cancelled Runs** | {analysis.get('cancelled_runs', 0)} |
| **Average Duration** | {analysis.get('average_duration_minutes', 0)} minutes |

## 📈 Trend Analysis

- **Trend:** {analysis.get('trend', 'unknown').title()}
- **Recent Success Rate:** {analysis.get('recent_success_rate', 0)}%
- **Previous Success Rate:** {analysis.get('older_success_rate', 0)}%

## 🚨 Top Failing Jobs

"""

        if analysis.get("top_failing_jobs"):
            report += "| Job Name | Failure Count |\n"
            report += "|----------|---------------|\n"
            for job_name, count in analysis["top_failing_jobs"]:
                report += f"| {job_name} | {count} |\n"
        else:
            report += "No failing jobs identified.\n"

        report += """
## 🎯 Recommendations

"""

        success_rate = analysis.get("success_rate", 0)
        if success_rate >= 95:
            report += "✅ **Excellent!** CI health is in great shape with high success rate.\n"
        elif success_rate >= 90:
            report += "✅ **Good!** CI health is acceptable but could be improved.\n"
        elif success_rate >= 80:
            report += (
                "⚠️ **Needs Attention!** CI health is below acceptable thresholds.\n"
            )
        else:
            report += "❌ **Critical!** CI health requires immediate attention.\n"

        if analysis.get("top_failing_jobs"):
            report += "\n**Focus Areas:**\n"
            for job_name, count in analysis["top_failing_jobs"][:3]:
                report += f"- Investigate and fix {job_name} (failed {count} times)\n"

        return report

    def save_reports(self, analysis: dict[str, Any], markdown_report: str):
        """Save reports to files."""
        self.log("Saving reports...")

        # Ensure reports directory exists
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)

        # Save JSON report
        json_path = reports_dir / "ci_health.json"
        with open(json_path, "w") as f:
            json.dump(analysis, f, indent=2)

        # Save Markdown report
        md_path = reports_dir / "ci_health.md"
        with open(md_path, "w") as f:
            f.write(markdown_report)

        self.log(f"Reports saved to {json_path} and {md_path}", "success")

    def display_summary(self, analysis: dict[str, Any]):
        """Display summary in terminal."""
        console.print(
            Panel.fit(
                "[bold blue]📊 CI Health Summary[/bold blue]", border_style="blue"
            )
        )

        summary_table = Table(title="7-Day CI Health Metrics")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="magenta")

        summary_table.add_row("Total Runs", str(analysis.get("total_runs", 0)))
        summary_table.add_row("Success Rate", f"{analysis.get('success_rate', 0)}%")
        summary_table.add_row("Failed Runs", str(analysis.get("failed_runs", 0)))
        summary_table.add_row(
            "Avg Duration", f"{analysis.get('average_duration_minutes', 0)} min"
        )
        summary_table.add_row("Trend", analysis.get("trend", "unknown").title())

        console.print(summary_table)

        if analysis.get("top_failing_jobs"):
            console.print("\n[bold yellow]🚨 Top Failing Jobs:[/bold yellow]")
            for job_name, count in analysis["top_failing_jobs"][:3]:
                console.print(f"  • {job_name}: {count} failures")

    def generate_report(self):
        """Generate and save CI health report."""
        console.print(
            Panel.fit(
                "[bold green]🔍 Generating CI Health Report[/bold green]",
                border_style="green",
            )
        )

        # Fetch and analyze workflow runs
        runs = self.fetch_workflow_runs(days=7)
        if not runs:
            self.log("No workflow runs found for analysis", "warning")
            return

        analysis = self.analyze_runs(runs)
        markdown_report = self.generate_markdown_report(analysis)

        # Save reports
        self.save_reports(analysis, markdown_report)

        # Display summary
        self.display_summary(analysis)

        console.print(
            Panel.fit(
                "[bold green]✅ CI Health Report Generated Successfully[/bold green]",
                border_style="green",
            )
        )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate CI health report")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    reporter = CIHealthReporter(verbose=args.verbose)
    reporter.generate_report()


if __name__ == "__main__":
    main()
