#!/usr/bin/env python3
"""
📈 Coverage Trend Tracker & Reporter

Tracks coverage history and generates trend reports with:
- Historical coverage data analysis
- Sparkline generation for visual trends
- Coverage delta calculations
- Trend prediction and alerts
- Integration with governance reporting

Usage:
    python scripts/metrics/coverage_trend.py --report
    python scripts/metrics/coverage_trend.py --add-coverage 87.5 --pr-number 42
    python scripts/metrics/coverage_trend.py --generate-sparkline
    python scripts/metrics/coverage_trend.py --predict-trend
"""

import argparse
import json
import logging
import statistics
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class CoverageTrendTracker:
    """Track and analyze coverage trends over time."""

    def __init__(self, history_file: Path | None = None, verbose: bool = False):
        """Initialize coverage trend tracker.

        Args:
            history_file: Path to coverage history JSON file
            verbose: Whether to enable verbose logging
        """
        self.history_file = history_file or Path(".ci/coverage_history.json")
        self.verbose = verbose
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.history = self._load_history()

    def _load_history(self) -> dict[str, Any]:
        """Load coverage history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file) as f:
                    data = json.load(f)
                    if self.verbose:
                        logger.info(
                            f"Loaded coverage history: {len(data.get('entries', []))} entries"
                        )
                    return data
            except (OSError, json.JSONDecodeError) as e:
                logger.warning(f"Could not load coverage history: {e}")
                return {
                    "entries": [],
                    "metadata": {"created": datetime.now().isoformat()},
                }
        else:
            if self.verbose:
                logger.info("No coverage history file found, starting fresh")
            return {"entries": [], "metadata": {"created": datetime.now().isoformat()}}

    def _save_history(self) -> bool:
        """Save coverage history to file."""
        try:
            # Update metadata
            self.history["metadata"]["last_updated"] = datetime.now().isoformat()
            self.history["metadata"]["total_entries"] = len(self.history["entries"])

            with open(self.history_file, "w") as f:
                json.dump(self.history, f, indent=2)

            if self.verbose:
                logger.info(f"Coverage history saved: {self.history_file}")
            return True
        except OSError as e:
            logger.error(f"Could not save coverage history: {e}")
            return False

    def add_coverage_entry(
        self,
        coverage: float,
        pr_number: str | None = None,
        commit_hash: str | None = None,
    ) -> bool:
        """Add a coverage entry to history.

        Args:
            coverage: Coverage percentage (0-100)
            pr_number: Optional PR number
            commit_hash: Optional commit hash

        Returns:
            True if successful
        """
        try:
            entry = {
                "coverage": coverage,
                "timestamp": datetime.now().isoformat(),
                "pr_number": pr_number,
                "commit_hash": commit_hash,
            }
            self.history["entries"].append(entry)

            # Keep only last 100 entries
            if len(self.history["entries"]) > 100:
                self.history["entries"] = self.history["entries"][-100:]
                if self.verbose:
                    logger.info("Trimmed coverage history to last 100 entries")

            return self._save_history()
        except Exception as e:
            logger.error(f"Failed to add coverage entry: {e}")
            return False

    def get_coverage_trend(self, days: int = 30) -> dict[str, Any]:
        """Get coverage trend analysis for the specified period.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with trend analysis
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_entries = []

        for entry in self.history["entries"]:
            try:
                entry_date = datetime.fromisoformat(entry["timestamp"])
                if entry_date >= cutoff_date:
                    recent_entries.append(entry)
            except ValueError:
                continue

        if not recent_entries:
            return {
                "period_days": days,
                "entries_count": 0,
                "current_coverage": None,
                "previous_coverage": None,
                "trend_direction": "unknown",
                "trend_magnitude": 0.0,
                "average_coverage": None,
                "min_coverage": None,
                "max_coverage": None,
                "volatility": None,
            }

        # Sort by timestamp
        recent_entries.sort(key=lambda x: x["timestamp"])

        # Calculate trend metrics
        current_coverage = recent_entries[-1]["coverage"]
        previous_coverage = (
            recent_entries[0]["coverage"]
            if len(recent_entries) > 1
            else current_coverage
        )

        coverage_values = [entry["coverage"] for entry in recent_entries]
        average_coverage = statistics.mean(coverage_values)
        min_coverage = min(coverage_values)
        max_coverage = max(coverage_values)

        # Calculate trend direction and magnitude
        trend_magnitude = current_coverage - previous_coverage
        if abs(trend_magnitude) < 0.1:
            trend_direction = "stable"
        elif trend_magnitude > 0:
            trend_direction = "improving"
        else:
            trend_direction = "declining"

        # Calculate volatility (standard deviation)
        volatility = (
            statistics.stdev(coverage_values) if len(coverage_values) > 1 else 0.0
        )

        return {
            "period_days": days,
            "entries_count": len(recent_entries),
            "current_coverage": current_coverage,
            "previous_coverage": previous_coverage,
            "trend_direction": trend_direction,
            "trend_magnitude": trend_magnitude,
            "average_coverage": average_coverage,
            "min_coverage": min_coverage,
            "max_coverage": max_coverage,
            "volatility": volatility,
        }

    def generate_sparkline(
        self, entries: list[dict] | None = None, width: int = 20
    ) -> str:
        """Generate a sparkline visualization of coverage trend.

        Args:
            entries: Coverage entries (uses recent entries if None)
            width: Width of sparkline in characters

        Returns:
            Sparkline string
        """
        if entries is None:
            entries = self.history["entries"][
                -width * 2 :
            ]  # Get more entries than width for better resolution

        if not entries:
            return "─" * width  # Flat line if no data

        # Sort by timestamp
        entries.sort(key=lambda x: x["timestamp"])

        # Get coverage values
        coverage_values = [entry["coverage"] for entry in entries]

        if len(coverage_values) < 2:
            return "─" * width

        min_val = min(coverage_values)
        max_val = max(coverage_values)

        if max_val == min_val:
            return "─" * width

        # Sparkline characters (Unicode)
        spark_chars = "▁▂▃▄▅▆▇█"

        # Generate sparkline
        sparkline = ""
        for i in range(width):
            # Map coverage to sparkline height
            if i < len(coverage_values):
                val = coverage_values[i]
                normalized = (val - min_val) / (max_val - min_val)
                char_index = int(normalized * (len(spark_chars) - 1))
                sparkline += spark_chars[char_index]
            else:
                sparkline += "─"

        return sparkline

    def predict_trend(self, days_ahead: int = 7) -> dict[str, Any]:
        """Predict coverage trend for the next few days.

        Args:
            days_ahead: Number of days to predict ahead

        Returns:
            Dictionary with prediction results
        """
        entries = self.history["entries"]

        if len(entries) < 3:
            return {
                "prediction_available": False,
                "reason": "Insufficient data for prediction",
                "days_ahead": days_ahead,
            }

        # Sort by timestamp
        entries.sort(key=lambda x: x["timestamp"])

        # Get recent coverage values
        recent_coverage = [
            entry["coverage"] for entry in entries[-10:]
        ]  # Last 10 entries

        try:
            # Simple linear regression for trend prediction
            x = list(range(len(recent_coverage)))
            y = recent_coverage

            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(x[i] ** 2 for i in range(n))

            # Calculate slope and intercept
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)
            (sum_y - slope * sum_x) / n

            # Predict future values
            current_coverage = recent_coverage[-1]
            predicted_coverage = current_coverage + slope * days_ahead

            # Calculate confidence based on recent volatility
            volatility = (
                statistics.stdev(recent_coverage) if len(recent_coverage) > 1 else 0.0
            )
            confidence = max(
                0.0, 1.0 - (volatility / 10.0)
            )  # Higher volatility = lower confidence

            return {
                "prediction_available": True,
                "current_coverage": current_coverage,
                "predicted_coverage": predicted_coverage,
                "trend_slope": slope,
                "confidence": confidence,
                "days_ahead": days_ahead,
                "volatility": volatility,
            }
        except Exception as e:
            return {
                "prediction_available": False,
                "reason": f"Prediction error: {e}",
                "days_ahead": days_ahead,
            }

    def generate_report(self, days: int = 30) -> str:
        """Generate a comprehensive coverage trend report.

        Args:
            days: Number of days to analyze

        Returns:
            Formatted report string
        """
        trend_data = self.get_coverage_trend(days)
        sparkline = self.generate_sparkline(width=30)
        prediction = self.predict_trend()

        report_lines = [
            "📈 Coverage Trend Report",
            "=" * 50,
            "",
            f"📊 Analysis Period: {days} days",
            f"📝 Data Points: {trend_data['entries_count']}",
            "",
        ]

        if trend_data["entries_count"] > 0:
            report_lines.extend(
                [
                    f"📈 Current Coverage: {trend_data['current_coverage']:.1f}%",
                    f"📊 Average Coverage: {trend_data['average_coverage']:.1f}%",
                    f"📉 Min Coverage: {trend_data['min_coverage']:.1f}%",
                    f"📈 Max Coverage: {trend_data['max_coverage']:.1f}%",
                    "",
                    f"🎯 Trend: {trend_data['trend_direction'].title()} ({trend_data['trend_magnitude']:+.1f}%)",
                    f"📊 Volatility: {trend_data['volatility']:.1f}%",
                    "",
                    f"📈 Sparkline: {sparkline}",
                    "",
                ]
            )

            if prediction["prediction_available"]:
                report_lines.extend(
                    [
                        "🔮 Trend Prediction:",
                        f"   Predicted coverage in {prediction['days_ahead']} days: {prediction['predicted_coverage']:.1f}%",
                        f"   Confidence: {prediction['confidence']:.1%}",
                        f"   Trend slope: {prediction['trend_slope']:.3f}",
                        "",
                    ]
                )
            else:
                report_lines.extend(
                    [
                        "🔮 Trend Prediction: Not available",
                        f"   Reason: {prediction['reason']}",
                        "",
                    ]
                )
        else:
            report_lines.extend(["⚠️  No coverage data available for analysis", ""])

        report_lines.extend(
            [f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "=" * 50]
        )

        return "\n".join(report_lines)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Coverage trend tracker and reporter")
    parser.add_argument(
        "--report", action="store_true", help="Generate coverage trend report"
    )
    parser.add_argument("--add-coverage", type=float, help="Add coverage entry")
    parser.add_argument("--pr-number", help="PR number for coverage entry")
    parser.add_argument("--commit-hash", help="Commit hash for coverage entry")
    parser.add_argument(
        "--generate-sparkline", action="store_true", help="Generate sparkline"
    )
    parser.add_argument(
        "--predict-trend", action="store_true", help="Predict future trend"
    )
    parser.add_argument(
        "--days", type=int, default=30, help="Days to analyze (default: 30)"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--history-file", type=Path, help="Path to coverage history file"
    )

    args = parser.parse_args()

    tracker = CoverageTrendTracker(history_file=args.history_file, verbose=args.verbose)

    try:
        if args.add_coverage is not None:
            success = tracker.add_coverage_entry(
                coverage=args.add_coverage,
                pr_number=args.pr_number,
                commit_hash=args.commit_hash,
            )
            if success:
                print(f"✅ Added coverage entry: {args.add_coverage:.1f}%")
            else:
                print("❌ Failed to add coverage entry")
                sys.exit(1)

        if args.generate_sparkline:
            sparkline = tracker.generate_sparkline()
            print(f"📈 Coverage Sparkline: {sparkline}")

        if args.predict_trend:
            prediction = tracker.predict_trend()
            if prediction["prediction_available"]:
                print(
                    f"🔮 Predicted coverage in {prediction['days_ahead']} days: {prediction['predicted_coverage']:.1f}%"
                )
                print(f"📊 Confidence: {prediction['confidence']:.1%}")
            else:
                print(f"⚠️  Prediction not available: {prediction['reason']}")

        if args.report:
            report = tracker.generate_report(args.days)
            print(report)

        # If no specific action requested, show basic status
        if not any(
            [
                args.report,
                args.add_coverage,
                args.generate_sparkline,
                args.predict_trend,
            ]
        ):
            trend_data = tracker.get_coverage_trend(args.days)
            if trend_data["entries_count"] > 0:
                sparkline = tracker.generate_sparkline(width=20)
                print(
                    f"📈 Coverage Trend: {trend_data['trend_direction']} ({trend_data['trend_magnitude']:+.1f}%)"
                )
                print(
                    f"📊 Current: {trend_data['current_coverage']:.1f}% | Sparkline: {sparkline}"
                )
            else:
                print("📊 No coverage data available")

        sys.exit(0)

    except Exception as e:
        logger.error(f"Coverage trend operation failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
