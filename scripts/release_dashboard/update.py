"""
Markdown Updater Module

Handles updating the release checklist markdown file with CI data and scores.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class MarkdownUpdater:
    """Updates markdown sections in the release checklist."""
    
    def __init__(self, checklist_path: str = "v0.7.0-release-checklist.md", verbose: bool = False):
        """
        Initialize the markdown updater.
        
        Args:
            checklist_path: Path to the release checklist markdown file
            verbose: Enable verbose logging
        """
        self.checklist_path = Path(checklist_path)
        self.verbose = verbose
        self.content = None
    
    def read(self) -> str:
        """Read the current checklist file."""
        try:
            with open(self.checklist_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
            
            if self.verbose:
                print(f"✓ Read checklist file: {self.checklist_path}")
            
            return self.content
        except FileNotFoundError:
            raise FileNotFoundError(f"Checklist file not found: {self.checklist_path}")
        except Exception as e:
            raise IOError(f"Error reading checklist file: {e}")
    
    def write(self, content: Optional[str] = None) -> None:
        """Write updated content to the checklist file."""
        try:
            write_content = content if content is not None else self.content
            
            if write_content is None:
                raise ValueError("No content to write")
            
            with open(self.checklist_path, 'w', encoding='utf-8') as f:
                f.write(write_content)
            
            if self.verbose:
                print(f"✓ Updated checklist file: {self.checklist_path}")
                
        except Exception as e:
            raise IOError(f"Error writing checklist file: {e}")
    
    def generate_ci_snapshot(self, runs: List[Dict[str, Any]], health: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate CI snapshot markdown section.
        
        Args:
            runs: List of workflow run data
            health: Optional CI health summary
        
        Returns:
            Markdown formatted CI snapshot section
        """
        if not runs:
            return """<!-- CI_SNAPSHOT_START -->
## 📡 Last CI Snapshot

**Last Updated:** """ + datetime.now().strftime("%B %d, %Y at %H:%M UTC") + """  
**CI Health Status:** ⚠️ NO DATA  

No recent workflow runs found.
<!-- CI_SNAPSHOT_END -->"""
        
        # Determine health status
        health_emoji = "🟢"
        health_text = "HEALTHY"
        
        if health:
            if health['status'] == 'critical':
                health_emoji = "🔴"
                health_text = "CRITICAL"
            elif health['status'] == 'warning':
                health_emoji = "🟡"
                health_text = "WARNING"
        
        lines = [
            "<!-- CI_SNAPSHOT_START -->",
            "## 📡 Last CI Snapshot",
            "",
            f"**Last Updated:** {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}  ",
            f"**CI Health Status:** {health_emoji} {health_text}  ",
            ""
        ]
        
        # Add health metrics if available
        if health:
            lines.extend([
                "### CI Health Metrics",
                f"- **Success Rate:** {health['success_rate']}%",
                f"- **Total Runs (last 50):** {health['total_runs']}",
                f"- **Successful:** {health.get('success_count', 0)}",
                f"- **Failed:** {health.get('failure_count', 0)}",
                "",
                "---",
                ""
            ])
        
        # Create table of recent runs
        lines.extend([
            "### Recent Workflow Runs",
            "| Workflow | Status | Duration | Branch | Commit | Last Run |",
            "|----------|--------|----------|--------|--------|----------|"
        ])
        
        for run in runs[:10]:  # Limit to 10 most recent
            from .fetch import GitHubWorkflowFetcher
            
            status_emoji = GitHubWorkflowFetcher.get_status_emoji(run.get('conclusion'), run.get('status', ''))
            status_text = run.get('conclusion') or run.get('status', 'unknown')
            
            duration = run.get('duration_seconds')
            duration_str = GitHubWorkflowFetcher().format_duration(duration) if duration else "N/A"
            
            branch = run.get('head_branch', 'N/A')
            if len(branch) > 15:
                branch = branch[:12] + "..."
            
            commit_sha = run.get('head_sha', 'N/A')
            commit_msg = run.get('commit_message', 'N/A')
            if commit_msg and len(commit_msg) > 30:
                commit_msg = commit_msg[:27] + "..."
            commit_display = f"{commit_sha}"
            
            last_run = run.get('created_at')
            if last_run:
                last_run_str = last_run.strftime("%Y-%m-%d %H:%M")
            else:
                last_run_str = "N/A"
            
            workflow_name = run.get('display_name', run.get('workflow_name', 'Unknown'))
            
            lines.append(
                f"| {workflow_name} | {status_emoji} {status_text} | {duration_str} | "
                f"{branch} | {commit_display} | {last_run_str} |"
            )
        
        # Add failing workflows section if any
        if health and health.get('failing_workflows'):
            lines.extend([
                "",
                "### ⚠️ Failing Workflows (Recent)",
                ""
            ])
            
            for fw in health['failing_workflows'][:3]:  # Top 3
                lines.append(f"- **{fw['name']}**: {fw['count']} failures - [View]({fw['url']})")
        
        lines.extend([
            "",
            "<!-- CI_SNAPSHOT_END -->"
        ])
        
        return "\n".join(lines)
    
    def generate_readiness_score_section(self, score_data: Dict[str, Any]) -> str:
        """
        Generate readiness score markdown section.
        
        Args:
            score_data: Score calculation results
        
        Returns:
            Markdown formatted readiness score section
        """
        total_score = score_data['total_score']
        status_emoji = score_data['status_emoji']
        status_text = score_data['status_text']
        
        lines = [
            "<!-- READINESS_SCORE_START -->",
            f"## 📊 Release Readiness Score: {total_score}% {status_emoji}",
            "",
            f"**Current Status:** {status_text}  ",
            f"**Last Updated:** {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}  ",
            "**Next Review:** Weekly during release window",
            "",
            "### Scoring Breakdown:",
            f"- **Core Gates ({score_data['core_passing']}/{score_data['core_total']}):** "
            f"{score_data['core_score']}% (weighted 50%)",
            f"- **Optional Gates ({score_data['optional_passing']}/{score_data['optional_total']}):** "
            f"{score_data['optional_score']}% (weighted 20%)",
            f"- **Deployment Automation ({score_data['deployment_passing']}/{score_data['deployment_total']}):** "
            f"{score_data['deployment_score']}% (weighted 20%)",
            f"- **Final Sign-Off ({score_data['signoff_passing']}/{score_data['signoff_total']}):** "
            f"{score_data['signoff_score']}% (weighted 10%)",
            "",
            f"**Weighted Total: {total_score}%**"
        ]
        
        # Add blockers if any
        if score_data.get('blockers'):
            lines.extend([
                "",
                "### 🚧 Current Blockers:",
            ])
            for blocker in score_data['blockers']:
                lines.append(f"- {blocker}")
        
        # Add recommendations if score is below 95%
        if total_score < 95:
            lines.extend([
                "",
                "### 📋 To Reach 95% (Release Ready):",
            ])
            
            if score_data['core_passing'] < score_data['core_total']:
                remaining = score_data['core_total'] - score_data['core_passing']
                lines.append(f"1. Complete {remaining} remaining core gate(s) - **CRITICAL**")
            
            if score_data['deployment_passing'] < score_data['deployment_total']:
                remaining = score_data['deployment_total'] - score_data['deployment_passing']
                lines.append(f"2. Complete {remaining} deployment automation item(s)")
            
            if score_data['signoff_passing'] < score_data['signoff_total'] - 1:
                remaining = score_data['signoff_total'] - score_data['signoff_passing']
                lines.append(f"3. Complete {remaining} sign-off checklist item(s)")
            
            if score_data['optional_passing'] < score_data['optional_total']:
                lines.append("4. Address optional gates to improve confidence")
        
        lines.append("<!-- READINESS_SCORE_END -->")
        
        return "\n".join(lines)
    
    def update_sections(self, ci_snapshot: str, readiness_score: str) -> str:
        """
        Update specific sections in the markdown content using markers.
        
        Args:
            ci_snapshot: CI snapshot markdown content
            readiness_score: Readiness score markdown content
        
        Returns:
            Updated markdown content
        """
        if self.content is None:
            self.read()
        
        content = self.content
        
        # Update CI Snapshot section
        ci_pattern = r'<!-- CI_SNAPSHOT_START -->.*?<!-- CI_SNAPSHOT_END -->'
        if re.search(ci_pattern, content, re.DOTALL):
            content = re.sub(ci_pattern, ci_snapshot, content, flags=re.DOTALL)
            if self.verbose:
                print("✓ Updated CI Snapshot section")
        else:
            # Append if markers don't exist
            content += f"\n\n{ci_snapshot}\n"
            if self.verbose:
                print("✓ Added CI Snapshot section (no markers found)")
        
        # Update Readiness Score section
        score_pattern = r'<!-- READINESS_SCORE_START -->.*?<!-- READINESS_SCORE_END -->'
        if re.search(score_pattern, content, re.DOTALL):
            content = re.sub(score_pattern, readiness_score, content, flags=re.DOTALL)
            if self.verbose:
                print("✓ Updated Readiness Score section")
        else:
            # Try to insert after overview section
            overview_pattern = r'(## 📦 Release Overview.*?\n---)'
            if re.search(overview_pattern, content, re.DOTALL):
                content = re.sub(
                    overview_pattern,
                    f'\\1\n\n{readiness_score}\n\n---',
                    content,
                    flags=re.DOTALL
                )
                if self.verbose:
                    print("✓ Inserted Readiness Score section after overview")
            else:
                # Prepend to content
                content = f"{readiness_score}\n\n{content}"
                if self.verbose:
                    print("✓ Prepended Readiness Score section")
        
        self.content = content
        return content
    
    def has_changes(self) -> bool:
        """Check if there are changes compared to the file on disk."""
        try:
            with open(self.checklist_path, 'r', encoding='utf-8') as f:
                disk_content = f.read()
            
            return self.content != disk_content
        except Exception:
            return True  # Assume changes if we can't read

