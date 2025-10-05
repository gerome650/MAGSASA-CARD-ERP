#!/usr/bin/env python3
"""
CI/CD Failure Analyzer - Intelligent Failure Diagnosis and Auto-Fix Suggestions

This script analyzes CI/CD failure logs and provides intelligent diagnosis,
root cause analysis, and recommended fixes. It can be run standalone or
integrated into GitHub Actions workflows.

Stage 7.1 Enhancement: Adds historical tracking, success rate analysis,
MTTR tracking, and trending labels for intelligent self-healing.

Usage:
    python scripts/analyze_ci_failure.py --ci
    python scripts/analyze_ci_failure.py --analyze-latest
    python scripts/analyze_ci_failure.py --job-logs /path/to/logs
"""

import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


@dataclass
class FailureAnalysis:
    """Structured failure analysis result."""

    category: str
    severity: str
    root_cause: str
    recommended_fix: str
    affected_files: list[str]
    confidence: float
    auto_fixable: bool
    fix_command: str | None = None
    documentation_links: list[str] = None
    error_signature: str | None = None  # Unique hash for tracking
    frequency: int = 0  # How many times this error has occurred
    success_rate: float = 0.0  # Historical fix success rate
    avg_mttr_minutes: float = 0.0  # Average Mean Time To Recovery
    trend: str = "stable"  # rising, improving, stable


