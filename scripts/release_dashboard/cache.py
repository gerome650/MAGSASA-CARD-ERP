"""
Cache Module

Handles JSON caching for readiness analytics and trending.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class ReadinessCache:
    """Manages JSON cache for readiness score history."""

    def __init__(
        self, cache_file: str = ".cache/readiness.json", verbose: bool = False
    ):
        """
        Initialize the cache manager.

        Args:
            cache_file: Path to JSON cache file
            verbose: Enable verbose logging
        """
        self.cache_path = Path(cache_file)
        self.verbose = verbose

        # Ensure cache directory exists
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> list[dict[str, Any]]:
        """
        Load history from cache file.

        Returns:
            List of historical score entries
        """
        try:
            if not self.cache_path.exists():
                if self.verbose:
                    print("ℹ No cache file found, starting fresh")
                return []

            with open(self.cache_path, encoding="utf-8") as f:
                data = json.load(f)

            if self.verbose:
                print(f"✓ Loaded {len(data)} entries from cache")

            return data

        except json.JSONDecodeError as e:
            if self.verbose:
                print(f"⚠ Cache file corrupted, starting fresh: {e}")
            return []
        except Exception as e:
            if self.verbose:
                print(f"⚠ Error loading cache: {e}")
            return []

    def save(self, history: list[dict[str, Any]]) -> bool:
        """
        Save history to cache file.

        Args:
            history: List of score entries to save

        Returns:
            True if saved successfully
        """
        try:
            # Limit history to last 100 entries to prevent unbounded growth
            limited_history = history[-100:] if len(history) > 100 else history

            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(limited_history, f, indent=2)

            if self.verbose:
                print(f"✓ Saved {len(limited_history)} entries to cache")

            return True

        except Exception as e:
            if self.verbose:
                print(f"✗ Error saving cache: {e}")
            return False

    def append_entry(self, score_data: dict[str, Any]) -> bool:
        """
        Append a new score entry to history.

        Args:
            score_data: Score data to append

        Returns:
            True if appended successfully
        """
        history = self.load()

        entry = {
            "timestamp": datetime.now().isoformat(),
            "score": score_data["total_score"],
            "status": score_data["status"],
            "core_score": score_data["core_score"],
            "optional_score": score_data["optional_score"],
            "deployment_score": score_data["deployment_score"],
            "signoff_score": score_data["signoff_score"],
            "blockers_count": len(score_data.get("blockers", [])),
            "ci_adjustment": score_data.get("ci_adjustment", 0),
        }

        history.append(entry)
        return self.save(history)

    def get_trend(self, lookback: int = 10) -> dict[str, Any] | None:
        """
        Get score trend over recent entries.

        Args:
            lookback: Number of entries to analyze

        Returns:
            Trend analysis data
        """
        history = self.load()

        if len(history) < 2:
            return None

        recent = history[-lookback:] if len(history) >= lookback else history

        scores = [entry["score"] for entry in recent]
        current = scores[-1]
        previous = scores[-2] if len(scores) >= 2 else current

        # Calculate trend
        if len(scores) >= 3:
            # Simple linear trend
            first_half_avg = sum(scores[: len(scores) // 2]) / (len(scores) // 2)
            second_half_avg = sum(scores[len(scores) // 2 :]) / (
                len(scores) - len(scores) // 2
            )

            if second_half_avg > first_half_avg + 2:
                trend = "improving"
                trend_emoji = "📈"
            elif second_half_avg < first_half_avg - 2:
                trend = "declining"
                trend_emoji = "📉"
            else:
                trend = "stable"
                trend_emoji = "➡️"
        else:
            change = current - previous
            if change > 1:
                trend = "improving"
                trend_emoji = "📈"
            elif change < -1:
                trend = "declining"
                trend_emoji = "📉"
            else:
                trend = "stable"
                trend_emoji = "➡️"

        return {
            "current": current,
            "previous": previous,
            "change": round(current - previous, 1),
            "trend": trend,
            "trend_emoji": trend_emoji,
            "min": round(min(scores), 1),
            "max": round(max(scores), 1),
            "avg": round(sum(scores) / len(scores), 1),
            "entries_analyzed": len(recent),
        }

    def export_csv(self, output_file: str = ".cache/readiness_history.csv") -> bool:
        """
        Export history to CSV format.

        Args:
            output_file: Path to output CSV file

        Returns:
            True if exported successfully
        """
        history = self.load()

        if not history:
            if self.verbose:
                print("⚠ No history to export")
            return False

        try:
            import csv

            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", newline="", encoding="utf-8") as f:
                fieldnames = [
                    "timestamp",
                    "score",
                    "status",
                    "core_score",
                    "optional_score",
                    "deployment_score",
                    "signoff_score",
                    "blockers_count",
                    "ci_adjustment",
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                writer.writeheader()
                writer.writerows(history)

            if self.verbose:
                print(f"✓ Exported {len(history)} entries to {output_path}")

            return True

        except Exception as e:
            if self.verbose:
                print(f"✗ Error exporting to CSV: {e}")
            return False

    def clear(self) -> bool:
        """
        Clear the cache file.

        Returns:
            True if cleared successfully
        """
        try:
            if self.cache_path.exists():
                self.cache_path.unlink()
                if self.verbose:
                    print("✓ Cache cleared")
            return True
        except Exception as e:
            if self.verbose:
                print(f"✗ Error clearing cache: {e}")
            return False
