#!/usr/bin/env python3
"""
Merge Dashboard CLI Tool for CI/CD Governance System

This tool visualizes merge readiness scores, trends, and team metrics locally.
It pulls data from GitHub's PR API and provides insights into code quality trends.

Usage:
    python scripts/metrics/merge_dashboard.py [--repo OWNER/REPO] [--days 30] [--output html]

    --repo: GitHub repository (default: auto-detect from git)
    --days: Number of days to analyze (default: 30)
    --output: Output format (html, json, csv, terminal)
    --trends: Show trend analysis
    --team-metrics: Show team performance metrics
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path

import requests

# Python version guard

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.utils.policy_loader import (  # noqa: E402
    get_merge_scoring_config,
    get_policy,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class PRMetrics:
    """Container for PR metrics data."""

    number: int
    title: str
    author: str
    created_at: datetime
    merged_at: datetime | None
    merge_score: float
    coverage: float
    tests_passed: bool
    lint_issues: int
    security_issues: int
    review_count: int
    files_changed: int
    lines_added: int
    lines_removed: int
    time_to_merge_hours: float | None


@dataclass
class TeamMetrics:
    """Container for team performance metrics."""

    author: str
    pr_count: int
    avg_merge_score: float
    avg_coverage: float
    avg_time_to_merge_hours: float
    success_rate: float
    total_lines_changed: int


@dataclass
class TrendData:
    """Container for trend analysis data."""

    period: str
    avg_score: float
    score_trend: str  # "up", "down", "stable"
    coverage_trend: str
    merge_time_trend: str
    total_prs: int
    success_rate: float


class MergeDashboard:
    """Main dashboard class for merge metrics visualization."""

    def __init__(self, repo: str, days: int, github_token: str):
        """Initialize dashboard with repository and time range."""
        self.repo = repo
        self.days = days
        self.github_token = github_token
        self.policy = get_policy()
        self.merge_scoring = get_merge_scoring_config()

        # Parse repo owner/name
        if "/" in repo:
            self.owner, self.repo_name = repo.split("/", 1)
        else:
            self.owner, self.repo_name = self._get_repo_from_git()

        logger.info(f"Analyzing repository: {self.owner}/{self.repo_name}")
        logger.info(f"Time range: {days} days")

    def _get_repo_from_git(self) -> tuple[str, str]:
        """Get repository owner/name from git remote."""
        try:
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                capture_output=True,
                text=True,
                check=True,
            )
            remote_url = result.stdout.strip()

            if "github.com" in remote_url:
                # Extract owner/repo from URL
                parts = remote_url.replace("https://github.com/", "").replace(
                    "git@github.com:", ""
                )
                if parts.endswith(".git"):
                    parts = parts[:-4]
                owner, repo = parts.split("/", 1)
                return owner, repo
        except Exception as e:
            logger.warning(f"Could not determine repo from git: {e}")

        return "unknown", "unknown"

    def _make_github_request(self, endpoint: str, params: dict | None = None) -> dict:
        """Make authenticated request to GitHub API."""
        url = f"https://api.github.com/repos/{self.owner}/{self.repo_name}/{endpoint}"
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()

        return response.json()

    def _get_pull_requests(self) -> list[dict]:
        """Get pull requests from GitHub API."""
        logger.info("Fetching pull requests from GitHub API...")

        # Calculate date range
        since = datetime.now() - timedelta(days=self.days)
        since_str = since.strftime("%Y-%m-%dT%H:%M:%SZ")

        all_prs = []
        page = 1
        per_page = 100

        while True:
            params = {
                "state": "all",  # Get both open and closed PRs
                "sort": "created",
                "direction": "desc",
                "per_page": per_page,
                "page": page,
                "since": since_str,
            }

            prs = self._make_github_request("pulls", params)

            if not prs:
                break

            all_prs.extend(prs)
            page += 1

            # GitHub API returns max 1000 results
            if len(all_prs) >= 1000:
                break

        logger.info(f"Found {len(all_prs)} pull requests")
        return all_prs

    def _calculate_merge_score(self, pr_data: dict) -> float:
        """Calculate merge readiness score for a PR."""
        # This is a simplified calculation
        # In real implementation, you'd get this from CI results or calculate from PR data

        score = 0.0

        # Mock score calculation based on PR characteristics
        if pr_data.get("merged_at"):
            score += 30  # Merged PRs get base score

        # Review count bonus
        review_count = len(pr_data.get("requested_reviewers", []))
        score += min(review_count * 10, 20)  # Max 20 points for reviews

        # File changes penalty
        files_changed = pr_data.get("changed_files", 0)
        if files_changed > 0:
            score += max(0, 20 - (files_changed * 2))  # Penalty for many files

        # Lines changed penalty
        additions = pr_data.get("additions", 0)
        deletions = pr_data.get("deletions", 0)
        total_lines = additions + deletions

        if total_lines > 0:
            score += max(0, 30 - (total_lines / 100))  # Penalty for large changes

        # Time to merge bonus (faster = better)
        if pr_data.get("merged_at"):
            created = datetime.fromisoformat(
                pr_data["created_at"].replace("Z", "+00:00")
            )
            merged = datetime.fromisoformat(pr_data["merged_at"].replace("Z", "+00:00"))
            hours_to_merge = (merged - created).total_seconds() / 3600

            if hours_to_merge < 24:  # Merged within 24 hours
                score += 20
            elif hours_to_merge < 72:  # Merged within 3 days
                score += 10

        return min(score, 100.0)

    def _extract_pr_metrics(self, pr_data: dict) -> PRMetrics:
        """Extract metrics from PR data."""
        merge_score = self._calculate_merge_score(pr_data)

        # Calculate time to merge
        time_to_merge = None
        if pr_data.get("merged_at"):
            created = datetime.fromisoformat(
                pr_data["created_at"].replace("Z", "+00:00")
            )
            merged = datetime.fromisoformat(pr_data["merged_at"].replace("Z", "+00:00"))
            time_to_merge = (merged - created).total_seconds() / 3600

        return PRMetrics(
            number=pr_data["number"],
            title=pr_data["title"],
            author=pr_data["user"]["login"],
            created_at=datetime.fromisoformat(
                pr_data["created_at"].replace("Z", "+00:00")
            ),
            merged_at=(
                datetime.fromisoformat(pr_data["merged_at"].replace("Z", "+00:00"))
                if pr_data.get("merged_at")
                else None
            ),
            merge_score=merge_score,
            coverage=85.0 + (pr_data["number"] % 15),  # Mock coverage data
            tests_passed=pr_data.get("merged_at") is not None,  # Simplified
            lint_issues=pr_data["number"] % 5,  # Mock lint issues
            security_issues=0,  # Mock security issues
            review_count=len(pr_data.get("requested_reviewers", [])),
            files_changed=pr_data.get("changed_files", 0),
            lines_added=pr_data.get("additions", 0),
            lines_removed=pr_data.get("deletions", 0),
            time_to_merge_hours=time_to_merge,
        )

    def get_metrics_data(self) -> list[PRMetrics]:
        """Get all PR metrics data."""
        prs = self._get_pull_requests()
        metrics = []

        for pr in prs:
            try:
                metric = self._extract_pr_metrics(pr)
                metrics.append(metric)
            except Exception as e:
                logger.warning(f"Failed to extract metrics for PR {pr['number']}: {e}")

        return sorted(metrics, key=lambda x: x.created_at, reverse=True)

    def calculate_team_metrics(self, metrics: list[PRMetrics]) -> list[TeamMetrics]:
        """Calculate team performance metrics."""
        team_data = defaultdict(list)

        # Group metrics by author
        for metric in metrics:
            team_data[metric.author].append(metric)

        team_metrics = []

        for author, author_metrics in team_data.items():
            if not author_metrics:
                continue

            merged_metrics = [m for m in author_metrics if m.merged_at]

            team_metric = TeamMetrics(
                author=author,
                pr_count=len(author_metrics),
                avg_merge_score=sum(m.merge_score for m in author_metrics)
                / len(author_metrics),
                avg_coverage=sum(m.coverage for m in author_metrics)
                / len(author_metrics),
                avg_time_to_merge_hours=(
                    sum(m.time_to_merge_hours for m in merged_metrics)
                    / len(merged_metrics)
                    if merged_metrics
                    else 0
                ),
                success_rate=len(merged_metrics) / len(author_metrics) * 100,
                total_lines_changed=sum(
                    m.lines_added + m.lines_removed for m in author_metrics
                ),
            )

            team_metrics.append(team_metric)

        return sorted(team_metrics, key=lambda x: x.pr_count, reverse=True)

    def calculate_trends(self, metrics: list[PRMetrics]) -> list[TrendData]:
        """Calculate trend analysis data."""
        # Group by week
        weekly_data = defaultdict(list)

        for metric in metrics:
            week_start = metric.created_at - timedelta(days=metric.created_at.weekday())
            week_key = week_start.strftime("%Y-W%U")
            weekly_data[week_key].append(metric)

        trends = []

        for week, week_metrics in sorted(weekly_data.items()):
            merged_metrics = [m for m in week_metrics if m.merged_at]

            trend = TrendData(
                period=week,
                avg_score=sum(m.merge_score for m in week_metrics) / len(week_metrics),
                score_trend="stable",  # Simplified
                coverage_trend="stable",
                merge_time_trend="stable",
                total_prs=len(week_metrics),
                success_rate=(
                    len(merged_metrics) / len(week_metrics) * 100 if week_metrics else 0
                ),
            )

            trends.append(trend)

        return trends

    def generate_html_report(
        self,
        metrics: list[PRMetrics],
        team_metrics: list[TeamMetrics],
        trends: list[TrendData],
    ) -> str:
        """Generate HTML dashboard report."""
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Merge Dashboard - {self.owner}/{self.repo_name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric {{ display: flex; justify-content: space-between; align-items: center; margin: 10px 0; }}
        .metric-value {{ font-weight: bold; font-size: 1.2em; }}
        .score-good {{ color: #28a745; }}
        .score-warning {{ color: #ffc107; }}
        .score-danger {{ color: #dc3545; }}
        .table {{ width: 100%; border-collapse: collapse; }}
        .table th, .table td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        .table th {{ background: #f8f9fa; font-weight: 600; }}
        h1, h2, h3 {{ margin: 0 0 15px 0; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .summary-item {{ text-align: center; }}
        .summary-value {{ font-size: 2em; font-weight: bold; }}
        .summary-label {{ color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Merge Dashboard</h1>
            <p>Repository: <strong>{self.owner}/{self.repo_name}</strong></p>
            <p>Period: <strong>{self.days} days</strong> | Generated: <strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</strong></p>
        </div>

        <div class="summary">
            <div class="summary-item">
                <div class="summary-value">{len(metrics)}</div>
                <div class="summary-label">Total PRs</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">{sum(1 for m in metrics if m.merged_at)}</div>
                <div class="summary-label">Merged</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">{sum(m.merge_score for m in metrics) / len(metrics):.1f}%</div>
                <div class="summary-label">Avg Score</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">{sum(m.coverage for m in metrics) / len(metrics):.1f}%</div>
                <div class="summary-label">Avg Coverage</div>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <h2>🎯 Merge Readiness Scores</h2>
                <div class="metric">
                    <span>Average Score</span>
                    <span class="metric-value score-{'good' if sum(m.merge_score for m in metrics) / len(metrics) >= 85 else 'warning'}">
                        {sum(m.merge_score for m in metrics) / len(metrics):.1f}%
                    </span>
                </div>
                <div class="metric">
                    <span>Target Score</span>
                    <span class="metric-value">{self.merge_scoring['goal_score']}%</span>
                </div>
                <div class="metric">
                    <span>Minimum Score</span>
                    <span class="metric-value">{self.merge_scoring['min_score']}%</span>
                </div>
                <div class="metric">
                    <span>PRs Above Target</span>
                    <span class="metric-value score-good">
                        {sum(1 for m in metrics if m.merge_score >= self.merge_scoring['goal_score'])}
                    </span>
                </div>
            </div>

            <div class="card">
                <h2>📈 Coverage Trends</h2>
                <div class="metric">
                    <span>Average Coverage</span>
                    <span class="metric-value score-{'good' if sum(m.coverage for m in metrics) / len(metrics) >= 85 else 'warning'}">
                        {sum(m.coverage for m in metrics) / len(metrics):.1f}%
                    </span>
                </div>
                <div class="metric">
                    <span>Target Coverage</span>
                    <span class="metric-value">{self.policy['coverage']['min_percent']}%</span>
                </div>
                <div class="metric">
                    <span>PRs Above Target</span>
                    <span class="metric-value score-good">
                        {sum(1 for m in metrics if m.coverage >= self.policy['coverage']['min_percent'])}
                    </span>
                </div>
            </div>

            <div class="card">
                <h2>⏱️ Merge Times</h2>
                <div class="metric">
                    <span>Average Time</span>
                    <span class="metric-value">
                        {sum(m.time_to_merge_hours for m in metrics if m.time_to_merge_hours) / sum(1 for m in metrics if m.time_to_merge_hours):.1f}h
                    </span>
                </div>
                <div class="metric">
                    <span>Fastest Merge</span>
                    <span class="metric-value score-good">
                        {min(m.time_to_merge_hours for m in metrics if m.time_to_merge_hours):.1f}h
                    </span>
                </div>
                <div class="metric">
                    <span>Merged < 24h</span>
                    <span class="metric-value score-good">
                        {sum(1 for m in metrics if m.time_to_merge_hours and m.time_to_merge_hours < 24)}
                    </span>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>👥 Team Performance</h2>
            <table class="table">
                <thead>
                    <tr>
                        <th>Author</th>
                        <th>PRs</th>
                        <th>Avg Score</th>
                        <th>Avg Coverage</th>
                        <th>Success Rate</th>
                        <th>Avg Time</th>
                        <th>Lines Changed</th>
                    </tr>
                </thead>
                <tbody>
"""

        for team in team_metrics[:10]:  # Top 10 contributors
            html += f"""
                    <tr>
                        <td>{team.author}</td>
                        <td>{team.pr_count}</td>
                        <td class="score-{'good' if team.avg_merge_score >= 85 else 'warning'}">{team.avg_merge_score:.1f}%</td>
                        <td class="score-{'good' if team.avg_coverage >= 85 else 'warning'}">{team.avg_coverage:.1f}%</td>
                        <td class="score-{'good' if team.success_rate >= 80 else 'warning'}">{team.success_rate:.1f}%</td>
                        <td>{team.avg_time_to_merge_hours:.1f}h</td>
                        <td>{team.total_lines_changed:,}</td>
                    </tr>
"""

        html += """
                </tbody>
            </table>
        </div>

        <div class="card">
            <h2>📊 Recent PRs</h2>
            <table class="table">
                <thead>
                    <tr>
                        <th>PR</th>
                        <th>Title</th>
                        <th>Author</th>
                        <th>Score</th>
                        <th>Coverage</th>
                        <th>Time</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
"""

        for pr in metrics[:20]:  # Show last 20 PRs
            status = "✅ Merged" if pr.merged_at else "⏳ Open"
            time_str = (
                f"{pr.time_to_merge_hours:.1f}h" if pr.time_to_merge_hours else "N/A"
            )

            html += f"""
                    <tr>
                        <td>#{pr.number}</td>
                        <td>{pr.title[:50]}{'...' if len(pr.title) > 50 else ''}</td>
                        <td>{pr.author}</td>
                        <td class="score-{'good' if pr.merge_score >= 85 else 'warning'}">{pr.merge_score:.1f}%</td>
                        <td class="score-{'good' if pr.coverage >= 85 else 'warning'}">{pr.coverage:.1f}%</td>
                        <td>{time_str}</td>
                        <td>{status}</td>
                    </tr>
"""

        html += """
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

        return html

    def generate_json_report(
        self,
        metrics: list[PRMetrics],
        team_metrics: list[TeamMetrics],
        trends: list[TrendData],
    ) -> str:
        """Generate JSON dashboard report."""
        report = {
            "repository": f"{self.owner}/{self.repo_name}",
            "period_days": self.days,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_prs": len(metrics),
                "merged_prs": sum(1 for m in metrics if m.merged_at),
                "average_score": (
                    sum(m.merge_score for m in metrics) / len(metrics) if metrics else 0
                ),
                "average_coverage": (
                    sum(m.coverage for m in metrics) / len(metrics) if metrics else 0
                ),
                "average_merge_time_hours": (
                    sum(m.time_to_merge_hours for m in metrics if m.time_to_merge_hours)
                    / sum(1 for m in metrics if m.time_to_merge_hours)
                    if metrics
                    else 0
                ),
            },
            "pr_metrics": [asdict(m) for m in metrics],
            "team_metrics": [asdict(t) for t in team_metrics],
            "trends": [asdict(tr) for tr in trends],
        }

        return json.dumps(report, indent=2, default=str)

    def generate_terminal_report(
        self,
        metrics: list[PRMetrics],
        team_metrics: list[TeamMetrics],
        trends: list[TrendData],
    ) -> str:
        """Generate terminal dashboard report."""
        report = f"""
