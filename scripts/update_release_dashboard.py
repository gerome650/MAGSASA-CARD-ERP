#!/usr/bin/env python3
"""
🚀 Release Readiness Dashboard Updater CLI (Production-Grade)

Automatically updates v0.7.0-release-checklist.md with the latest GitHub Actions
and CI/CD data from the repository.

Features:
- Modular architecture (fetch, update, notify, scoring)
- Rich terminal output with colors and formatting
- JSON caching for analytics and trending
- Slack notifications with detailed failure info
- CI gating with --check-only flag
- Dry-run mode for preview

Usage:
    python scripts/update_release_dashboard.py [options]

Options:
    --commit              Automatically commit the updated file
    --branch <branch>     Specify the branch (default: main)
    --token <GH_TOKEN>    GitHub access token (fallback to GH_TOKEN env variable)
    --notify              Send Slack notification when readiness < 90%
    --verbose             Enable verbose output
    --dry-run             Show what would be updated without making changes
    --check-only          Exit 1 if readiness < 90% (for CI gating)
    --no-cache            Skip caching results to JSON

Examples:
    # Preview changes
    python scripts/update_release_dashboard.py --dry-run

    # Commit updates and send notifications
    python scripts/update_release_dashboard.py --commit --notify --verbose

    # Enforce readiness gate (CI will fail if <90%)
    python scripts/update_release_dashboard.py --check-only
"""

import argparse
import subprocess
import sys
from typing import Any

# Rich library for beautiful terminal output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  Warning: rich library not found. Install with: pip install rich")
    print("    Falling back to basic output.\n")

# Import modular components
try:
    from release_dashboard import (
        GitHubWorkflowFetcher,
        MarkdownUpdater,
        ReadinessScorer,
        SlackNotifier,
    )
    from release_dashboard.cache import ReadinessCache
    from release_dashboard.pr_commenter import PRCommenter
except ImportError:
    print("❌ Error: Could not import release_dashboard modules.")
    print("   Make sure you're running from the repository root.")
    sys.exit(1)