class HistoricalDatabase:
    """Manages historical failure and fix data using SQLite."""

    def __init__(self, db_path: str = "ci_failure_history.db"):
        """Initialize database connection and create tables if needed."""
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path))
        self._create_tables()

    def _create_tables(self):
        """Create necessary database tables."""
        cursor = self.conn.cursor()

        # Failures table - tracks all failure occurrences
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS failures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                job_name TEXT,
                branch TEXT,
                category TEXT NOT NULL,
                error_signature TEXT NOT NULL,
                severity TEXT,
                root_cause TEXT,
                confidence REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Fix attempts table - tracks all fix attempts
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS fix_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                failure_id INTEGER,
                timestamp TEXT NOT NULL,
                fix_strategy TEXT NOT NULL,
                fix_command TEXT,
                success INTEGER NOT NULL,
                resolution_time_minutes REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (failure_id) REFERENCES failures(id)
            )
        """
        )

        # Indices for faster queries
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_error_signature
            ON failures(error_signature)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_category
            ON failures(category)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON failures(timestamp)
        """
        )

        self.conn.commit()

    def record_failure(
        self, analysis: FailureAnalysis, job_name: str = None, branch: str = None
    ) -> int:
        """Record a failure occurrence and return its ID."""
        cursor = self.conn.cursor()

        cursor.execute(
            """
            INSERT INTO failures (timestamp, job_name, branch, category,
                                error_signature, severity, root_cause, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                datetime.now().isoformat(),
                job_name,
                branch,
                analysis.category,
                analysis.error_signature,
                analysis.severity,
                analysis.root_cause,
                analysis.confidence,
            ),
        )

        self.conn.commit()
        return cursor.lastrowid

    def record_fix_attempt(
        self,
        failure_id: int,
        fix_strategy: str,
        fix_command: str,
        success: bool,
        resolution_time_minutes: float = None,
    ):
        """Record a fix attempt."""
        cursor = self.conn.cursor()

        cursor.execute(
            """
            INSERT INTO fix_attempts (failure_id, timestamp, fix_strategy,
                                     fix_command, success, resolution_time_minutes)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                failure_id,
                datetime.now().isoformat(),
                fix_strategy,
                fix_command,
                1 if success else 0,
                resolution_time_minutes,
            ),
        )

        self.conn.commit()

    def get_failure_stats(self, error_signature: str, days: int = 30) -> dict[str, Any]:
        """Get historical stats for a specific error signature."""
        cursor = self.conn.cursor()

        since_date = (datetime.now() - timedelta(days=days)).isoformat()

        # Get frequency
        cursor.execute(
            """
            SELECT COUNT(*) as frequency
            FROM failures
            WHERE error_signature = ? AND timestamp >= ?
        """,
            (error_signature, since_date),
        )

        result = cursor.fetchone()
        frequency = result[0] if result else 0

        # Get success rate from fix attempts
        cursor.execute(
            """
            SELECT
                COUNT(*) as total_attempts,
                SUM(success) as successful_attempts,
                AVG(CASE WHEN success = 1 THEN resolution_time_minutes END) as avg_mttr
            FROM fix_attempts fa
            JOIN failures f ON fa.failure_id = f.id
            WHERE f.error_signature = ? AND f.timestamp >= ?
        """,
            (error_signature, since_date),
        )

        result = cursor.fetchone()
        total_attempts = result[0] if result and result[0] else 0
        successful_attempts = result[1] if result and result[1] else 0
        avg_mttr = result[2] if result and result[2] else 0.0

        success_rate = (
            (successful_attempts / total_attempts) if total_attempts > 0 else 0.0
        )

        return {
            "frequency": frequency,
            "success_rate": success_rate,
            "avg_mttr_minutes": avg_mttr or 0.0,
            "total_attempts": total_attempts,
        }

    def get_trend(self, error_signature: str, category: str) -> str:
        """Determine if an error is rising, improving, or stable."""
        cursor = self.conn.cursor()

        # Compare last 7 days vs previous 7 days
        last_week = (datetime.now() - timedelta(days=7)).isoformat()
        prev_week = (datetime.now() - timedelta(days=14)).isoformat()

        cursor.execute(
            """
            SELECT COUNT(*) FROM failures
            WHERE error_signature = ? AND timestamp >= ?
        """,
            (error_signature, last_week),
        )
        recent_count = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*) FROM failures
            WHERE error_signature = ?
            AND timestamp >= ? AND timestamp < ?
        """,
            (error_signature, prev_week, last_week),
        )
        previous_count = cursor.fetchone()[0]

        if recent_count > previous_count * 1.5:
            return "rising"
        elif recent_count < previous_count * 0.5:
            return "improving"
        else:
            return "stable"

    def get_top_failures(self, days: int = 7, limit: int = 10) -> list[dict[str, Any]]:
        """Get top failures by frequency in the given period."""
        cursor = self.conn.cursor()

        since_date = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute(
            """
            SELECT
                category,
                error_signature,
                COUNT(*) as frequency,
                MAX(timestamp) as last_occurrence,
                AVG(confidence) as avg_confidence
            FROM failures
            WHERE timestamp >= ?
            GROUP BY category, error_signature
            ORDER BY frequency DESC
            LIMIT ?
        """,
            (since_date, limit),
        )

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "category": row[0],
                    "error_signature": row[1],
                    "frequency": row[2],
                    "last_occurrence": row[3],
                    "avg_confidence": row[4],
                }
            )

        return results

    def close(self):
        """Close database connection."""
        self.conn.close()


class CIFailureAnalyzer:
    """Intelligent CI/CD failure analyzer with ML-inspired pattern recognition."""

    def __init__(
        self, use_history: bool = True, db_path: str = "ci_failure_history.db"
    ):
        """Initialize analyzer with optional historical tracking."""
        self.use_history = use_history
        self.db = HistoricalDatabase(db_path) if use_history else None
        self.failure_patterns = {
            "dependency": {
                "patterns": [
                    r"ModuleNotFoundError: No module named \'([^\']+)\'",
                    r"ImportError: cannot import name \'([^\']+)\'",
                    r"pip install ([^\s]+)",
                    r"No module named \'([^\']+)\'",
                    r"PackageNotFoundError",
                    r"Could not find a version that satisfies the requirement",
                    r"ERROR: Could not install packages",
                    r"Requirement already satisfied but import fails",
                ],
                "severity": "high",
                "auto_fixable": True,
            },
            "test_assertion": {
                "patterns": [
                    r"AssertionError",
                    r"FAILED.*test_.*\.py",
                    r"assert.*failed",
                    r"Expected.*but got",
                    r"Test.*failed",
                ],
                "severity": "medium",
                "auto_fixable": False,
            },
            "network_timeout": {
                "patterns": [
                    r"ReadTimeoutError",
                    r"ConnectionTimeout",
                    r"HTTPSConnectionPool.*timeout",
                    r"requests\.exceptions\.Timeout",
                    r"Connection timed out",
                    r"504 Gateway Timeout",
                    r"502 Bad Gateway",
                ],
                "severity": "low",
                "auto_fixable": True,
            },
            "missing_file": {
                "patterns": [
                    r"FileNotFoundError: \[Errno 2\] No such file or directory",
                    r"No such file or directory: \'([^\']+)\'",
                    r"Could not find file",
                    r"Missing file:",
                    r"File does not exist",
                ],
                "severity": "high",
                "auto_fixable": True,
            },
            "schema_validation": {
                "patterns": [
                    r"jsonschema\.exceptions\.ValidationError",
                    r"YAMLError",
                    r"Invalid YAML",
                    r"Schema validation failed",
                    r"Invalid configuration",
                    r"ValidationError",
                ],
                "severity": "medium",
                "auto_fixable": False,
            },
            "permission": {
                "patterns": [
                    r"Permission denied",
                    r"Access denied",
                    r"Not enough permissions",
                    r"chmod.*failed",
                    r"Cannot write to",
                ],
                "severity": "medium",
                "auto_fixable": True,
            },
            "disk_space": {
                "patterns": [
                    r"No space left on device",
                    r"Disk full",
                    r"ENOSPC",
                    r"Out of disk space",
                ],
                "severity": "high",
                "auto_fixable": False,
            },
        }

        self.fix_strategies = {
            "dependency": {
                "auto_fix": True,
                "fix_template": "pip install {package}",
                "file_update": "requirements.txt",
                "command_template": 'echo "{package}" >> requirements.txt',
            },
            "missing_file": {
                "auto_fix": True,
                "fix_template": "Create missing file: {file}",
                "file_update": None,
                "command_template": None,
            },
            "network_timeout": {
                "auto_fix": True,
                "fix_template": "Retry with increased timeout",
                "file_update": None,
                "command_template": None,
            },
        }

    def analyze_logs(
        self, log_content: str, job_name: str = None, branch: str = None
    ) -> list[FailureAnalysis]:
        """Analyze log content and return structured failure analysis with history."""
        analyses = []
        seen_signatures = set()  # Avoid duplicate analyses

        for category, config in self.failure_patterns.items():
            for pattern in config["patterns"]:
                matches = re.finditer(
                    pattern, log_content, re.IGNORECASE | re.MULTILINE
                )
                for match in matches:
                    analysis = self._create_analysis(
                        category, config, match, log_content
                    )
                    if analysis and analysis.error_signature not in seen_signatures:
                        seen_signatures.add(analysis.error_signature)

                        # Enrich with historical data
                        if self.use_history and self.db:
                            self._enrich_with_history(analysis)
                            # Record this failure occurrence
                            self.db.record_failure(analysis, job_name, branch)

                        analyses.append(analysis)

        return analyses

    def _generate_error_signature(self, category: str, root_cause: str) -> str:
        """Generate a unique signature for error tracking."""
        # Normalize the root cause to create consistent signatures
        normalized = f"{category}:{root_cause}".lower()
        # Remove variable parts like timestamps, IDs, etc.
        normalized = re.sub(r"\d{4}-\d{2}-\d{2}", "DATE", normalized)
        normalized = re.sub(r"\d+\.\d+\.\d+", "VERSION", normalized)
        normalized = re.sub(r"id:\s*\d+", "id:ID", normalized)

        return hashlib.md5(normalized.encode()).hexdigest()[:16]

    def _enrich_with_history(self, analysis: FailureAnalysis):
        """Enrich analysis with historical data."""
        if not analysis.error_signature:
            return

        stats = self.db.get_failure_stats(analysis.error_signature)
        analysis.frequency = stats["frequency"]
        analysis.success_rate = stats["success_rate"]
        analysis.avg_mttr_minutes = stats["avg_mttr_minutes"]
        analysis.trend = self.db.get_trend(analysis.error_signature, analysis.category)

    def _create_analysis(
        self, category: str, config: dict, match: re.Match, log_content: str
    ) -> FailureAnalysis | None:
        """Create a failure analysis from a pattern match."""
        matched_text = match.group(0)
        captured_groups = match.groups()

        # Extract context around the match
        start = max(0, match.start() - 200)
        end = min(len(log_content), match.end() + 200)
        context = log_content[start:end]

        # Determine root cause and fix
        root_cause, recommended_fix, affected_files, fix_command = self._determine_fix(
            category, matched_text, captured_groups, context
        )

        # Calculate confidence based on pattern specificity and context
        confidence = self._calculate_confidence(match, context, category)

        # Generate error signature for tracking
        error_signature = self._generate_error_signature(category, root_cause)

        return FailureAnalysis(
            category=category,
            severity=config["severity"],
            root_cause=root_cause,
            recommended_fix=recommended_fix,
            affected_files=affected_files,
            confidence=confidence,
            auto_fixable=config.get("auto_fixable", False),
            fix_command=fix_command,
            documentation_links=self._get_documentation_links(category),
            error_signature=error_signature,
        )

    def _determine_fix(
        self, category: str, matched_text: str, captured_groups: tuple, context: str
    ) -> tuple[str, str, list[str], str | None]:
        """Determine the appropriate fix for a failure category."""

        if category == "dependency":
            package = captured_groups[0] if captured_groups else "unknown-package"
            root_cause = f"Missing or incompatible dependency: {package}"
            recommended_fix = f"Install missing dependency: pip install {package}"
            affected_files = [
                "requirements.txt",
                "observability/observability_requirements.txt",
            ]
            fix_command = f'echo "{package}>=1.0.0" >> requirements.txt'

        elif category == "test_assertion":
            root_cause = "Test assertion failed - logic or expectation error"
            recommended_fix = "Review test logic and expected values"
            affected_files = self._extract_test_files(context)
            fix_command = None

        elif category == "network_timeout":
            root_cause = "Network timeout or connection issue"
            recommended_fix = "Retry with exponential backoff or increase timeout"
            affected_files = []
            fix_command = None

        elif category == "missing_file":
            file_path = captured_groups[0] if captured_groups else "unknown-file"
            root_cause = f"Missing required file: {file_path}"
            recommended_fix = f"Create or restore missing file: {file_path}"
            affected_files = [file_path]
            fix_command = f"touch {file_path}" if file_path != "unknown-file" else None

        elif category == "schema_validation":
            root_cause = "Configuration or schema validation error"
            recommended_fix = "Fix YAML/JSON syntax or schema compliance"
            affected_files = self._extract_config_files(context)
            fix_command = None

        elif category == "permission":
            root_cause = "Permission denied or access control issue"
            recommended_fix = "Fix file permissions or access rights"
            affected_files = []
            fix_command = "chmod +x scripts/*.py"

        elif category == "disk_space":
            root_cause = "Insufficient disk space"
            recommended_fix = "Clean up disk space or increase storage"
            affected_files = []
            fix_command = None

        else:
            root_cause = f"Unknown failure category: {category}"
            recommended_fix = "Manual investigation required"
            affected_files = []
            fix_command = None

        return root_cause, recommended_fix, affected_files, fix_command

    def _extract_test_files(self, context: str) -> list[str]:
        """Extract test file paths from context."""
        test_files = []
        test_pattern = r"test_[^/\s]+\.py"
        matches = re.findall(test_pattern, context)
        test_files.extend(matches)
        return test_files

    def _extract_config_files(self, context: str) -> list[str]:
        """Extract configuration file paths from context."""
        config_files = []
        config_patterns = [
            r"[^/\s]+\.yml",
            r"[^/\s]+\.yaml",
            r"[^/\s]+\.json",
            r"requirements\.txt",
            r"config[^/\s]*\.py",
        ]

        for pattern in config_patterns:
            matches = re.findall(pattern, context)
            config_files.extend(matches)

        return config_files

    def _calculate_confidence(
        self, match: re.Match, context: str, category: str
    ) -> float:
        """Calculate confidence score for the analysis."""
        base_confidence = 0.7

        # Increase confidence for specific patterns
        if "ModuleNotFoundError" in match.group(0):
            base_confidence += 0.2
        if "requirements.txt" in context:
            base_confidence += 0.1
        if category in ["dependency", "missing_file"]:
            base_confidence += 0.1

        return min(1.0, base_confidence)

    def _get_documentation_links(self, category: str) -> list[str]:
        """Get relevant documentation links for failure category."""
        links = {
            "dependency": [
                "https://pip.pypa.io/en/stable/user_guide/",
                "https://docs.python.org/3/tutorial/modules.html",
            ],
            "test_assertion": [
                "https://docs.pytest.org/en/stable/",
                "https://docs.python.org/3/library/unittest.html",
            ],
            "network_timeout": [
                "https://requests.readthedocs.io/en/latest/user/quickstart/",
                "https://docs.github.com/en/actions/learn-github-actions/understanding-github-actions",
            ],
            "missing_file": [
                "https://docs.github.com/en/actions/learn-github-actions/understanding-github-actions"
            ],
        }

        return links.get(category, [])

    def generate_markdown_report(self, analyses: list[FailureAnalysis]) -> str:
        """Generate a markdown report from failure analyses."""
        if not analyses:
            return (
                "## 🎉 No Critical Failures Detected\n\nAll checks passed successfully!"
            )

        # Group by category
        categories = {}
        for analysis in analyses:
            if analysis.category not in categories:
                categories[analysis.category] = []
            categories[analysis.category].append(analysis)

        report = ["## 🔍 CI/CD Failure Analysis Report\n"]
        report.append(f"**Analysis Time:** {datetime.now().isoformat()}\n")

        # Summary
        total_failures = len(analyses)
        auto_fixable = sum(1 for a in analyses if a.auto_fixable)

        report.append("### 📊 Summary\n")
        report.append(f"- **Total Failures:** {total_failures}")
        report.append(f"- **Auto-Fixable:** {auto_fixable}")
        report.append(f"- **Categories:** {', '.join(categories.keys())}\n")

        # Detailed analysis by category
        for category, category_analyses in categories.items():
            emoji = self._get_category_emoji(category)
            report.append(f"### {emoji} {category.title()} Issues\n")

            for i, analysis in enumerate(category_analyses, 1):
                trend_emoji = self._get_trend_emoji(analysis.trend)
                report.append(f"#### {i}. {analysis.root_cause} {trend_emoji}\n")
                report.append(f"**Severity:** {analysis.severity.upper()}")
                report.append(f"**Confidence:** {analysis.confidence:.1%}")
                report.append(
                    f"**Auto-Fixable:** {'✅ Yes' if analysis.auto_fixable else '❌ No'}"
                )

                # Add historical data if available
                if analysis.frequency > 0:
                    report.append(
                        f"**Frequency (30d):** {analysis.frequency} occurrences"
                    )
                if analysis.success_rate > 0:
                    report.append(
                        f"**Historical Fix Success Rate:** {analysis.success_rate:.1%}"
                    )
                if analysis.avg_mttr_minutes > 0:
                    report.append(
                        f"**Avg MTTR:** {analysis.avg_mttr_minutes:.1f} minutes"
                    )
                report.append("")

                report.append("**Recommended Fix:**")
                report.append(f"```bash\n{analysis.recommended_fix}\n```\n")

                if analysis.affected_files:
                    report.append("**Affected Files:**")
                    for file in analysis.affected_files:
                        report.append(f"- `{file}`")
                    report.append("")

                if analysis.fix_command:
                    report.append("**Auto-Fix Command:**")
                    report.append(f"```bash\n{analysis.fix_command}\n```\n")

                if analysis.documentation_links:
                    report.append("**Documentation:**")
                    for link in analysis.documentation_links:
                        report.append(f"- {link}")
                    report.append("")

        # Next Steps
        report.append("### 🚀 Next Steps\n")
        if auto_fixable > 0:
            report.append(
                "1. **Auto-Fix Available:** Consider running the auto-fix job"
            )
            report.append("2. **Review Changes:** Validate auto-fixes before merging")

        report.append("3. **Manual Fixes:** Address non-auto-fixable issues")
        report.append("4. **Retry CI:** Push changes to trigger new CI run")
        report.append("5. **Monitor:** Watch for similar failures in future runs\n")

        return "\n".join(report)

    def _get_category_emoji(self, category: str) -> str:
        """Get emoji for failure category."""
        emojis = {
            "dependency": "🐍",
            "test_assertion": "🔥",
            "network_timeout": "🌐",
            "missing_file": "📦",
            "schema_validation": "🛠️",
            "permission": "🔒",
            "disk_space": "💾",
        }
        return emojis.get(category, "❓")

    def _get_trend_emoji(self, trend: str) -> str:
        """Get emoji for trend indicator."""
        emojis = {"rising": "🔥", "improving": "📉", "stable": "📊"}
        return emojis.get(trend, "")

    def close(self):
        """Close database connection."""
        if self.db:
            self.db.close()


def get_job_logs_from_github(workflow_run_id: str, job_name: str = None) -> str:
    """Get job logs from GitHub Actions API."""
    try:
        # Use GitHub CLI if available
        cmd = ["gh", "run", "view", workflow_run_id, "--log"]
        if job_name:
            cmd.extend(["--job", job_name])

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback: try to read from local file
        log_file = Path(f"ci-logs-{workflow_run_id}.txt")
        if log_file.exists():
            return log_file.read_text()
        return ""


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Analyze CI/CD failures intelligently")
    parser.add_argument(
        "--ci", action="store_true", help="Run in CI mode (non-interactive)"
    )
    parser.add_argument(
        "--analyze-latest", action="store_true", help="Analyze the latest CI run"
    )
    parser.add_argument("--job-logs", help="Path to job log file")
    parser.add_argument("--workflow-run-id", help="GitHub workflow run ID")
    parser.add_argument("--job-name", help="Specific job name to analyze")
    parser.add_argument("--branch", help="Branch name for tracking")
    parser.add_argument("--json-output", help="Output results in JSON format")
    parser.add_argument("--markdown-output", help="Output markdown report to file")
    parser.add_argument(
        "--no-history", action="store_true", help="Disable historical tracking"
    )
    parser.add_argument(
        "--db-path", default="ci_failure_history.db", help="Path to history database"
    )

    args = parser.parse_args()

    # Get branch name if not provided
    branch = args.branch
    if not branch:
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True,
            )
            branch = result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            branch = "unknown"

    # Get log content
    log_content = ""

    if args.job_logs:
        log_file = Path(args.job_logs)
        if log_file.exists():
            log_content = log_file.read_text()
        else:
            print(f"❌ Log file not found: {log_file}")
            sys.exit(1)
    elif args.workflow_run_id:
        log_content = get_job_logs_from_github(args.workflow_run_id, args.job_name)
    elif args.analyze_latest:
        # Get latest workflow run ID (requires GitHub CLI)
        try:
            result = subprocess.run(
                ["gh", "run", "list", "--limit", "1", "--json", "databaseId"],
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(result.stdout)
            if data:
                latest_run_id = str(data[0]["databaseId"])
                log_content = get_job_logs_from_github(latest_run_id)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ GitHub CLI not available for latest run analysis")
            sys.exit(1)
    else:
        # Read from stdin or default log file
        if not sys.stdin.isatty():
            log_content = sys.stdin.read()
        else:
            print(
                "❌ No log input provided. Use --job-logs, --workflow-run-id, or pipe logs via stdin"
            )
            sys.exit(1)

    if not log_content:
        print("❌ No log content to analyze")
        sys.exit(1)

    # Analyze logs with historical tracking
    use_history = not args.no_history
    analyzer = CIFailureAnalyzer(use_history=use_history, db_path=args.db_path)

    try:
        analyses = analyzer.analyze_logs(
            log_content, job_name=args.job_name, branch=branch
        )

        # Generate outputs
        if args.json_output:
            result = {
                "timestamp": datetime.now().isoformat(),
                "job_name": args.job_name,
                "branch": branch,
                "total_failures": len(analyses),
                "auto_fixable_count": sum(1 for a in analyses if a.auto_fixable),
                "categories": list({a.category for a in analyses}),
                "analyses": [asdict(a) for a in analyses],
            }

            with open(args.json_output, "w") as f:
                json.dump(result, f, indent=2)

            print(f"✅ Analysis results written to {args.json_output}")

        # Generate markdown report
        markdown_report = analyzer.generate_markdown_report(analyses)

        if args.markdown_output:
            with open(args.markdown_output, "w") as f:
                f.write(markdown_report)
            print(f"✅ Markdown report written to {args.markdown_output}")

        # Print summary
        if not args.ci:
            print("\n" + "=" * 60)
            print("📊 FAILURE ANALYSIS SUMMARY")
            print("=" * 60)
            print(markdown_report)

        # Exit with appropriate code
        exit_code = 0
        if analyses:
            critical_failures = [a for a in analyses if a.severity == "high"]
            if critical_failures:
                exit_code = 1  # Critical failures

        return exit_code

    finally:
        # Clean up database connection
        analyzer.close()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
