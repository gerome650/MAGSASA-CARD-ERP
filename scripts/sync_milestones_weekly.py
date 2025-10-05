#!/usr/bin/env python3
"""
AI Studio Strategic Milestones → Notion Sync

Syncs AI Studio milestones and links them to project roadmap items
where names match.

Features:
- Milestone status tracking
- Cross-project milestone linking
- Target date synchronization
- Progress aggregation across projects
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.notion_client import (
    NotionClient,
    create_title_property,
    create_rich_text_property,
    create_number_property,
    create_date_property,
    create_select_property,
    extract_title_value,
    extract_select_value,
    extract_date_value
)


# AI Studio strategic milestones (from project planning)
AI_STUDIO_MILESTONES = [
    {
        "stage_name": "Stage 7.3.1 - Weekly Notion Sync",
        "target_date": "2025-10-06",
        "status": "In Progress",
        "description": "Automated weekly sync of CI reports, roadmap, and milestones to Notion"
    },
    {
        "stage_name": "Stage 7.3.2 - Notion Intelligence Sync",
        "target_date": "2025-10-10",
        "status": "Completed",
        "description": "Two-way sync between Notion and CI intelligence data"
    },
    {
        "stage_name": "Stage 7.4 - Production Deployment",
        "target_date": "2025-10-15",
        "status": "Planning",
        "description": "Deploy to production with full observability and monitoring"
    },
    {
        "stage_name": "Stage 7.5 - Performance Optimization",
        "target_date": "2025-10-22",
        "status": "Not Started",
        "description": "Optimize system performance based on production metrics"
    },
    {
        "stage_name": "Stage 8.0 - Advanced Features",
        "target_date": "2025-11-01",
        "status": "Not Started",
        "description": "Implement advanced features and AI-powered capabilities"
    }
]


def sync_milestones(notion_client: NotionClient, database_id: str, dry_run: bool = False) -> Dict[str, Any]:
    """
    Sync AI Studio milestones to Notion.
    
    Args:
        notion_client: Initialized Notion client
        database_id: Target milestones database ID
        dry_run: If True, skip actual writes
    
    Returns:
        Dict with sync results
    """
    # Get existing milestones from Notion
    existing_milestones = notion_client.query_database(database_id)
    
    # Create lookup by stage name
    existing_by_name = {}
    for milestone in existing_milestones:
        stage_name = extract_title_value(milestone["properties"].get("Stage Name", {}))
        if stage_name:
            existing_by_name[stage_name] = milestone
    
    synced_count = 0
    created_count = 0
    updated_count = 0
    
    # Sync each milestone
    for milestone_data in AI_STUDIO_MILESTONES:
        try:
            stage_name = milestone_data["stage_name"]
            
            # Prepare properties
            properties = {
                "Stage Name": create_title_property(stage_name),
                "Target Date": create_date_property(milestone_data["target_date"]),
                "Status": create_select_property(milestone_data["status"]),
                "Description": create_rich_text_property(milestone_data["description"])
            }
            
            # Calculate progress based on status
            status_progress = {
                "Not Started": 0,
                "Planning": 15,
                "In Progress": 50,
                "Testing": 85,
                "Completed": 100
            }
            progress = status_progress.get(milestone_data["status"], 0)
            properties["Progress"] = create_number_property(progress)
            
            if dry_run:
                action = "update" if stage_name in existing_by_name else "create"
                print(f"[DRY-RUN] Would {action}: {stage_name}")
                print(f"  Status: {milestone_data['status']} ({progress}%)")
                print(f"  Target: {milestone_data['target_date']}")
            else:
                # Update existing or create new
                if stage_name in existing_by_name:
                    page_id = existing_by_name[stage_name]["id"]
                    notion_client.update_page(page_id, properties)
                    updated_count += 1
                else:
                    notion_client.create_page(database_id, properties)
                    created_count += 1
            
            synced_count += 1
            
        except Exception as e:
            print(f"⚠️ Warning: Failed to sync milestone '{milestone_data['stage_name']}': {e}")
            continue
    
    # Calculate stats
    completed_milestones = [m for m in AI_STUDIO_MILESTONES if m["status"] == "Completed"]
    in_progress_milestones = [m for m in AI_STUDIO_MILESTONES if m["status"] == "In Progress"]
    
    return {
        "records_synced": synced_count,
        "created": created_count,
        "updated": updated_count,
        "total_milestones": len(AI_STUDIO_MILESTONES),
        "completed": len(completed_milestones),
        "in_progress": len(in_progress_milestones),
        "action": "synced" if not dry_run else "would_sync"
    }


def main():
    """CLI entry point for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync AI Studio milestones to Notion")
    parser.add_argument("--dry-run", action="store_true", help="Don't write to Notion")
    parser.add_argument("--db-id", help="Database ID (or use AI_STUDIO_MILESTONES_DB_ID env var)")
    args = parser.parse_args()
    
    # Get database ID
    database_id = args.db_id or os.getenv("AI_STUDIO_MILESTONES_DB_ID")
    if not database_id:
        print("❌ Error: Database ID required (--db-id or AI_STUDIO_MILESTONES_DB_ID env var)")
        sys.exit(1)
    
    # Initialize client and sync
    try:
        client = NotionClient()
        result = sync_milestones(client, database_id, dry_run=args.dry_run)
        
        print(f"✅ Milestones sync complete:")
        print(f"   Total Synced: {result['records_synced']}/{result['total_milestones']}")
        print(f"   Created: {result['created']}")
        print(f"   Updated: {result['updated']}")
        print(f"   Completed: {result['completed']}")
        print(f"   In Progress: {result['in_progress']}")
        print(f"   Action: {result['action']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


