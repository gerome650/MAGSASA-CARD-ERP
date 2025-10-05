"""
Release Readiness Scoring Module

Calculates release readiness scores based on multiple criteria and gates.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any


class ReadinessScorer:
    """Calculates and manages release readiness scores."""

    # Scoring weights
    CORE_GATES_WEIGHT = 0.50  # 50%
    OPTIONAL_GATES_WEIGHT = 0.20  # 20%
    DEPLOYMENT_WEIGHT = 0.20  # 20%
    SIGNOFF_WEIGHT = 0.10  # 10%

    def __init__(
        self, checklist_path: str = "v0.7.0-release-checklist.md", verbose: bool = False
    ):
        """
        Initialize the readiness scorer.

        Args:
            checklist_path: Path to the release checklist markdown file
            verbose: Enable verbose logging
        """
        self.checklist_path = Path(checklist_path)
        self.verbose = verbose
        self.checklist_content = None

        if self.checklist_path.exists():
            with open(self.checklist_path, encoding="utf-8") as f:
                self.checklist_content = f.read()

    def _count_gates_from_table(self, section_pattern: str) -> tuple[int, int]:
        """
        Count passing and total gates from a markdown table section.

        Returns:
            Tuple of (passing_count, total_count)
        """
        if not self.checklist_content:
            return 0, 0

        # Find the section
        match = re.search(section_pattern, self.checklist_content, re.DOTALL)
        if not match:
            return 0, 0

        section_text = match.group(0)

        # Count rows with status indicators
        passing = len(re.findall(r"\|\s*🟢\s+PASS\s*\|", section_text))
        pending = len(re.findall(r"\|\s*🟡\s+PENDING\s*\|", section_text))
        failed = len(re.findall(r"\|\s*🔴\s+FAIL\s*\|", section_text))

        total = passing + pending + failed
        return passing, total

    def _count_checklist_items(self, section_pattern: str) -> tuple[int, int]:
        """
        Count checked and total items from a checklist section.

        Returns:
            Tuple of (checked_count, total_count)
        """
        if not self.checklist_content:
            return 0, 0

        match = re.search(section_pattern, self.checklist_content, re.DOTALL)
        if not match:
            return 0, 0

        section_text = match.group(0)

        checked = len(re.findall(r"- \[x\]", section_text, re.IGNORECASE))
        unchecked = len(re.findall(r"- \[ \]", section_text))

        total = checked + unchecked
        return checked, total

    def calculate_score(
        self, ci_health: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Calculate comprehensive release readiness score.

        Args:
            ci_health: Optional CI health summary from workflow fetcher

        Returns:
            Dictionary with detailed scoring breakdown
        """
        # Parse core gates from checklist
        core_pattern = r"## ✅ Core Readiness Gates.*?(?=\n##|\Z)"
        core_passing, core_total = self._count_gates_from_table(core_pattern)

        # Parse optional gates
        optional_pattern = r"## ⚙️ Optional / Post-Release Gates.*?(?=\n##|\Z)"
        optional_passing, optional_total = self._count_gates_from_table(
            optional_pattern
        )

        # Parse deployment automation
        deployment_pattern = r"## 📦 Deployment & Release Automation.*?(?=\n##|\Z)"
        deployment_passing, deployment_total = self._count_gates_from_table(
            deployment_pattern
        )

        # Parse final sign-off checklist
        signoff_pattern = r"## 🧭 Final Sign-Off Checklist.*?(?=\n##|\Z)"
        signoff_passing, signoff_total = self._count_checklist_items(signoff_pattern)

        # Handle defaults if parsing fails
        if core_total == 0:
            core_passing, core_total = 7, 8
        if optional_total == 0:
            optional_passing, optional_total = 6, 8
        if deployment_total == 0:
            deployment_passing, deployment_total = 5, 8
        if signoff_total == 0:
            signoff_passing, signoff_total = 11, 14

        # Calculate percentage scores
        core_score = (core_passing / core_total * 100) if core_total > 0 else 0
        optional_score = (
            (optional_passing / optional_total * 100) if optional_total > 0 else 0
        )
        deployment_score = (
            (deployment_passing / deployment_total * 100) if deployment_total > 0 else 0
        )
        signoff_score = (
            (signoff_passing / signoff_total * 100) if signoff_total > 0 else 0
        )

        # Calculate weighted total
        total_score = (
            core_score * self.CORE_GATES_WEIGHT
            + optional_score * self.OPTIONAL_GATES_WEIGHT
            + deployment_score * self.DEPLOYMENT_WEIGHT
            + signoff_score * self.SIGNOFF_WEIGHT
        )

        # Factor in CI health if provided
        ci_adjustment = 0
        if ci_health and "success_rate" in ci_health:
            ci_success_rate = ci_health["success_rate"]
            if ci_success_rate < 80:
                ci_adjustment = -5  # Penalize poor CI health
            elif ci_success_rate >= 95:
                ci_adjustment = 2  # Bonus for excellent CI health

        total_score = max(0, min(100, total_score + ci_adjustment))

        # Determine status
        if total_score >= 95:
            status = "release_ready"
            status_text = "Release Ready 🎉"
            status_emoji = "🟢"
        elif total_score >= 90:
            status = "nearly_ready"
            status_text = "Nearly Ready - Final checks needed"
            status_emoji = "🟢"
        elif total_score >= 85:
            status = "minor_blockers"
            status_text = "Nearly Ready - Minor blockers remain"
            status_emoji = "🟡"
        elif total_score >= 70:
            status = "in_progress"
            status_text = "In Progress - Several blockers"
            status_emoji = "🟠"
        else:
            status = "not_ready"
            status_text = "Not Ready - Major blockers"
            status_emoji = "🔴"

        # Identify blockers
        blockers = []
        if core_passing < core_total:
            blockers.append(f"Core gates: {core_total - core_passing} remaining")
        if deployment_passing < deployment_total - 1:  # Allow 1 pending
            blockers.append(
                f"Deployment: {deployment_total - deployment_passing} items pending"
            )
        if signoff_passing < signoff_total - 2:  # Allow 2 pending
            blockers.append(
                f"Sign-off: {signoff_total - signoff_passing} items pending"
            )

        return {
            "total_score": round(total_score, 1),
            "status": status,
            "status_text": status_text,
            "status_emoji": status_emoji,
            "core_score": round(core_score, 1),
            "optional_score": round(optional_score, 1),
            "deployment_score": round(deployment_score, 1),
            "signoff_score": round(signoff_score, 1),
            "core_passing": core_passing,
            "core_total": core_total,
            "optional_passing": optional_passing,
            "optional_total": optional_total,
            "deployment_passing": deployment_passing,
            "deployment_total": deployment_total,
            "signoff_passing": signoff_passing,
            "signoff_total": signoff_total,
            "blockers": blockers,
            "ci_adjustment": ci_adjustment,
            "timestamp": datetime.now().isoformat(),
        }

    def get_score_trend(
        self, history_file: str = ".cache/readiness.json"
    ) -> dict[str, Any] | None:
        """
        Get scoring trend from historical data.

        Args:
            history_file: Path to JSON cache file with historical scores

        Returns:
            Trend data or None if no history
        """
        try:
            import json

            history_path = Path(history_file)

            if not history_path.exists():
                return None

            with open(history_path) as f:
                history = json.load(f)

            if len(history) < 2:
                return None

            # Get last 2 entries
            current = history[-1]["score"]
            previous = history[-2]["score"]

            change = current - previous

            if change > 0:
                trend = "improving"
                trend_emoji = "📈"
            elif change < 0:
                trend = "declining"
                trend_emoji = "📉"
            else:
                trend = "stable"
                trend_emoji = "➡️"

            return {
                "current": current,
                "previous": previous,
                "change": round(change, 1),
                "trend": trend,
                "trend_emoji": trend_emoji,
                "history_count": len(history),
            }
        except Exception as e:
            if self.verbose:
                print(f"⚠ Could not load score trend: {e}")
            return None