class ReleaseDashboardUpdater:
    """Main orchestrator for the release dashboard update process."""

    def __init__(
        self,
        token: str | None = None,
        repo_name: str | None = None,
        checklist_path: str = "v0.7.0-release-checklist.md",
        verbose: bool = False,
        use_cache: bool = True,
    ):
        """
        Initialize the dashboard updater.

        Args:
            token: GitHub access token
            repo_name: Full repository name (owner/repo)
            checklist_path: Path to release checklist file
            verbose: Enable verbose logging
            use_cache: Enable JSON caching
        """
        self.verbose = verbose
        self.use_cache = use_cache
        self.console = Console() if RICH_AVAILABLE else None

        # Initialize modular components
        try:
            self.fetcher = GitHubWorkflowFetcher(
                token=token, repo_full_name=repo_name, verbose=verbose
            )
            self.updater = MarkdownUpdater(
                checklist_path=checklist_path, verbose=verbose
            )
            self.notifier = SlackNotifier(verbose=verbose)
            self.scorer = ReadinessScorer(
                checklist_path=checklist_path, verbose=verbose
            )

            if self.use_cache:
                self.cache = ReadinessCache(verbose=verbose)
            else:
                self.cache = None

        except Exception as e:
            self._print_error(f"Initialization failed: {e}")
            raise

    def _print_status(self, message: str, style: str = "info"):
        """Print status message with rich formatting if available."""
        if RICH_AVAILABLE and self.console:
            if style == "success":
                self.console.print(f"✅ {message}", style="bold green")
            elif style == "error":
                self.console.print(f"❌ {message}", style="bold red")
            elif style == "warning":
                self.console.print(f"⚠️  {message}", style="bold yellow")
            elif style == "info":
                self.console.print(f"ℹ️  {message}", style="bold blue")
            else:
                self.console.print(message)
        else:
            prefix = {"success": "✅", "error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(
                style, "•"
            )
            print(f"{prefix} {message}")

    def _print_error(self, message: str):
        """Print error message."""
        self._print_status(message, "error")

    def _print_success(self, message: str):
        """Print success message."""
        self._print_status(message, "success")

    def _print_warning(self, message: str):
        """Print warning message."""
        self._print_status(message, "warning")

    def _display_score_summary(self, score_data: dict[str, Any]):
        """Display score summary in a beautiful table."""
        if RICH_AVAILABLE and self.console:
            # Create score summary table
            table = Table(
                title="📊 Release Readiness Score",
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("Category", style="cyan", width=30)
            table.add_column("Score", justify="right", style="green", width=12)
            table.add_column("Passing", justify="center", width=15)
            table.add_column("Weight", justify="right", width=10)

            table.add_row(
                "Core Gates",
                f"{score_data['core_score']}%",
                f"{score_data['core_passing']}/{score_data['core_total']}",
                "50%",
            )
            table.add_row(
                "Optional Gates",
                f"{score_data['optional_score']}%",
                f"{score_data['optional_passing']}/{score_data['optional_total']}",
                "20%",
            )
            table.add_row(
                "Deployment",
                f"{score_data['deployment_score']}%",
                f"{score_data['deployment_passing']}/{score_data['deployment_total']}",
                "20%",
            )
            table.add_row(
                "Sign-off",
                f"{score_data['signoff_score']}%",
                f"{score_data['signoff_passing']}/{score_data['signoff_total']}",
                "10%",
            )
            table.add_row(
                "[bold]TOTAL[/bold]",
                f"[bold]{score_data['total_score']}%[/bold]",
                "",
                "[bold]100%[/bold]",
                style="bold",
            )

            self.console.print(table)

            # Display status panel
            status_color = (
                "green"
                if score_data["total_score"] >= 90
                else "yellow" if score_data["total_score"] >= 80 else "red"
            )
            panel = Panel(
                f"[{status_color}]{score_data['status_emoji']} {score_data['status_text']}[/{status_color}]",
                title="Status",
                border_style=status_color,
            )
            self.console.print(panel)

            # Display blockers if any
            if score_data.get("blockers"):
                self.console.print("\n[bold red]🚧 Current Blockers:[/bold red]")
                for blocker in score_data["blockers"]:
                    self.console.print(f"  • {blocker}")
        else:
            # Fallback to simple text output
            print(f"\n{'='*60}")
            print(
                f"  📊 RELEASE READINESS SCORE: {score_data['total_score']}% {score_data['status_emoji']}"
            )
            print(f"{'='*60}")
            print(f"  Status: {score_data['status_text']}")
            print(
                f"\n  Core Gates:       {score_data['core_score']}% ({score_data['core_passing']}/{score_data['core_total']})"
            )
            print(
                f"  Optional Gates:   {score_data['optional_score']}% ({score_data['optional_passing']}/{score_data['optional_total']})"
            )
            print(
                f"  Deployment:       {score_data['deployment_score']}% ({score_data['deployment_passing']}/{score_data['deployment_total']})"
            )
            print(
                f"  Sign-off:         {score_data['signoff_score']}% ({score_data['signoff_passing']}/{score_data['signoff_total']})"
            )
            print(f"{'='*60}\n")

    def run(
        self,
        commit: bool = False,
        branch: str = "main",
        notify: bool = False,
        dry_run: bool = False,
        check_only: bool = False,
        pr_comment: bool = False,
        strict: bool = False,
    ) -> tuple[bool, float]:
        """
        Main execution method.

        Args:
            commit: Commit changes to git
            branch: Target branch
            notify: Send Slack notification
            dry_run: Preview only, no changes
            check_only: Only check score, exit 1 if < 90%
            pr_comment: Post/update PR comment with readiness info
            strict: Fail if PR comment or Slack notification fails

        Returns:
            Tuple of (success, readiness_score)
        """
        try:
            if RICH_AVAILABLE and self.console:
                self.console.rule("[bold blue]🚀 Release Dashboard Updater[/bold blue]")
            else:
                print("\n" + "=" * 60)
                print("  🚀 RELEASE DASHBOARD UPDATER")
                print("=" * 60 + "\n")

            # Step 1: Fetch workflow runs
            self._print_status("Fetching GitHub Actions workflow runs...")
            runs = self.fetcher.get_workflow_runs(
                limit=10, branch=branch if branch != "main" else None
            )
            self._print_success(f"Retrieved {len(runs)} workflow runs")

            # Step 2: Get CI health summary
            self._print_status("Analyzing CI health...")
            ci_health = self.fetcher.get_workflow_health_summary()
            self._print_success(
                f"CI Health: {ci_health['status'].upper()} (Success rate: {ci_health['success_rate']}%)"
            )

            # Step 3: Calculate readiness score
            self._print_status("Calculating release readiness score...")
            score_data = self.scorer.calculate_score(ci_health=ci_health)
            self._print_success(f"Readiness score: {score_data['total_score']}%")

            # Display score summary
            print()  # Blank line for spacing
            self._display_score_summary(score_data)
            print()  # Blank line for spacing

            # Handle check-only mode
            if check_only:
                threshold = 90.0
                if score_data["total_score"] < threshold:
                    self._print_error(
                        f"Readiness check FAILED: {score_data['total_score']}% < {threshold}%"
                    )
                    return False, score_data["total_score"]
                else:
                    self._print_success(
                        f"Readiness check PASSED: {score_data['total_score']}% >= {threshold}%"
                    )
                    return True, score_data["total_score"]

            # Step 4: Generate updated markdown sections
            self._print_status("Generating markdown updates...")
            ci_snapshot = self.updater.generate_ci_snapshot(runs, ci_health)
            readiness_score_section = self.updater.generate_readiness_score_section(
                score_data
            )

            if dry_run:
                self._print_warning("DRY RUN MODE - No changes will be made")
                print("\n" + "=" * 60)
                print("PREVIEW: CI SNAPSHOT")
                print("=" * 60)
                print(
                    ci_snapshot[:500] + "..." if len(ci_snapshot) > 500 else ci_snapshot
                )
                print("\n" + "=" * 60)
                print("PREVIEW: READINESS SCORE")
                print("=" * 60)
                print(readiness_score_section)
                print("=" * 60 + "\n")
                return True, score_data["total_score"]

            # Step 5: Update the markdown file
            self._print_status("Updating checklist file...")
            self.updater.read()
            self.updater.update_sections(ci_snapshot, readiness_score_section)

            if self.updater.has_changes():
                self.updater.write()
                self._print_success("Checklist file updated successfully")
            else:
                self._print_status("No changes detected, file is up to date", "info")

            # Step 6: Cache results
            if self.use_cache and self.cache:
                self._print_status("Caching results for analytics...")
                self.cache.append_entry(score_data)
                self._print_success("Results cached")

            # Step 7: Send notification if requested
            if notify:
                self._print_status("Sending Slack notification...")
                success = self.notifier.send_readiness_alert(
                    score=score_data["total_score"],
                    score_data=score_data,
                    failing_workflows=ci_health.get("failing_workflows"),
                    blockers=score_data.get("blockers"),
                )
                if success:
                    self._print_success("Slack notification sent")
                else:
                    error_msg = "Failed to send Slack notification (webhook may not be configured)"
                    if strict:
                        self._print_error(error_msg)
                        return False, score_data["total_score"]
                    else:
                        self._print_warning(error_msg)

            # Step 7.5: Post PR comment if requested
            if pr_comment and not dry_run:
                self._print_status("Posting PR comment with readiness info...")
                try:
                    commenter = PRCommenter(
                        token=self.fetcher.token, verbose=self.verbose
                    )
                    success = commenter.post_readiness_comment(
                        score_data=score_data,
                        failing_workflows=ci_health.get("failing_workflows", []),
                        dashboard_branch=branch,
                        strict=strict,
                    )
                    if success:
                        self._print_success("PR comment posted successfully")
                    else:
                        error_msg = "Failed to post PR comment"
                        if strict:
                            self._print_error(error_msg)
                            return False, score_data["total_score"]
                        else:
                            self._print_warning(error_msg)
                except Exception as e:
                    error_msg = f"Failed to post PR comment: {e}"
                    if strict:
                        self._print_error(error_msg)
                        return False, score_data["total_score"]
                    else:
                        self._print_warning(error_msg)
            elif pr_comment and dry_run:
                self._print_warning(
                    "DRY RUN: Would post PR comment with readiness info"
                )

            # Step 8: Commit changes if requested
            if commit and self.updater.has_changes():
                self._print_status("Committing changes to git...")
                success = self._commit_changes(branch)
                if success:
                    self._print_success(f"Changes committed and pushed to {branch}")
                else:
                    self._print_warning("Git commit/push failed")

            if RICH_AVAILABLE and self.console:
                self.console.rule("[bold green]✅ Update Complete[/bold green]")
            else:
                print("\n" + "=" * 60)
                print("  ✅ UPDATE COMPLETE")
                print("=" * 60 + "\n")

            return True, score_data["total_score"]

        except Exception as e:
            self._print_error(f"Update failed: {e}")
            if self.verbose:
                import traceback

                traceback.print_exc()
            return False, 0.0

    def _commit_changes(self, branch: str) -> bool:
        """Commit and push changes to git."""
        try:
            # Check if there are changes
            result = subprocess.run(
                ["git", "diff", "--quiet", self.updater.checklist_path],
                capture_output=True,
            )

            if result.returncode == 0:
                # No changes
                return True

            # Add file
            subprocess.run(["git", "add", str(self.updater.checklist_path)], check=True)

            # Commit
            commit_message = "chore(dashboard): automated readiness update"
            subprocess.run(["git", "commit", "-m", commit_message], check=True)

            # Push
            subprocess.run(["git", "push", "origin", branch], check=True)

            return True

        except subprocess.CalledProcessError as e:
            if self.verbose:
                print(f"Git operation failed: {e}")
            return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="🚀 Update release readiness dashboard with latest CI/CD data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview changes
  python scripts/update_release_dashboard.py --dry-run

  # Commit updates and send notifications
  python scripts/update_release_dashboard.py --commit --notify --verbose

  # Enforce readiness gate (CI will fail if <90%)
  python scripts/update_release_dashboard.py --check-only

  # Full automation mode
  python scripts/update_release_dashboard.py --commit --notify --branch main

  # Post PR comment with readiness info
  python scripts/update_release_dashboard.py --pr-comment

  # Full automation with PR comments and strict mode
  python scripts/update_release_dashboard.py --commit --notify --pr-comment --strict
        """,
    )

    parser.add_argument(
        "--commit", action="store_true", help="Automatically commit the updated file"
    )
    parser.add_argument(
        "--branch", default="main", help="Specify the branch (default: main)"
    )
    parser.add_argument(
        "--token", help="GitHub access token (fallback to GH_TOKEN env variable)"
    )
    parser.add_argument(
        "--repo",
        help="Full repository name (owner/repo, auto-detected if not specified)",
    )
    parser.add_argument(
        "--notify",
        action="store_true",
        help="Send Slack notification when readiness < 90%%",
    )
    parser.add_argument(
        "--pr-comment",
        action="store_true",
        help="Post or update PR comment with readiness summary",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if PR comment or Slack notification fails",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Exit 1 if readiness < 90%% (for CI gating)",
    )
    parser.add_argument(
        "--no-cache", action="store_true", help="Skip caching results to JSON"
    )

    args = parser.parse_args()

    try:
        # Banner
        if not args.check_only:
            if RICH_AVAILABLE:
                console = Console()
                console.print(
                    "\n[bold cyan]🚀 Release Dashboard Updater v1.0.0[/bold cyan]"
                )
                console.print(
                    "[dim]Production-grade automation for release readiness tracking[/dim]\n"
                )
            else:
                print("\n🚀 Release Dashboard Updater v1.0.0")
                print("   Production-grade automation for release readiness tracking\n")

        # Initialize updater
        updater = ReleaseDashboardUpdater(
            token=args.token,
            repo_name=args.repo,
            verbose=args.verbose,
            use_cache=not args.no_cache,
        )

        # Run update
        success, score = updater.run(
            commit=args.commit,
            branch=args.branch,
            notify=args.notify,
            dry_run=args.dry_run,
            check_only=args.check_only,
            pr_comment=args.pr_comment,
            strict=args.strict,
        )

        # Exit with appropriate code
        if not success:
            sys.exit(1)

        # Check-only mode: exit 1 if score < 90%
        if args.check_only and score < 90.0:
            sys.exit(1)

        sys.exit(0)

    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}\n")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user\n")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}\n")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
