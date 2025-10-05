"""
PR Auto-Commenter Module for Release Dashboard

Automatically posts and updates PR comments with release readiness information,
including current score, failing workflows, and shields.io badge.
"""

import os
import re
from datetime import datetime
from typing import Any
from urllib.parse import quote

try:
    from github import Auth, Github
    from github.GithubException import GithubException
except ImportError:
    raise ImportError("PyGithub library not found. Install with: pip install PyGithub")


class PRCommenter:
    """Handles PR comment posting and updating for release readiness."""

    # HTML marker for idempotent comment updates
    COMMENT_MARKER = "<!-- RELEASE_DASHBOARD_COMMENT_MARKER: DO_NOT_DELETE -->"

    def __init__(
        self,
        token: str | None = None,
        owner: str | None = None,
        repo: str | None = None,
        pr_number: int | None = None,
        verbose: bool = False,
    ):
        """
        Initialize the PR commenter.

        Args:
            token: GitHub access token (defaults to GH_TOKEN env var)
            owner: Repository owner (auto-detected if not provided)
            repo: Repository name (auto-detected if not provided)
            pr_number: PR number (auto-detected from GitHub context if not provided)
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
            raise ValueError(f"Failed to initialize GitHub client: {e}")

        # Auto-detect repository and PR info if not provided
        if not owner or not repo:
            owner, repo = self._detect_repo_info()

        if not pr_number:
            pr_number = self._detect_pr_number()

        self.owner = owner
        self.repo_name = repo
        self.pr_number = pr_number

        # Get repository and PR objects
        try:
            self.repository = self.github.get_repo(f"{owner}/{repo}")
            self.pr = self.repository.get_pull(pr_number)
            if self.verbose:
                print(f"✓ Connected to PR #{pr_number} in {owner}/{repo}")
        except GithubException as e:
            if e.status == 401:
                raise ValueError("Invalid GitHub token. Please check your credentials.")
            elif e.status == 404:
                raise ValueError(
                    f"Repository '{owner}/{repo}' or PR #{pr_number} not found or no access."
                )
            else:
                raise ValueError(f"Failed to access PR: {e}")

    def _detect_repo_info(self) -> tuple[str, str]:
        """Detect repository owner and name from git remote or GitHub context."""
        # Try GitHub Actions context first
        github_repo = os.getenv("GITHUB_REPOSITORY")
        if github_repo:
            owner, repo = github_repo.split("/", 1)
            return owner, repo

        # Fallback to git remote
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
                parts = url.split("github.com")[-1].strip("/:").replace(".git", "")
                owner, repo = parts.split("/", 1)
                return owner, repo
            else:
                raise ValueError("Could not detect GitHub repository from git remote")
        except subprocess.CalledProcessError:
            raise ValueError(
                "Failed to detect repository. Not in a git repository or no remote configured."
            )

    def _detect_pr_number(self) -> int | None:
        """Detect PR number from GitHub Actions context or git branch."""
        # Try GitHub Actions context first
        github_ref = os.getenv("GITHUB_REF")
        if github_ref:
            # Format: refs/pull/123/merge
            match = re.match(r"refs/pull/(\d+)/merge", github_ref)
            if match:
                return int(match.group(1))

        # Try from pull request event payload
        github_event_path = os.getenv("GITHUB_EVENT_PATH")
        if github_event_path:
            try:
                import json

                with open(github_event_path) as f:
                    event_data = json.load(f)
                    if "pull_request" in event_data:
                        return event_data["pull_request"]["number"]
            except Exception:
                pass

        return None

    def get_status_emoji_and_text(self, score: float) -> tuple[str, str, str]:
        """
        Get status emoji, text, and color based on readiness score.

        Args:
            score: Readiness score (0-100)

        Returns:
            Tuple of (emoji, text, color)
        """
        if score >= 95:
            return "🟢", "Ready", "green"
        elif score >= 90:
            return "🟡", "Nearly Ready", "yellow"
        elif score >= 80:
            return "🟠", "Risky", "orange"
        else:
            return "🔴", "Blocked", "red"

    def generate_badge_url(self, score: float) -> str:
        """
        Generate shields.io badge URL for readiness score.

        Args:
            score: Readiness score (0-100)

        Returns:
            Shields.io badge URL
        """
        _, _, color = self.get_status_emoji_and_text(score)
        score_text = f"{score:.1f}%"
        encoded_score = quote(score_text)
        encoded_color = quote(color)

        return f"https://img.shields.io/badge/Readiness-{encoded_score}-{encoded_color}.svg?style=for-the-badge"

    def format_failing_workflows(
        self, failing_workflows: list[dict[str, Any]], max_items: int = 3
    ) -> str:
        """
        Format failing workflows list for markdown.

        Args:
            failing_workflows: List of failing workflow data
            max_items: Maximum number of workflows to show

        Returns:
            Formatted markdown string
        """
        if not failing_workflows:
            return "• ✅ No failing workflows detected"

        items = []
        for i, workflow in enumerate(failing_workflows[:max_items]):
            name = workflow.get("name", "Unknown Workflow")
            count = workflow.get("count", 0)
            url = workflow.get("url", "#")
            items.append(f"• ❌ **{name}** — {count} recent failures ([logs]({url}))")

        # Add "more" indicator if there are additional failures
        if len(failing_workflows) > max_items:
            remaining = len(failing_workflows) - max_items
            items.append(f"• +{remaining} more failing workflows...")

        return "\n".join(items)

    def generate_comment_body(
        self,
        score_data: dict[str, Any],
        failing_workflows: list[dict[str, Any]],
        dashboard_branch: str = "main",
    ) -> str:
        """
        Generate the complete PR comment body.

        Args:
            score_data: Readiness scoring data
            failing_workflows: List of failing workflows
            dashboard_branch: Branch containing the dashboard file

        Returns:
            Complete markdown comment body
        """
        score = score_data.get("total_score", 0)
        emoji, status_text, color = self.get_status_emoji_and_text(score)

        # Generate badge URL
        badge_url = self.generate_badge_url(score)

        # Format failing workflows
        workflows_markdown = self.format_failing_workflows(failing_workflows)

        # Generate timestamp
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Build comment body
        body = f"""🧭 **Release Readiness: {score:.1f}% {emoji}**

