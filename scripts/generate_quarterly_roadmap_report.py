#!/usr/bin/env python3
"""
Quarterly Roadmap Report Generator

This script generates comprehensive quarterly reports combining all milestone
metrics, trends, and progress from the Engineering Roadmap database.

Stage 7.3.2: Advanced Features - Quarterly Reports

Usage:
    python scripts/generate_quarterly_roadmap_report.py --quarter Q4-2024
    python scripts/generate_quarterly_roadmap_report.py --auto-quarter
"""

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


@dataclass
class QuarterlyMetrics:
    """Quarterly metrics for roadmap analysis."""

    quarter: str
    total_milestones: int
    completed_milestones: int
    in_progress_milestones: int
    planned_milestones: int
    blocked_milestones: int
    avg_progress: float
    avg_workflow_pass_rate: float
    avg_auto_fix_success: float
    avg_mttr: float
    improving_trends: int
    stable_trends: int
    degrading_trends: int
    milestones: list[dict[str, Any]]


class QuarterlyReportGenerator:
    """Generates quarterly roadmap reports from Notion data."""

    def __init__(self, notion_api_key: str, roadmap_db_id: str):
        """Initialize the quarterly report generator."""
        self.notion_api_key = notion_api_key
        self.roadmap_db_id = roadmap_db_id
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {notion_api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

    def generate_quarterly_report(self, quarter: str) -> str:
        """Generate a comprehensive quarterly roadmap report."""
        print(f"📊 Generating quarterly report for {quarter}...")

        # Get all milestones
        milestones = self._fetch_all_milestones()

        # Calculate quarterly metrics
        metrics = self._calculate_quarterly_metrics(milestones, quarter)

        # Generate insights
        insights = self._generate_quarterly_insights(metrics)

        # Generate recommendations
        recommendations = self._generate_quarterly_recommendations(metrics)

        # Build markdown report
        report = self._build_quarterly_report(
            quarter, metrics, insights, recommendations
        )

        return report

    def _fetch_all_milestones(self) -> list[dict[str, Any]]:
        """Fetch all milestones from Notion database."""
        try:
            url = f"{self.base_url}/databases/{self.roadmap_db_id}/query"

            all_milestones = []
            has_more = True
            start_cursor = None

            while has_more:
                payload = {"page_size": 100}
                if start_cursor:
                    payload["start_cursor"] = start_cursor

                response = requests.post(url, headers=self.headers, json=payload)
                response.raise_for_status()

                data = response.json()
                all_milestones.extend(data["results"])

                has_more = data["has_more"]
                start_cursor = data.get("next_cursor")

            return all_milestones

        except Exception as e:
            print(f"❌ Error fetching milestones: {e}")
            return []

    def _calculate_quarterly_metrics(
        self, milestones: list[dict], quarter: str
    ) -> QuarterlyMetrics:
        """Calculate quarterly metrics from milestone data."""
        total_milestones = len(milestones)
        completed = 0
        in_progress = 0
        planned = 0
        blocked = 0

        progress_sum = 0
        pass_rate_sum = 0
        auto_fix_sum = 0
        mttr_sum = 0

        improving = 0
        stable = 0
        degrading = 0

        milestone_details = []

        for milestone in milestones:
            props = milestone["properties"]

            # Extract milestone data
            name = self._extract_title(props.get("🧩 Milestone", {}))
            status = self._extract_select_value(props.get("✅ Status", {}))
            progress = props.get("📊 Progress", {}).get("number", 0) or 0
            pass_rate = props.get("🧪 Workflow Pass Rate", {}).get("number", 0) or 0
            auto_fix = props.get("🩹 Auto-Fix Success", {}).get("number", 0) or 0
            mttr = props.get("⏱️ MTTR", {}).get("number", 0) or 0
            trend = self._extract_select_value(props.get("📈 Trend", {}))
            target_date = self._extract_date(props.get("📆 Target Date", {}))

            # Count by status
            if status == "Completed":
                completed += 1
            elif status == "In Progress":
                in_progress += 1
            elif status == "Planned":
                planned += 1
            elif status == "Blocked":
                blocked += 1

            # Sum metrics
            progress_sum += progress
            pass_rate_sum += pass_rate
            auto_fix_sum += auto_fix
            mttr_sum += mttr

            # Count trends
            if trend == "Improving":
                improving += 1
            elif trend == "Stable":
                stable += 1
            elif trend == "Degrading":
                degrading += 1

            milestone_details.append(
                {
                    "name": name,
                    "status": status,
                    "progress": progress,
                    "pass_rate": pass_rate,
                    "auto_fix": auto_fix,
                    "mttr": mttr,
                    "trend": trend,
                    "target_date": target_date,
                }
            )

        # Calculate averages
        avg_progress = (progress_sum / total_milestones) if total_milestones > 0 else 0
        avg_pass_rate = (
            (pass_rate_sum / total_milestones) if total_milestones > 0 else 0
        )
        avg_auto_fix = (auto_fix_sum / total_milestones) if total_milestones > 0 else 0
        avg_mttr = (mttr_sum / total_milestones) if total_milestones > 0 else 0

        return QuarterlyMetrics(
            quarter=quarter,
            total_milestones=total_milestones,
            completed_milestones=completed,
            in_progress_milestones=in_progress,
            planned_milestones=planned,
            blocked_milestones=blocked,
            avg_progress=avg_progress,
            avg_workflow_pass_rate=avg_pass_rate,
            avg_auto_fix_success=avg_auto_fix,
            avg_mttr=avg_mttr,
            improving_trends=improving,
            stable_trends=stable,
            degrading_trends=degrading,
            milestones=milestone_details,
        )

    def _generate_quarterly_insights(self, metrics: QuarterlyMetrics) -> list[str]:
        """Generate insights from quarterly metrics."""
        insights = []

        # Completion rate insight
        completion_rate = (
            (metrics.completed_milestones / metrics.total_milestones * 100)
            if metrics.total_milestones > 0
            else 0
        )
        if completion_rate >= 80:
            insights.append(
                f"🎉 Excellent milestone completion rate: {completion_rate:.0f}% ({metrics.completed_milestones}/{metrics.total_milestones})"
            )
        elif completion_rate >= 60:
            insights.append(
                f"📈 Good milestone completion rate: {completion_rate:.0f}% ({metrics.completed_milestones}/{metrics.total_milestones})"
            )
        else:
            insights.append(
                f"⚠️ Milestone completion rate needs improvement: {completion_rate:.0f}% ({metrics.completed_milestones}/{metrics.total_milestones})"
            )

        # Progress insight
        if metrics.avg_progress >= 80:
            insights.append(
                f"🚀 Strong average progress: {metrics.avg_progress:.0f}% across all milestones"
            )
        elif metrics.avg_progress >= 60:
            insights.append(
                f"📊 Moderate average progress: {metrics.avg_progress:.0f}% - room for acceleration"
            )
        else:
            insights.append(
                f"🔄 Average progress below target: {metrics.avg_progress:.0f}% - focus on execution"
            )

        # CI health insight
        if metrics.avg_workflow_pass_rate >= 90 and metrics.avg_auto_fix_success >= 80:
            insights.append(
                f"✅ Excellent CI health: {metrics.avg_workflow_pass_rate:.0f}% pass rate, {metrics.avg_auto_fix_success:.0f}% auto-fix success"
            )
        elif (
            metrics.avg_workflow_pass_rate >= 80 and metrics.avg_auto_fix_success >= 70
        ):
            insights.append(
                f"📈 Good CI health: {metrics.avg_workflow_pass_rate:.0f}% pass rate, {metrics.avg_auto_fix_success:.0f}% auto-fix success"
            )
        else:
            insights.append(
                f"⚠️ CI health needs attention: {metrics.avg_workflow_pass_rate:.0f}% pass rate, {metrics.avg_auto_fix_success:.0f}% auto-fix success"
            )

        # Trend insight
        if metrics.improving_trends > metrics.degrading_trends:
            insights.append(
                f"📈 Positive trend momentum: {metrics.improving_trends} improving vs {metrics.degrading_trends} degrading"
            )
        elif metrics.degrading_trends > metrics.improving_trends:
            insights.append(
                f"📉 Trend concerns: {metrics.degrading_trends} degrading vs {metrics.improving_trends} improving"
            )
        else:
            insights.append(
                f"📊 Stable trends: {metrics.stable_trends} stable milestones"
            )

        # Blocked milestones insight
        if metrics.blocked_milestones > 0:
            insights.append(
                f"🚧 {metrics.blocked_milestones} milestone(s) blocked - investigate and resolve blockers"
            )

        return insights

    def _generate_quarterly_recommendations(
        self, metrics: QuarterlyMetrics
    ) -> list[str]:
        """Generate recommendations based on quarterly metrics."""
        recommendations = []

        # Completion recommendations
        if metrics.completed_milestones / metrics.total_milestones < 0.6:
            recommendations.append(
                "🎯 **Focus on Execution:** Increase milestone completion rate through better planning and resource allocation"
            )

        # Progress recommendations
        if metrics.avg_progress < 60:
            recommendations.append(
                "⚡ **Accelerate Progress:** Implement agile practices and regular check-ins to boost milestone progress"
            )

        # CI health recommendations
        if metrics.avg_workflow_pass_rate < 80:
            recommendations.append(
                "🔧 **Improve CI Stability:** Focus on reducing flaky tests and improving test reliability"
            )

        if metrics.avg_auto_fix_success < 70:
            recommendations.append(
                "🤖 **Enhance Auto-Fix:** Improve auto-fix strategies and expand coverage for common failure patterns"
            )

        if metrics.avg_mttr > 10:
            recommendations.append(
                "⏱️ **Reduce MTTR:** Implement faster debugging tools and better error reporting to decrease resolution time"
            )

        # Trend recommendations
        if metrics.degrading_trends > metrics.improving_trends:
            recommendations.append(
                "📊 **Address Degrading Trends:** Investigate root causes of declining metrics and implement corrective actions"
            )

        # Blocked milestone recommendations
        if metrics.blocked_milestones > 0:
            recommendations.append(
                "🚧 **Resolve Blockers:** Conduct blocker review sessions and implement escalation procedures"
            )

        # General recommendations
        recommendations.append(
            "📈 **Continue Monitoring:** Maintain regular milestone reviews and CI health monitoring"
        )
        recommendations.append(
            "🔄 **Iterate and Improve:** Use quarterly insights to refine processes and planning for next quarter"
        )

        return recommendations

    def _build_quarterly_report(
        self,
        quarter: str,
        metrics: QuarterlyMetrics,
        insights: list[str],
        recommendations: list[str],
    ) -> str:
        """Build the final quarterly report."""
        report_lines = []

        # Header
        report_date = datetime.now().strftime("%Y-%m-%d")
        report_lines.append(f"# 📊 Engineering Roadmap Quarterly Report – {quarter}")
        report_lines.append(f"*Generated: {report_date}*\n")

        # Executive Summary
        report_lines.append("## 📈 Executive Summary\n")
        report_lines.append(f"- **Total Milestones:** {metrics.total_milestones}")
        report_lines.append(
            f"- **Completed:** {metrics.completed_milestones} ({metrics.completed_milestones/metrics.total_milestones*100:.0f}%)"
        )
        report_lines.append(f"- **In Progress:** {metrics.in_progress_milestones}")
        report_lines.append(f"- **Planned:** {metrics.planned_milestones}")
        report_lines.append(f"- **Blocked:** {metrics.blocked_milestones}")
        report_lines.append(f"- **Average Progress:** {metrics.avg_progress:.0f}%")
        report_lines.append(
            f"- **Average CI Pass Rate:** {metrics.avg_workflow_pass_rate:.0f}%"
        )
        report_lines.append(
            f"- **Average Auto-Fix Success:** {metrics.avg_auto_fix_success:.0f}%"
        )
        report_lines.append(f"- **Average MTTR:** {metrics.avg_mttr:.1f} minutes\n")

        # Key Insights
        report_lines.append("## 🧠 Key Insights\n")
        for insight in insights:
            report_lines.append(f"- {insight}")
        report_lines.append("")

        # Milestone Breakdown
        report_lines.append("## 🗺️ Milestone Breakdown\n")
        report_lines.append(
            "| Milestone | Status | Progress | Pass Rate | Auto-Fix | MTTR | Trend |"
        )
        report_lines.append(
            "|-----------|--------|----------|-----------|----------|------|-------|"
        )

        for milestone in metrics.milestones:
            status_emoji = {
                "Completed": "✅",
                "In Progress": "🟡",
                "Planned": "📅",
                "Blocked": "🚧",
            }.get(milestone["status"], "❓")

            trend_emoji = {"Improving": "📈", "Stable": "📊", "Degrading": "📉"}.get(
                milestone["trend"], "❓"
            )

            report_lines.append(
                f"| {milestone['name']} | {status_emoji} {milestone['status']} | "
                f"{milestone['progress']:.0f}% | {milestone['pass_rate']:.0f}% | "
                f"{milestone['auto_fix']:.0f}% | {milestone['mttr']:.1f}min | "
                f"{trend_emoji} {milestone['trend']} |"
            )

        report_lines.append("")

        # Trend Analysis
        report_lines.append("## 📊 Trend Analysis\n")
        report_lines.append(f"- **Improving:** {metrics.improving_trends} milestones")
        report_lines.append(f"- **Stable:** {metrics.stable_trends} milestones")
        report_lines.append(f"- **Degrading:** {metrics.degrading_trends} milestones\n")

        # Recommendations
        report_lines.append("## 🎯 Recommendations\n")
        for i, rec in enumerate(recommendations, 1):
            report_lines.append(f"{i}. {rec}")
        report_lines.append("")

        # Footer
        report_lines.append("---\n")
        report_lines.append(
            f"*Quarterly report generated by CI Intelligence Agent v2.0 on {datetime.now().isoformat()}*\n"
        )
        report_lines.append("*Data sourced from Notion Engineering Roadmap database*\n")

        return "\n".join(report_lines)

    def _extract_title(self, title_prop: dict[str, Any]) -> str:
        """Extract title from Notion title property."""
        if "title" in title_prop and title_prop["title"]:
            return title_prop["title"][0].get("text", {}).get("content", "")
        return ""

    def _extract_select_value(self, select_prop: dict[str, Any]) -> str:
        """Extract value from Notion select property."""
        if "select" in select_prop and select_prop["select"]:
            return select_prop["select"].get("name", "")
        return ""

    def _extract_date(self, date_prop: dict[str, Any]) -> str:
        """Extract date from Notion date property."""
        if "date" in date_prop and date_prop["date"]:
            return date_prop["date"].get("start", "")
        return ""


def get_current_quarter() -> str:
    """Get the current quarter string."""
    now = datetime.now()
    quarter = (now.month - 1) // 3 + 1
    year = now.year
    return f"Q{quarter}-{year}"


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate quarterly roadmap reports from Notion data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate report for specific quarter
  python scripts/generate_quarterly_roadmap_report.py --quarter Q4-2024

  # Generate report for current quarter
  python scripts/generate_quarterly_roadmap_report.py --auto-quarter

  # Generate and save to file
  python scripts/generate_quarterly_roadmap_report.py --quarter Q4-2024 --output reports/Q4-2024_ROADMAP_REPORT.md
        """,
    )

    parser.add_argument(
        "--quarter", help="Quarter to generate report for (e.g., Q4-2024)"
    )
    parser.add_argument(
        "--auto-quarter",
        action="store_true",
        help="Generate report for current quarter",
    )
    parser.add_argument("--output", help="Output file path (default: stdout)")
    parser.add_argument(
        "--notion-api-key", help="Notion API key (or set NOTION_API_KEY env var)"
    )
    parser.add_argument(
        "--roadmap-db-id",
        help="Notion roadmap database ID (or set NOTION_ROADMAP_DB_ID env var)",
    )

    args = parser.parse_args()

    # Determine quarter
    if args.auto_quarter:
        quarter = get_current_quarter()
    elif args.quarter:
        quarter = args.quarter
    else:
        quarter = get_current_quarter()

    # Get configuration
    notion_api_key = args.notion_api_key or os.getenv("NOTION_API_KEY")
    roadmap_db_id = args.roadmap_db_id or os.getenv("NOTION_ROADMAP_DB_ID")

    if not notion_api_key:
        print(
            "❌ Error: Notion API key required. Set NOTION_API_KEY env var or use --notion-api-key"
        )
        sys.exit(1)

    if not roadmap_db_id:
        print(
            "❌ Error: Roadmap database ID required. Set NOTION_ROADMAP_DB_ID env var or use --roadmap-db-id"
        )
        sys.exit(1)

    try:
        generator = QuarterlyReportGenerator(notion_api_key, roadmap_db_id)
        report = generator.generate_quarterly_report(quarter)

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report)
            print(f"✅ Quarterly report written to {args.output}")
        else:
            print(report)

    except Exception as e:
        print(f"❌ Error generating quarterly report: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