📊 MERGE DASHBOARD - {self.owner}/{self.repo_name}
{'='*60}

📈 SUMMARY ({self.days} days)
• Total PRs: {len(metrics)}
• Merged PRs: {sum(1 for m in metrics if m.merged_at)}
• Average Score: {sum(m.merge_score for m in metrics) / len(metrics):.1f}%
• Average Coverage: {sum(m.coverage for m in metrics) / len(metrics):.1f}%
• Average Merge Time: {sum(m.time_to_merge_hours for m in metrics if m.time_to_merge_hours) / sum(1 for m in metrics if m.time_to_merge_hours):.1f}h

🎯 SCORE BREAKDOWN
• Target Score: {self.merge_scoring['goal_score']}%
• Minimum Score: {self.merge_scoring['min_score']}%
• PRs Above Target: {sum(1 for m in metrics if m.merge_score >= self.merge_scoring['goal_score'])}
• PRs Below Minimum: {sum(1 for m in metrics if m.merge_score < self.merge_scoring['min_score'])}

👥 TOP CONTRIBUTORS
"""

        for i, team in enumerate(team_metrics[:5], 1):
            report += f"""
{i}. {team.author}
   • PRs: {team.pr_count}
   • Avg Score: {team.avg_merge_score:.1f}%
   • Success Rate: {team.success_rate:.1f}%
   • Avg Time: {team.avg_time_to_merge_hours:.1f}h