**Status:** {status_text}

📊 **Top Failing Workflows:**
{workflows_markdown}

📄 **Dashboard:** [{self.owner}/{self.repo_name}/v0.7.0-release-checklist.md](https://github.com/{self.owner}/{self.repo_name}/blob/{dashboard_branch}/v0.7.0-release-checklist.md)

🛡️ **Readiness Badge:**
![Readiness Badge]({badge_url})

**Last updated:** {timestamp}

{self.COMMENT_MARKER}"""

        return body

    def find_existing_comment(self) -> Any | None:
        """
        Find existing release dashboard comment.

        Returns:
            GitHub comment object if found, None otherwise
        """
        try:
            comments = list(self.pr.get_issue_comments())

            for comment in comments:
                if self.COMMENT_MARKER in comment.body:
                    if self.verbose:
                        print(
                            f"✓ Found existing release dashboard comment (ID: {comment.id})"
                        )
                    return comment

            if self.verbose:
                print("ℹ No existing release dashboard comment found")
            return None

        except GithubException as e:
            if self.verbose:
                print(f"⚠ Warning: Could not search for existing comments: {e}")
            return None

    def upsert_pr_comment(
        self, body: str, marker: str | None = None, strict: bool = False
    ) -> bool:
        """
        Post or update PR comment with release readiness information.

        Args:
            body: Comment body content
            marker: Optional custom marker (defaults to class marker)
            strict: If True, raise exceptions on failure instead of returning False

        Returns:
            True if successful, False otherwise (unless strict=True)
        """
        marker = marker or self.COMMENT_MARKER

        try:
            # Look for existing comment
            existing_comment = self.find_existing_comment()

            if existing_comment:
                # Update existing comment
                if self.verbose:
                    print("📝 Updating existing release dashboard comment...")
                existing_comment.edit(body)
                if self.verbose:
                    print("✅ Successfully updated PR comment")
            else:
                # Create new comment
                if self.verbose:
                    print("📝 Creating new release dashboard comment...")
                self.pr.create_issue_comment(body)
                if self.verbose:
                    print("✅ Successfully created PR comment")

            return True

        except GithubException as e:
            error_msg = f"Failed to post/update PR comment: {e}"
            if strict:
                raise RuntimeError(error_msg)
            else:
                if self.verbose:
                    print(f"⚠ Warning: {error_msg}")
                return False
        except Exception as e:
            error_msg = f"Unexpected error posting PR comment: {e}"
            if strict:
                raise RuntimeError(error_msg)
            else:
                if self.verbose:
                    print(f"⚠ Warning: {error_msg}")
                return False

    def post_readiness_comment(
        self,
        score_data: dict[str, Any],
        failing_workflows: list[dict[str, Any]],
        dashboard_branch: str = "main",
        strict: bool = False,
    ) -> bool:
        """
        Convenience method to post a complete readiness comment.

        Args:
            score_data: Readiness scoring data
            failing_workflows: List of failing workflows
            dashboard_branch: Branch containing the dashboard file
            strict: If True, raise exceptions on failure

        Returns:
            True if successful, False otherwise (unless strict=True)
        """
        try:
            body = self.generate_comment_body(
                score_data, failing_workflows, dashboard_branch
            )
            return self.upsert_pr_comment(body, strict=strict)
        except Exception as e:
            error_msg = f"Failed to generate or post readiness comment: {e}"
            if strict:
                raise RuntimeError(error_msg)
            else:
                if self.verbose:
                    print(f"⚠ Warning: {error_msg}")
                return False


def get_repo_and_pr(
    token: str | None = None,
    owner: str | None = None,
    repo: str | None = None,
    pr_number: int | None = None,
) -> tuple[str, str, int]:
    """
    Detect repository and PR information from various sources.

    Args:
        token: GitHub token
        owner: Repository owner (auto-detected if not provided)
        repo: Repository name (auto-detected if not provided)
        pr_number: PR number (auto-detected if not provided)

    Returns:
        Tuple of (owner, repo, pr_number)

    Raises:
        ValueError: If repository or PR cannot be detected
    """
    commenter = PRCommenter(
        token=token, owner=owner, repo=repo, pr_number=pr_number, verbose=True
    )
    return commenter.owner, commenter.repo_name, commenter.pr_number
