"""
GitHub Workflow Fetcher Module

Handles fetching workflow runs and CI data from GitHub Actions API.
"""

import os
from typing import Any

try:
    from github import Auth, Github
    from github.GithubException import GithubException
except ImportError as e:
    raise ImportError(
        "PyGithub library not found. Install with: pip install PyGithub"
    ) from e


class GitHubWorkflowFetcher:
    """Fetches workflow runs and CI data from GitHub Actions."""

    # Workflow name display mappings
    WORKFLOW_DISPLAY_NAMES = {
        "ci.yml": "Build & Test",
        "pr.yml": "PR Validation",
        "auto_release.yml": "Auto Release",
        "chaos-engineering.yml": "Chaos Engineering",
        "chaos-validation-self-healing.yml": "Chaos Self-Healing",
        "observability.yml": "Observability",
        "mcp-validation.yml": "MCP Validation",
        "stage-readiness-check.yml": "Stage Readiness",
        "docs-gate.yml": "Documentation",
        "notion-weekly-sync.yml": "Notion Sync",
        "notion-roadmap-sync.yml": "Roadmap Sync",
        "ci-intelligence-report.yml": "CI Intelligence",
        "kind-chaos-smoketest.yml": "Chaos Smoketest",
        "resilience-gate.yml": "Resilience Gate",
        "resilience-gate-main.yml": "Main Resilience Gate",
        "release.yml": "Release Pipeline",
        "update-readiness.yml": "Dashboard Updater",
    }

    def __init__(
        self,
        token: str | None = None,
        repo_full_name: str | None = None,
        verbose: bool = False,
    ):
        """
        Initialize the GitHub workflow fetcher.

        Args:
            token: GitHub personal access token (defaults to GH_TOKEN env var)
            repo_full_name: Full repository name (owner/repo)
            verbose: Enable verbose logging
        """
        self.token = token or os.getenv("GH_TOKEN")
        self.verbose = verbose

        if not self.token:
            raise ValueError(
                "GitHub token required. Set GH_TOKEN env var or pass token parameter"
            )

        # Initialize GitHub client
        try:
            self.github = Github(auth=Auth.Token(self.token))
        except Exception as e:
            raise ValueError(f"Failed to initialize GitHub client: {e}") from e

        # Get repository
        if not repo_full_name:
            repo_full_name = self._detect_repo_from_git()

        try:
            self.repo = self.github.get_repo(repo_full_name)
            if self.verbose:
                print(f"✓ Connected to repository: {repo_full_name}")
        except GithubException as e:
            if e.status == 401:
                raise ValueError(
                    "Invalid GitHub token. Please check your credentials."
                ) from e
            elif e.status == 404:
                raise ValueError(
                    f"Repository '{repo_full_name}' not found or no access."
                ) from e
            else:
                raise ValueError(f"Failed to access repository: {e}") from e

    def _detect_repo_from_git(self) -> str:
        """Detect repository name from git remote."""
        import subprocess

        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=True,
            )
            url = result.stdout.strip()

            # Parse GitHub URL (handles both HTTPS and SSH)
            if "github.com" in url:
                # Extract owner/repo from URL
                parts = url.split("github.com")[-1].strip("/:").replace(".git", "")
                return parts
            else:
                raise ValueError("Could not detect GitHub repository from git remote")
        except subprocess.CalledProcessError as e:
            raise ValueError(
                "Failed to detect repository. Not in a git repository or no remote configured."
            ) from e

    def get_workflow_runs(
        self, limit: int = 10, branch: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Fetch recent workflow runs from GitHub Actions.

        Args:
            limit: Maximum number of runs to fetch
            branch: Filter by branch (None for all branches)

        Returns:
            List of workflow run data dictionaries
        """
        try:
            workflows = list(self.repo.get_workflows())
            if self.verbose:
                print(f"✓ Found {len(workflows)} workflows")

            all_runs = []
            for workflow in workflows:
                try:
                    # Get runs with optional branch filter
                    if branch:
                        runs = list(workflow.get_runs()[:5])  # Get last 5 per workflow
                        runs = [r for r in runs if r.head_branch == branch]
                    else:
                        runs = list(workflow.get_runs()[:5])

                    for run in runs:
                        duration_seconds = None
                        if run.created_at and run.updated_at:
                            duration = run.updated_at - run.created_at
                            duration_seconds = int(duration.total_seconds())

                        all_runs.append(
                            {
                                "id": run.id,
                                "workflow_name": workflow.name,
                                "workflow_file": (
                                    workflow.path.split("/")[-1]
                                    if workflow.path
                                    else workflow.name
                                ),
                                "display_name": self.WORKFLOW_DISPLAY_NAMES.get(
                                    (
                                        workflow.path.split("/")[-1]
                                        if workflow.path
                                        else workflow.name
                                    ),
                                    workflow.name,
                                ),
                                "status": run.status,
                                "conclusion": run.conclusion,
                                "created_at": run.created_at,
                                "updated_at": run.updated_at,
                                "duration_seconds": duration_seconds,
                                "head_branch": run.head_branch,
                                "head_sha": run.head_sha[:7] if run.head_sha else "N/A",
                                "commit_message": (
                                    run.head_commit.message
                                    if run.head_commit
                                    else "N/A"
                                ),
                                "html_url": run.html_url,
                                "run_number": run.run_number,
                                "event": run.event,
                                "actor": run.actor.login if run.actor else "N/A",
                            }
                        )
                except Exception as e:
                    if self.verbose:
                        print(
                            f"⚠ Warning: Could not fetch runs for workflow {workflow.name}: {e}"
                        )
                    continue

            # Sort by creation time (newest first) and limit
            all_runs.sort(key=lambda x: x["created_at"], reverse=True)
            return all_runs[:limit]

        except Exception as e:
            if self.verbose:
                print(f"✗ Error fetching workflow runs: {e}")
            return []

    def get_workflow_health_summary(self) -> dict[str, Any]:
        """
        Get overall workflow health summary.

        Returns:
            Dictionary with health metrics
        """
        runs = self.get_workflow_runs(limit=50)  # Get more for better stats

        if not runs:
            return {
                "total_runs": 0,
                "success_rate": 0.0,
                "failure_count": 0,
                "status": "unknown",
                "failing_workflows": [],
            }

        total = len(runs)
        successes = sum(1 for r in runs if r["conclusion"] == "success")
        failures = sum(1 for r in runs if r["conclusion"] == "failure")

        success_rate = (successes / total) * 100 if total > 0 else 0

        # Find consistently failing workflows
        workflow_failures = {}
        for run in runs:
            if run["conclusion"] == "failure":
                wf_name = run["display_name"]
                if wf_name not in workflow_failures:
                    workflow_failures[wf_name] = {
                        "name": wf_name,
                        "count": 0,
                        "last_failure": run["created_at"],
                        "url": run["html_url"],
                    }
                workflow_failures[wf_name]["count"] += 1

        # Sort by failure count
        failing_workflows = sorted(
            workflow_failures.values(), key=lambda x: x["count"], reverse=True
        )[
            :3
        ]  # Top 3 failing workflows

        # Determine overall status
        if success_rate >= 95:
            status = "healthy"
        elif success_rate >= 85:
            status = "warning"
        else:
            status = "critical"

        return {
            "total_runs": total,
            "success_count": successes,
            "failure_count": failures,
            "success_rate": round(success_rate, 1),
            "status": status,
            "failing_workflows": failing_workflows,
        }

    def format_duration(self, seconds: int | None) -> str:
        """Format duration in human-readable format."""
        if seconds is None:
            return "N/A"

        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"

    @staticmethod
    def get_status_emoji(conclusion: str | None, status: str) -> str:
        """Get emoji for workflow status."""
        if conclusion == "success":
            return "✅"
        elif conclusion == "failure":
            return "❌"
        elif conclusion == "cancelled":
            return "🚫"
        elif conclusion == "skipped":
            return "⏭️"
        elif status == "in_progress":
            return "🟡"
        elif status == "queued":
            return "⏳"
        else:
            return "⚪"