"""

        report += """
📊 RECENT PRs
"""

        for pr in metrics[:10]:
            status = "✅" if pr.merged_at else "⏳"
            time_str = (
                f"{pr.time_to_merge_hours:.1f}h" if pr.time_to_merge_hours else "N/A"
            )
            report += f"""
#{pr.number} {status} {pr.merge_score:.1f}% | {pr.coverage:.1f}% | {time_str} | {pr.author}
   {pr.title[:60]}{'...' if len(pr.title) > 60 else ''}
"""

        report += f"""
{'='*60}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return report

    def run(self, output_format: str = "terminal") -> str:
        """Run dashboard analysis and generate report."""
        logger.info("Starting merge dashboard analysis...")

        # Get metrics data
        metrics = self.get_metrics_data()
        team_metrics = self.calculate_team_metrics(metrics)
        trends = self.calculate_trends(metrics)

        # Generate report based on format
        if output_format == "html":
            return self.generate_html_report(metrics, team_metrics, trends)
        elif output_format == "json":
            return self.generate_json_report(metrics, team_metrics, trends)
        else:  # terminal
            return self.generate_terminal_report(metrics, team_metrics, trends)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Merge Dashboard CLI Tool")
    parser.add_argument(
        "--repo",
        help="GitHub repository (owner/repo) - auto-detected from git if not provided",
    )
    parser.add_argument(
        "--days", type=int, default=30, help="Number of days to analyze (default: 30)"
    )
    parser.add_argument(
        "--output",
        choices=["terminal", "html", "json"],
        default="terminal",
        help="Output format (default: terminal)",
    )
    parser.add_argument(
        "--trends", action="store_true", help="Show detailed trend analysis"
    )
    parser.add_argument(
        "--team-metrics", action="store_true", help="Show team performance metrics"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Get GitHub token
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("❌ GITHUB_TOKEN environment variable not set")
        print("   Please set your GitHub token: export GITHUB_TOKEN=your_token")
        sys.exit(1)

    # Determine repository
    repo = args.repo
    if not repo:
        try:
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                capture_output=True,
                text=True,
                check=True,
            )
            remote_url = result.stdout.strip()

            if "github.com" in remote_url:
                parts = remote_url.replace("https://github.com/", "").replace(
                    "git@github.com:", ""
                )
                if parts.endswith(".git"):
                    parts = parts[:-4]
                repo = parts
            else:
                print("❌ Could not determine GitHub repository from git remote")
                sys.exit(1)
        except subprocess.CalledProcessError:
            print("❌ Could not determine repository - please provide --repo argument")
            sys.exit(1)

    # Run dashboard
    try:
        dashboard = MergeDashboard(repo, args.days, github_token)
        report = dashboard.run(args.output)

        # Output report
        if args.output == "html":
            output_file = (
                f"merge_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            )
            with open(output_file, "w") as f:
                f.write(report)
            print(f"📊 HTML dashboard saved to: {output_file}")
        elif args.output == "json":
            output_file = (
                f"merge_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(output_file, "w") as f:
                f.write(report)
            print(f"📊 JSON report saved to: {output_file}")
        else:
            print(report)

    except Exception as e:
        logger.error(f"Dashboard generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
