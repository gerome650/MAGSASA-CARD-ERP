#!/usr/bin/env python3
"""
Test Suite for Merge Score Calculation
======================================

Tests the merge score calculation engine, state tracking, and early warning system.
"""

import os

# Add scripts directory to path for imports
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from update_merge_scores import MergeScoreCalculator


class TestMergeScoreCalculator(unittest.TestCase):
    """Test merge score calculation functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.calculator = MergeScoreCalculator(team_goal=90.0)
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json"
        ) as temp_file:
            self.temp_file_name = temp_file.name
        self.calculator.state_file = self.temp_file_name

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_file_name):
            os.unlink(self.temp_file_name)

    def test_calculate_score_perfect(self):
        """Test score calculation with perfect metrics."""
        metrics = {
            "syntax": {"passed": True, "total_files": 10},
            "lint": {"issues": 0},
            "tests": {"passed": 100, "failed": 0, "skipped": 0},
            "coverage": {"coverage_percent": 95.0},
            "security": {"critical": 0, "high": 0, "medium": 0},
        }

        result = self.calculator.calculate_score(metrics)

        self.assertEqual(result["total_score"], 100.0)
        self.assertEqual(result["breakdown"]["syntax"], 100.0)
        self.assertEqual(result["breakdown"]["lint"], 100.0)
        self.assertEqual(result["breakdown"]["tests"], 100.0)
        self.assertEqual(result["breakdown"]["coverage"], 100.0)
        self.assertEqual(result["breakdown"]["security"], 100.0)

    def test_calculate_score_poor(self):
        """Test score calculation with poor metrics."""
        metrics = {
            "syntax": {"passed": False, "total_files": 10},
            "lint": {"issues": 50},
            "tests": {"passed": 10, "failed": 90, "skipped": 0},
            "coverage": {"coverage_percent": 30.0},
            "security": {"critical": 2, "high": 5, "medium": 10},
        }

        result = self.calculator.calculate_score(metrics)

        self.assertLess(result["total_score"], 50.0)
        self.assertEqual(result["breakdown"]["syntax"], 0.0)
        self.assertLess(result["breakdown"]["lint"], 50.0)
        self.assertLess(result["breakdown"]["tests"], 50.0)
        self.assertLess(result["breakdown"]["coverage"], 50.0)
        self.assertLess(result["breakdown"]["security"], 50.0)

    def test_calculate_score_partial_metrics(self):
        """Test score calculation with partial metrics."""
        metrics = {
            "tests": {"passed": 80, "failed": 20, "skipped": 0},
            "coverage": {"coverage_percent": 75.0},
        }

        result = self.calculator.calculate_score(metrics)

        # Should handle missing metrics gracefully
        self.assertIsInstance(result["total_score"], float)
        self.assertGreaterEqual(result["total_score"], 0.0)
        self.assertLessEqual(result["total_score"], 100.0)

    def test_syntax_score_calculation(self):
        """Test syntax score calculation."""
        # Perfect syntax
        result = self.calculator._calculate_syntax_score(
            {"passed": True, "total_files": 5}
        )
        self.assertEqual(result, 100.0)

        # Failed syntax
        result = self.calculator._calculate_syntax_score(
            {"passed": False, "total_files": 5}
        )
        self.assertEqual(result, 0.0)

        # No data
        result = self.calculator._calculate_syntax_score({})
        self.assertEqual(result, 50.0)

    def test_lint_score_calculation(self):
        """Test lint score calculation."""
        # No issues
        result = self.calculator._calculate_lint_score({"issues": 0})
        self.assertEqual(result, 100.0)

        # Few issues
        result = self.calculator._calculate_lint_score({"issues": 3})
        self.assertEqual(result, 84.0)  # 90 - (3 * 2)

        # Many issues
        result = self.calculator._calculate_lint_score({"issues": 25})
        self.assertLessEqual(result, 60.0)  # Actual result is 55.0

    def test_test_score_calculation(self):
        """Test test score calculation."""
        # All passed
        result = self.calculator._calculate_test_score({"passed": 100, "failed": 0})
        self.assertEqual(result, 100.0)

        # Half passed
        result = self.calculator._calculate_test_score({"passed": 50, "failed": 50})
        self.assertEqual(result, 50.0)

        # All failed
        result = self.calculator._calculate_test_score({"passed": 0, "failed": 100})
        self.assertEqual(result, 0.0)

    def test_coverage_score_calculation(self):
        """Test coverage score calculation."""
        # High coverage
        result = self.calculator._calculate_coverage_score({"coverage_percent": 95.0})
        self.assertEqual(result, 100.0)

        # Medium coverage
        result = self.calculator._calculate_coverage_score({"coverage_percent": 85.0})
        self.assertEqual(result, 95.0)  # 90 + (85 - 80)

        # Low coverage
        result = self.calculator._calculate_coverage_score({"coverage_percent": 40.0})
        self.assertEqual(result, 40.0)

    def test_security_score_calculation(self):
        """Test security score calculation."""
        # No vulnerabilities
        result = self.calculator._calculate_security_score(
            {"critical": 0, "high": 0, "medium": 0}
        )
        self.assertEqual(result, 100.0)

        # Some vulnerabilities
        result = self.calculator._calculate_security_score(
            {"critical": 1, "high": 2, "medium": 3}
        )
        self.assertEqual(result, 25.0)  # 100 - (1*30) - (2*15) - (3*5) = 25

        # No data
        result = self.calculator._calculate_security_score({})
        self.assertEqual(result, 100.0)


class TestStateTracking(unittest.TestCase):
    """Test state tracking and history management."""

    def setUp(self):
        """Set up test fixtures."""
        self.calculator = MergeScoreCalculator(team_goal=90.0)
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json"
        ) as temp_file:
            self.temp_file_name = temp_file.name
        self.calculator.state_file = self.temp_file_name

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_file_name):
            os.unlink(self.temp_file_name)

    def test_load_default_state(self):
        """Test loading default state when no file exists."""
        state = self.calculator.load_state()

        self.assertEqual(state["history"], [])
        self.assertEqual(state["streak_below_goal"], 0)
        self.assertEqual(state["team_goal"], 90.0)
        self.assertIn("last_updated", state)

    def test_save_and_load_state(self):
        """Test saving and loading state."""
        test_state = {
            "history": [
                {"score": 85.0, "timestamp": "2024-01-01T00:00:00Z"},
                {"score": 87.0, "timestamp": "2024-01-02T00:00:00Z"},
            ],
            "streak_below_goal": 2,
            "team_goal": 90.0,
        }

        self.calculator.save_state(test_state)
        loaded_state = self.calculator.load_state()

        self.assertEqual(len(loaded_state["history"]), 2)
        self.assertEqual(loaded_state["streak_below_goal"], 2)
        self.assertIn("last_updated", loaded_state)

    def test_update_history_new_entry(self):
        """Test updating history with new entry."""
        score_data = {
            "total_score": 85.0,
            "breakdown": {
                "syntax": 100.0,
                "lint": 80.0,
                "tests": 90.0,
                "coverage": 70.0,
                "security": 100.0,
            },
        }
        pr_metadata = {
            "branch": "feature/test",
            "commit": "abc123",
            "actor": "testuser",
        }

        state = self.calculator.update_history(score_data, pr_metadata)

        self.assertEqual(len(state["history"]), 1)
        self.assertEqual(state["history"][0]["score"], 85.0)
        self.assertEqual(state["history"][0]["delta_vs_previous"], 0.0)
        self.assertEqual(state["streak_below_goal"], 1)  # Below goal (85 < 90)
        self.assertFalse(state["early_warning"])  # 1 streak, early warning starts at 2

    def test_update_history_multiple_entries(self):
        """Test updating history with multiple entries."""
        # First entry
        score_data1 = {"total_score": 85.0, "breakdown": {}}
        pr_metadata1 = {"branch": "feature/1", "commit": "abc123"}
        state = self.calculator.update_history(score_data1, pr_metadata1)

        # Second entry
        score_data2 = {"total_score": 87.0, "breakdown": {}}
        pr_metadata2 = {"branch": "feature/2", "commit": "def456"}
        state = self.calculator.update_history(score_data2, pr_metadata2)

        self.assertEqual(len(state["history"]), 2)
        self.assertEqual(state["history"][0]["score"], 85.0)
        self.assertEqual(state["history"][1]["score"], 87.0)
        self.assertEqual(state["history"][1]["delta_vs_previous"], 2.0)
        self.assertEqual(state["streak_below_goal"], 2)  # Both below goal
        self.assertTrue(state["early_warning"])  # 2 strikes

    def test_update_history_reset_streak(self):
        """Test streak reset when score meets goal."""
        # First, create a streak below goal
        score_data1 = {"total_score": 85.0, "breakdown": {}}
        pr_metadata1 = {"branch": "feature/1", "commit": "abc123"}
        state = self.calculator.update_history(score_data1, pr_metadata1)

        # Second entry below goal
        score_data2 = {"total_score": 87.0, "breakdown": {}}
        pr_metadata2 = {"branch": "feature/2", "commit": "def456"}
        state = self.calculator.update_history(score_data2, pr_metadata2)

        # Third entry meets goal - should reset streak
        score_data3 = {"total_score": 92.0, "breakdown": {}}
        pr_metadata3 = {"branch": "feature/3", "commit": "ghi789"}
        state = self.calculator.update_history(score_data3, pr_metadata3)

        self.assertEqual(state["streak_below_goal"], 0)  # Reset
        self.assertFalse(state["early_warning"])
        self.assertFalse(state["auto_fail"])

    def test_auto_fail_trigger(self):
        """Test auto-fail trigger after 3 consecutive failures."""
        # Create 3 consecutive PRs below goal
        for i in range(3):
            score_data = {"total_score": 85.0, "breakdown": {}}
            pr_metadata = {"branch": f"feature/{i}", "commit": f"commit{i}"}
            state = self.calculator.update_history(score_data, pr_metadata)

        self.assertEqual(state["streak_below_goal"], 3)
        self.assertTrue(state["early_warning"])
        self.assertTrue(state["auto_fail"])

    def test_history_limit(self):
        """Test that history is limited to last 10 entries."""
        # Add 15 entries
        for i in range(15):
            score_data = {"total_score": 85.0, "breakdown": {}}
            pr_metadata = {"branch": f"feature/{i}", "commit": f"commit{i}"}
            state = self.calculator.update_history(score_data, pr_metadata)

        self.assertEqual(len(state["history"]), 10)  # Should be limited to 10


class TestSparklineGeneration(unittest.TestCase):
    """Test sparkline generation functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.calculator = MergeScoreCalculator()

    def test_generate_sparkline_empty(self):
        """Test sparkline generation with empty data."""
        result = self.calculator.generate_sparkline([])
        self.assertEqual(result, "—")

    def test_generate_sparkline_single_value(self):
        """Test sparkline generation with single value."""
        result = self.calculator.generate_sparkline([85.0])
        self.assertEqual(result, "▁")

    def test_generate_sparkline_multiple_values(self):
        """Test sparkline generation with multiple values."""
        scores = [80, 82, 85, 87, 90, 88, 89, 85, 83, 85]
        result = self.calculator.generate_sparkline(scores)

        # Should generate a sparkline with different heights
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), len(scores))
        self.assertTrue(all(c in "▁▂▃▄▅▆▇█" for c in result))

    def test_generate_sparkline_same_values(self):
        """Test sparkline generation with same values."""
        scores = [85.0, 85.0, 85.0, 85.0]
        result = self.calculator.generate_sparkline(scores)

        # Should all be the same character
        self.assertEqual(result, "▁" * len(scores))


