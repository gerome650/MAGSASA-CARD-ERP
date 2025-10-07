#!/usr/bin/env python3
"""
Merge Quality Scoring Engine
============================

Calculates merge readiness scores based on CI quality gates and maintains
rolling history with early warning system for streak tracking.

Features:
- Merge score calculation (0-100%)
- Rolling history tracking (last 10 PRs)
- Early warning system (2/3 strikes)
- Streak tracking below team goal
- Slack digest preparation
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone


class MergeScoreCalculator:
    """Calculates merge readiness scores from CI metrics."""

    def __init__(self, team_goal: float = 90.0):
        self.team_goal = team_goal
        self.state_file = "merge_quality_state.json"

    def calculate_score(self, metrics: dict) -> dict:
        """
        Calculate merge readiness score from CI metrics.

        Args:
            metrics: Dict containing CI metrics

        Returns:
            Dict with calculated score and breakdown
        """
        # Base weights for different quality gates
        weights = {
            "syntax": 0.25,  # 25% - Syntax validation
            "lint": 0.20,  # 20% - Linting results
            "tests": 0.30,  # 30% - Test results
            "coverage": 0.15,  # 15% - Test coverage
            "security": 0.10,  # 10% - Security checks
        }

        # Calculate component scores
        syntax_score = self._calculate_syntax_score(metrics.get("syntax", {}))
        lint_score = self._calculate_lint_score(metrics.get("lint", {}))
        test_score = self._calculate_test_score(metrics.get("tests", {}))
        coverage_score = self._calculate_coverage_score(metrics.get("coverage", {}))
        security_score = self._calculate_security_score(metrics.get("security", {}))

        # Weighted total score
        total_score = (
            syntax_score * weights["syntax"]
            + lint_score * weights["lint"]
            + test_score * weights["tests"]
            + coverage_score * weights["coverage"]
            + security_score * weights["security"]
        )

        return {
            "total_score": round(total_score, 1),
            "breakdown": {
                "syntax": syntax_score,
                "lint": lint_score,
                "tests": test_score,
                "coverage": coverage_score,
                "security": security_score,
            },
            "weights": weights,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _calculate_syntax_score(self, syntax_metrics: dict) -> float:
        """Calculate syntax validation score (0-100)."""
        if not syntax_metrics:
            return 50.0  # Neutral if no data

        # Assume syntax_metrics has 'passed' boolean and 'total_files' count
        passed = syntax_metrics.get("passed", False)
        total_files = syntax_metrics.get("total_files", 1)

        if total_files == 0:
            return 100.0  # Perfect if no files to check

        return 100.0 if passed else 0.0

    def _calculate_lint_score(self, lint_metrics: dict) -> float:
        """Calculate linting score (0-100)."""
        if not lint_metrics:
            return 50.0  # Neutral if no data

        issues = lint_metrics.get("issues", 0)

        # Score decreases with more issues
        if issues == 0:
            return 100.0
        elif issues <= 5:
            return 90.0 - (issues * 2)  # -2 points per issue
        elif issues <= 20:
            return 80.0 - ((issues - 5) * 3)  # -3 points per issue beyond 5
        else:
            return max(0.0, 65.0 - ((issues - 20) * 2))  # -2 points per issue beyond 20

    def _calculate_test_score(self, test_metrics: dict) -> float:
        """Calculate test results score (0-100)."""
        if not test_metrics:
            return 50.0  # Neutral if no data

        passed = test_metrics.get("passed", 0)
        failed = test_metrics.get("failed", 0)
        total = passed + failed

        if total == 0:
            return 50.0  # Neutral if no tests

        return (passed / total) * 100.0

    def _calculate_coverage_score(self, coverage_metrics: dict) -> float:
        """Calculate coverage score (0-100)."""
        if not coverage_metrics:
            return 50.0  # Neutral if no data

        coverage_percent = coverage_metrics.get("coverage_percent", 0.0)

        # Score based on coverage percentage
        if coverage_percent >= 90:
            return 100.0
        elif coverage_percent >= 80:
            return 90.0 + (coverage_percent - 80)  # 90-100 range
        elif coverage_percent >= 70:
            return 70.0 + ((coverage_percent - 70) * 2)  # 70-90 range
        elif coverage_percent >= 50:
            return 50.0 + ((coverage_percent - 50) * 1)  # 50-70 range
        else:
            return coverage_percent  # 0-50 range

    def _calculate_security_score(self, security_metrics: dict) -> float:
        """Calculate security checks score (0-100)."""
        if not security_metrics:
            return 100.0  # Perfect if no security checks (assume safe)

        # Assume security_metrics has vulnerability counts
        critical = security_metrics.get("critical", 0)
        high = security_metrics.get("high", 0)
        medium = security_metrics.get("medium", 0)

        # Score decreases with severity
        score = 100.0
        score -= critical * 30  # -30 points per critical
        score -= high * 15  # -15 points per high
        score -= medium * 5  # -5 points per medium

        return max(0.0, score)

    def load_state(self) -> dict:
        """Load merge quality state from file."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file) as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError):
                pass

        # Return default state
        return {
            "history": [],
            "streak_below_goal": 0,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "team_goal": self.team_goal,
        }

    def save_state(self, state: dict) -> None:
        """Save merge quality state to file."""
        state["last_updated"] = datetime.now(timezone.utc).isoformat()

        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)

    def update_history(self, score_data: dict, pr_metadata: dict) -> dict:
        """
        Update rolling history with new PR score.

        Args:
            score_data: Calculated score data
            pr_metadata: PR metadata (branch, commit, etc.)

        Returns:
            Updated state with early warning analysis
        """
        state = self.load_state()
        history = state.get("history", [])

        # Create new history entry
        new_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "score": score_data["total_score"],
            "breakdown": score_data["breakdown"],
            "pr_metadata": pr_metadata,
            "delta_vs_previous": 0.0,
        }

        # Calculate delta vs previous PR
        if history:
            prev_score = history[-1]["score"]
            new_entry["delta_vs_previous"] = round(
                score_data["total_score"] - prev_score, 1
            )

        # Add to history (keep last 10 PRs)
        history.append(new_entry)
        state["history"] = history[-10:]

        # Update streak tracking
        current_score = score_data["total_score"]
        if current_score < self.team_goal:
            state["streak_below_goal"] += 1
        else:
            state["streak_below_goal"] = 0

        # Determine early warning status
        state["early_warning"] = state["streak_below_goal"] >= 2
        state["auto_fail"] = state["streak_below_goal"] >= 3

        self.save_state(state)
        return state

    def generate_sparkline(self, scores: list[float]) -> str:
        """Generate Unicode sparkline from score history."""
        if not scores:
            return "—"

        # Normalize scores to 0-7 range for sparkline chars
        min_score = min(scores)
        max_score = max(scores)

        if max_score == min_score:
            return "▁" * len(scores)

        spark_chars = "▁▂▃▄▅▆▇█"
        sparkline = ""

        for score in scores:
            normalized = (score - min_score) / (max_score - min_score)
            char_index = int(normalized * (len(spark_chars) - 1))
            sparkline += spark_chars[char_index]

        return sparkline

    def prepare_slack_payload(self, state: dict, score_data: dict) -> dict:
        """Prepare Slack Block Kit payload for merge quality digest."""
        history = state.get("history", [])
        scores = [entry["score"] for entry in history]

        # Calculate rolling average
        rolling_avg = sum(scores) / len(scores) if scores else 0.0

        # Generate sparkline
        sparkline = self.generate_sparkline(scores)

        # Determine status badges
        badges = {}
        breakdown = score_data.get("breakdown", {})

        badges["syntax"] = "✅" if breakdown.get("syntax", 0) >= 90 else "❌"
        badges["lint"] = "✅" if breakdown.get("lint", 0) >= 90 else "❌"
        badges["coverage"] = "✅" if breakdown.get("coverage", 0) >= 80 else "❌"

        # Count severity levels (mock data for now)
        severity = {"critical": 0, "warning": 0, "info": 0}

        # Mock workflow performance data
        top_slowest_workflows = [
            {"name": "CI Pro Dashboard", "duration": "8.5 min", "percent": 35},
            {"name": "Python Tests", "duration": "6.2 min", "percent": 28},
            {"name": "Lint Check", "duration": "2.1 min", "percent": 15},
        ]

        return {
            "merge_score": score_data["total_score"],
            "delta_vs_last": history[-1]["delta_vs_previous"] if history else 0.0,
            "rolling_average": round(rolling_avg, 1),
            "trend": scores,
            "severity": severity,
            "team_goal": self.team_goal,
            "streak_below_goal": state.get("streak_below_goal", 0),
            "early_warning": state.get("early_warning", False),
            "auto_fail": state.get("auto_fail", False),
            "sparkline": sparkline,
            "badges": badges,
            "top_slowest_workflows": top_slowest_workflows,
        }


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Update merge quality scores")
    parser.add_argument("--pytest-json", help="Pytest JSON report path")
    parser.add_argument("--coverage-xml", help="Coverage XML report path")
    parser.add_argument("--ruff-json", help="Ruff lint JSON report path")
    parser.add_argument("--syntax-guard-json", help="Syntax guard JSON report path")
    parser.add_argument(
        "--team-goal", type=float, default=90.0, help="Team goal percentage"
    )
    parser.add_argument("--branch", default="main", help="Branch name")
    parser.add_argument("--commit", default="", help="Commit hash")
    parser.add_argument("--actor", default="", help="Actor (user) name")
    parser.add_argument(
        "--output",
        default="merge_slack_payload.json",
        help="Output file for Slack payload",
    )

    args = parser.parse_args()

    # Initialize calculator
    calculator = MergeScoreCalculator(team_goal=args.team_goal)

    # Parse metrics from files
    metrics = {}

    # Parse pytest results
    if args.pytest_json and os.path.exists(args.pytest_json):
        try:
            with open(args.pytest_json) as f:
                pytest_data = json.load(f)
                summary = pytest_data.get("summary", {})
                metrics["tests"] = {
                    "passed": summary.get("passed", 0),
                    "failed": summary.get("failed", 0),
                    "skipped": summary.get("skipped", 0),
                }
        except (OSError, json.JSONDecodeError):
            print(f"Warning: Could not parse pytest JSON: {args.pytest_json}")

    # Parse coverage results
    if args.coverage_xml and os.path.exists(args.coverage_xml):
        try:
            import xml.etree.ElementTree as ET

            tree = ET.parse(args.coverage_xml)
            root = tree.getroot()
            line_rate = float(root.attrib.get("line-rate", 0))
            metrics["coverage"] = {"coverage_percent": round(line_rate * 100, 1)}
        except (OSError, ET.ParseError, ValueError):
            print(f"Warning: Could not parse coverage XML: {args.coverage_xml}")

    # Parse ruff results
    if args.ruff_json and os.path.exists(args.ruff_json):
        try:
            with open(args.ruff_json) as f:
                ruff_data = json.load(f)
                metrics["lint"] = {
                    "issues": len(ruff_data) if isinstance(ruff_data, list) else 0
                }
        except (OSError, json.JSONDecodeError):
            print(f"Warning: Could not parse ruff JSON: {args.ruff_json}")

    # Parse syntax guard results
    if args.syntax_guard_json and os.path.exists(args.syntax_guard_json):
        try:
            with open(args.syntax_guard_json) as f:
                syntax_data = json.load(f)
                metrics["syntax"] = {
                    "passed": syntax_data.get("passed", False),
                    "total_files": syntax_data.get("total_files_checked", 0),
                }
        except (OSError, json.JSONDecodeError):
            print(
                f"Warning: Could not parse syntax guard JSON: {args.syntax_guard_json}"
            )

    # Calculate score
    score_data = calculator.calculate_score(metrics)

    # Prepare PR metadata
    pr_metadata = {
        "branch": args.branch,
        "commit": args.commit,
        "actor": args.actor,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Update history and get state
    state = calculator.update_history(score_data, pr_metadata)

    # Generate Slack payload
    slack_payload = calculator.prepare_slack_payload(state, score_data)

    # Save Slack payload
    with open(args.output, "w") as f:
        json.dump(slack_payload, f, indent=2)

    # Print summary
    print(f"Merge Score: {score_data['total_score']}%")
    print(f"Team Goal: {args.team_goal}%")
    print(f"Streak Below Goal: {state.get('streak_below_goal', 0)}")

    if state.get("early_warning"):
        print("⚠️  Early Warning: 2/3 strikes!")

    if state.get("auto_fail"):
        print("🔥 Auto-Fail: 3+ consecutive PRs below goal!")
        sys.exit(1)

    print(f"Slack payload saved to: {args.output}")


if __name__ == "__main__":
    main()
