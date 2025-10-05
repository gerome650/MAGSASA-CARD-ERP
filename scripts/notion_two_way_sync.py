#!/usr/bin/env python3
"""
Notion Two-Way Sync Agent

This script enables bidirectional synchronization between Notion roadmap
and GitHub issues/PRs, allowing status changes in Notion to propagate
back to GitHub.

Stage 7.3.2: Advanced Features - Two-Way Sync

Usage:
    python scripts/notion_two_way_sync.py --sync-from-notion
    python scripts/notion_two_way_sync.py --sync-to-notion
    python scripts/notion_two_way_sync.py --full-sync
"""

import sys
import os
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import requests
import re

# Import centralized Notion client
sys.path.append(str(Path(__file__).parent.parent))
from utils.notion_client import (
    NotionClient,
    get_safe_database_id,
    extract_title_value,
    extract_select_value,
    extract_rich_text_value
)


@dataclass
class SyncChange:
    """Represents a change detected during sync."""
    type: str  # 'milestone_status', 'milestone_progress', 'milestone_notes'
    milestone_name: str
    old_value: Any
    new_value: Any
    source: str  # 'notion' or 'github'
    timestamp: str


class TwoWaySyncAgent:
    """Handles bidirectional sync between Notion and GitHub."""
    
    def __init__(self, github_token: str, github_repo: str):
        """Initialize the two-way sync agent."""
        # Use centralized Notion client
        self.notion_client = NotionClient()
        
        # Get database ID from environment variables with safety checks
        self.roadmap_db_id = get_safe_database_id("MAGSASA", "ROADMAP")
        
        # Fallback to legacy environment variable for backward compatibility
        if not self.roadmap_db_id:
            self.roadmap_db_id = get_safe_database_id("NOTION_ROADMAP", "")
        
        self.github_token = github_token
        self.github_repo = github_repo
        self.github_base_url = f"https://api.github.com/repos/{github_repo}"
        
        self.github_headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def sync_from_notion(self, dry_run: bool = False) -> List[SyncChange]:
        """Sync changes from Notion to GitHub."""
        print("📤 Syncing changes from Notion to GitHub...")
        
        changes = []
        
        try:
            # Get all milestones from Notion
            milestones = self._fetch_notion_milestones()
            
            for milestone in milestones:
                milestone_changes = self._process_milestone_changes(milestone, dry_run)
                changes.extend(milestone_changes)
            
            print(f"✅ Processed {len(changes)} changes from Notion")
            return changes
            
        except Exception as e:
            print(f"❌ Error syncing from Notion: {e}")
            return []
    
    def sync_to_notion(self, dry_run: bool = False) -> List[SyncChange]:
        """Sync changes from GitHub to Notion."""
        print("📥 Syncing changes from GitHub to Notion...")
        
        changes = []
        
        try:
            # Get GitHub issues with roadmap labels
            github_issues = self._fetch_github_roadmap_issues()
            
            for issue in github_issues:
                issue_changes = self._process_github_issue_changes(issue, dry_run)
                changes.extend(issue_changes)
            
            print(f"✅ Processed {len(changes)} changes from GitHub")
            return changes
            
        except Exception as e:
            print(f"❌ Error syncing to Notion: {e}")
            return []
    
    def full_sync(self, dry_run: bool = False) -> Dict[str, List[SyncChange]]:
        """Perform full bidirectional sync."""
        print("🔄 Performing full bidirectional sync...")
        
        from_notion = self.sync_from_notion(dry_run)
        to_notion = self.sync_to_notion(dry_run)
        
        return {
            "from_notion": from_notion,
            "to_notion": to_notion,
            "total_changes": len(from_notion) + len(to_notion)
        }
    
    def _fetch_notion_milestones(self) -> List[Dict[str, Any]]:
        """Fetch all milestones from Notion database."""
        if not self.roadmap_db_id:
            print("⚠️ Roadmap database ID not configured. Skipping Notion milestone fetch.")
            return []
        
        return self.notion_client.query_database(self.roadmap_db_id)
    
    def _fetch_github_roadmap_issues(self) -> List[Dict[str, Any]]:
        """Fetch GitHub issues with roadmap-related labels."""
        url = f"{self.github_base_url}/issues"
        params = {
            "labels": "roadmap,milestone",
            "state": "all",
            "per_page": 100
        }
        
        response = requests.get(url, headers=self.github_headers, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def _process_milestone_changes(self, milestone: Dict[str, Any], dry_run: bool) -> List[SyncChange]:
        """Process changes for a single milestone from Notion."""
        changes = []
        
        try:
            props = milestone["properties"]
            milestone_name = extract_title_value(props.get("🧩 Milestone", {}))
            status = extract_select_value(props.get("✅ Status", {}))
            progress = props.get("📊 Progress", {}).get("number", 0) or 0
            notes = extract_rich_text_value(props.get("📝 Notes", {}))
            
            if not milestone_name:
                return changes
            
            # Find associated GitHub issue
            github_issue = self._find_github_issue_for_milestone(milestone_name)
            
            if github_issue:
                # Check for status changes
                current_github_state = self._map_notion_status_to_github(status)
                
                if github_issue["state"] != current_github_state:
                    if not dry_run:
                        self._update_github_issue_status(github_issue["number"], current_github_state)
                    
                    changes.append(SyncChange(
                        type="milestone_status",
                        milestone_name=milestone_name,
                        old_value=github_issue["state"],
                        new_value=current_github_state,
                        source="notion",
                        timestamp=datetime.now().isoformat()
                    ))
                
                # Check for progress updates in issue body
                if progress > 0:
                    progress_text = f"**Progress:** {progress}%"
                    if progress_text not in github_issue["body"]:
                        if not dry_run:
                            self._update_github_issue_progress(github_issue["number"], progress)
                        
                        changes.append(SyncChange(
                            type="milestone_progress",
                            milestone_name=milestone_name,
                            old_value="N/A",
                            new_value=f"{progress}%",
                            source="notion",
                            timestamp=datetime.now().isoformat()
                        ))
                
                # Check for notes updates
                if notes and notes not in github_issue["body"]:
                    if not dry_run:
                        self._update_github_issue_notes(github_issue["number"], notes)
                    
                    changes.append(SyncChange(
                        type="milestone_notes",
                        milestone_name=milestone_name,
                        old_value="N/A",
                        new_value=notes,
                        source="notion",
                        timestamp=datetime.now().isoformat()
                    ))
            
        except Exception as e:
            print(f"⚠️ Error processing milestone {milestone_name}: {e}")
        
        return changes
    
    def _process_github_issue_changes(self, issue: Dict[str, Any], dry_run: bool) -> List[SyncChange]:
        """Process changes for a single GitHub issue."""
        changes = []
        
        try:
            # Extract milestone name from issue title or body
            milestone_name = self._extract_milestone_name_from_issue(issue)
            
            if not milestone_name:
                return changes
            
            # Find corresponding Notion milestone
            notion_milestone = self._find_notion_milestone_by_name(milestone_name)
            
            if notion_milestone:
                # Check for status changes
                github_status = self._map_github_state_to_notion(issue["state"])
                current_notion_status = extract_select_value(
                    notion_milestone["properties"].get("✅ Status", {})
                )
                
                if github_status != current_notion_status:
                    if not dry_run:
                        self._update_notion_milestone_status(notion_milestone["id"], github_status)
                    
                    changes.append(SyncChange(
                        type="milestone_status",
                        milestone_name=milestone_name,
                        old_value=current_notion_status,
                        new_value=github_status,
                        source="github",
                        timestamp=datetime.now().isoformat()
                    ))
            
        except Exception as e:
            print(f"⚠️ Error processing GitHub issue {issue['number']}: {e}")
        
        return changes
    
    def _find_github_issue_for_milestone(self, milestone_name: str) -> Optional[Dict[str, Any]]:
        """Find GitHub issue associated with a milestone."""
        issues = self._fetch_github_roadmap_issues()
        
        for issue in issues:
            if milestone_name.lower() in issue["title"].lower():
                return issue
        
        return None
    
    def _find_notion_milestone_by_name(self, milestone_name: str) -> Optional[Dict[str, Any]]:
        """Find Notion milestone by name."""
        milestones = self._fetch_notion_milestones()
        
        for milestone in milestones:
            name = extract_title_value(milestone["properties"].get("🧩 Milestone", {}))
            if name and name.lower() == milestone_name.lower():
                return milestone
        
        return None
    
    def _map_notion_status_to_github(self, notion_status: str) -> str:
        """Map Notion status to GitHub state."""
        mapping = {
            "Completed": "closed",
            "In Progress": "open",
            "Planned": "open",
            "Blocked": "open"
        }
        return mapping.get(notion_status, "open")
    
    def _map_github_state_to_notion(self, github_state: str) -> str:
        """Map GitHub state to Notion status."""
        mapping = {
            "open": "In Progress",
            "closed": "Completed"
        }
        return mapping.get(github_state, "In Progress")
    
    def _update_github_issue_status(self, issue_number: int, state: str):
        """Update GitHub issue state."""
        url = f"{self.github_base_url}/issues/{issue_number}"
        payload = {"state": state}
        
        response = requests.patch(url, headers=self.github_headers, json=payload)
        response.raise_for_status()
    
    def _update_github_issue_progress(self, issue_number: int, progress: int):
        """Update GitHub issue with progress information."""
        url = f"{self.github_base_url}/issues/{issue_number}/comments"
        payload = {
            "body": f"📊 **Milestone Progress Updated:** {progress}%\n\n*Updated via Notion sync at {datetime.now().isoformat()}*"
        }
        
        response = requests.post(url, headers=self.github_headers, json=payload)
        response.raise_for_status()
    
    def _update_github_issue_notes(self, issue_number: int, notes: str):
        """Update GitHub issue with notes from Notion."""
        url = f"{self.github_base_url}/issues/{issue_number}/comments"
        payload = {
            "body": f"📝 **Milestone Notes:**\n\n{notes}\n\n*Updated via Notion sync at {datetime.now().isoformat()}*"
        }
        
        response = requests.post(url, headers=self.github_headers, json=payload)
        response.raise_for_status()
    
    def _update_notion_milestone_status(self, page_id: str, status: str):
        """Update Notion milestone status."""
        from utils.notion_client import create_select_property
        
        properties = {
            "✅ Status": create_select_property(status)
        }
        
        self.notion_client.update_page(page_id, properties)
    
    def _extract_milestone_name_from_issue(self, issue: Dict[str, Any]) -> Optional[str]:
        """Extract milestone name from GitHub issue."""
        title = issue["title"]
        body = issue.get("body", "")
        
        # Look for milestone patterns in title
        patterns = [
            r"milestone[:\s]+(.+)",
            r"stage[:\s]+(.+)",
            r"roadmap[:\s]+(.+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Look for milestone patterns in body
        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
# Extract methods are now imported from utils.notion_client


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Two-way sync between Notion roadmap and GitHub",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sync changes from Notion to GitHub
  python scripts/notion_two_way_sync.py --sync-from-notion
  
  # Sync changes from GitHub to Notion
  python scripts/notion_two_way_sync.py --sync-to-notion
  
  # Full bidirectional sync
  python scripts/notion_two_way_sync.py --full-sync
  
  # Dry run to see what would change
  python scripts/notion_two_way_sync.py --full-sync --dry-run
        """
    )
    
    parser.add_argument(
        "--sync-from-notion",
        action="store_true",
        help="Sync changes from Notion to GitHub"
    )
    parser.add_argument(
        "--sync-to-notion",
        action="store_true",
        help="Sync changes from GitHub to Notion"
    )
    parser.add_argument(
        "--full-sync",
        action="store_true",
        help="Perform full bidirectional sync"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without making updates"
    )
    # Note: API key and database IDs are now configured via environment variables
    # See env.template for configuration options
    parser.add_argument(
        "--github-token",
        help="GitHub token (or set GITHUB_TOKEN env var)"
    )
    parser.add_argument(
        "--github-repo",
        help="GitHub repository (or set GITHUB_REPOSITORY env var)"
    )
    
    args = parser.parse_args()
    
    # Check for required environment variables
    if not os.getenv("NOTION_API_KEY"):
        print("❌ Error: NOTION_API_KEY environment variable is required.")
        print("Please copy env.template to .env and set your Notion API key.")
        sys.exit(1)
    
    github_token = args.github_token or os.getenv("GITHUB_TOKEN")
    github_repo = args.github_repo or os.getenv("GITHUB_REPOSITORY")
    
    if not github_token:
        print("❌ Error: GitHub token required. Set GITHUB_TOKEN env var or use --github-token")
        sys.exit(1)
    
    if not github_repo:
        print("❌ Error: GitHub repository required. Set GITHUB_REPOSITORY env var or use --github-repo")
        sys.exit(1)
    
    try:
        # Initialize sync agent (now uses centralized client and environment variables)
        sync_agent = TwoWaySyncAgent(
            github_token=github_token,
            github_repo=github_repo
        )
        
        if args.dry_run:
            print("🔍 DRY RUN MODE - No changes will be made\n")
        
        if args.sync_from_notion:
            changes = sync_agent.sync_from_notion(dry_run=args.dry_run)
            print(f"\n📤 Changes from Notion to GitHub: {len(changes)}")
            for change in changes:
                print(f"  - {change.type}: {change.milestone_name} ({change.old_value} → {change.new_value})")
        
        if args.sync_to_notion:
            changes = sync_agent.sync_to_notion(dry_run=args.dry_run)
            print(f"\n📥 Changes from GitHub to Notion: {len(changes)}")
            for change in changes:
                print(f"  - {change.type}: {change.milestone_name} ({change.old_value} → {change.new_value})")
        
        if args.full_sync:
            result = sync_agent.full_sync(dry_run=args.dry_run)
            print(f"\n🔄 Full sync completed:")
            print(f"  - From Notion: {len(result['from_notion'])} changes")
            print(f"  - To Notion: {len(result['to_notion'])} changes")
            print(f"  - Total: {result['total_changes']} changes")
        
        if not any([args.sync_from_notion, args.sync_to_notion, args.full_sync]):
            parser.print_help()
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