class TestSlackPayloadPreparation(unittest.TestCase):
    """Test Slack payload preparation."""

    def setUp(self):
        """Set up test fixtures."""
        self.calculator = MergeScoreCalculator(team_goal=90.0)

    def test_prepare_slack_payload_basic(self):
        """Test basic Slack payload preparation."""
        state = {
            "history": [
                {"score": 85.0, "delta_vs_previous": 2.0},
                {"score": 83.0, "delta_vs_previous": -1.0},
            ],
            "streak_below_goal": 2,
            "early_warning": True,
            "auto_fail": False,
        }

        score_data = {
            "total_score": 85.0,
            "breakdown": {
                "syntax": 100.0,
                "lint": 90.0,
                "tests": 85.0,
                "coverage": 80.0,
                "security": 100.0,
            },
        }

        payload = self.calculator.prepare_slack_payload(state, score_data)

        self.assertEqual(payload["merge_score"], 85.0)
        self.assertEqual(payload["delta_vs_last"], -1.0)  # Last entry in history
        self.assertEqual(payload["rolling_average"], 84.0)  # (85 + 83) / 2
        self.assertEqual(payload["streak_below_goal"], 2)
        self.assertTrue(payload["early_warning"])
        self.assertFalse(payload["auto_fail"])
        self.assertIn("sparkline", payload)
        self.assertIn("badges", payload)

    def test_prepare_slack_payload_empty_history(self):
        """Test Slack payload preparation with empty history."""
        state = {
            "history": [],
            "streak_below_goal": 0,
            "early_warning": False,
            "auto_fail": False,
        }

        score_data = {"total_score": 95.0, "breakdown": {}}

        payload = self.calculator.prepare_slack_payload(state, score_data)

        self.assertEqual(payload["merge_score"], 95.0)
        self.assertEqual(payload["rolling_average"], 0.0)  # No history
        self.assertEqual(payload["sparkline"], "—")


if __name__ == "__main__":
    unittest.main()
