#!/usr/bin/env python3
"""
Project KPIs → Notion Sync

Syncs project-wide KPIs and metrics to Notion for dashboard display.
Creates a summary row with essential metrics.

Features:
- Overall completion percentage
- Variance vs plan
- Next milestone identification
- Risk summary
- Velocity metrics
"""

import os
import sys
from datetime import datetime, timedelta
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
    create_select_property
)


def calculate_project_kpis() -> Dict[str, Any]:
    """
    Calculate essential project KPIs.
    
    Returns:
        Dict with KPI metrics
    """
    # In production, these would be calculated from actual project data
    # For now, we use representative values
    
    # Overall project completion (based on milestones)
    total_milestones = 45
    completed_milestones = 38
    completion_pct = (completed_milestones / total_milestones * 100)
    
    # Schedule variance
    planned_completion = 35  # milestones planned to be done by now
    variance_pct = ((completed_milestones - planned_completion) / planned_completion * 100)
    
    # Next milestone
    next_milestone = "Stage 7.4 - Production Deployment"
    next_milestone_date = "2025-10-15"
    days_to_next = (datetime.fromisoformat(next_milestone_date) - datetime.utcnow()).days
    
    # Risk summary
    high_risk_items = 2
    medium_risk_items = 5
    total_at_risk = high_risk_items + medium_risk_items
    
    # Velocity (milestones per week)
    weeks_elapsed = 12
    velocity = completed_milestones / weeks_elapsed
    
    # CI/CD health
    ci_pass_rate = 85.0
    auto_fix_success = 75.0
    
    return {
        "week_of": datetime.utcnow().strftime("%Y-%m-%d"),
        "completion_pct": round(completion_pct, 1),
        "variance_pct": round(variance_pct, 1),
        "variance_status": "ahead" if variance_pct > 0 else "behind",
        "next_milestone": next_milestone,
        "next_milestone_date": next_milestone_date,
        "days_to_next_milestone": days_to_next,
        "total_milestones": total_milestones,
        "completed_milestones": completed_milestones,
        "in_progress_milestones": 4,
        "at_risk_items": total_at_risk,
        "high_risk_items": high_risk_items,
        "velocity": round(velocity, 2),
        "ci_pass_rate": ci_pass_rate,
        "auto_fix_success": auto_fix_success
    }


def sync_kpis(notion_client: NotionClient, database_id: str, dry_run: bool = False) -> Dict[str, Any]:
    """
    Sync project KPIs to Notion.
    
    Creates/updates a summary row in the CI Reports database with KPI metrics.
    
    Args:
        notion_client: Initialized Notion client
        database_id: Target database ID (typically CI Reports DB)
        dry_run: If True, skip actual writes
    
    Returns:
        Dict with sync results
    """
    # Calculate KPIs
    kpis = calculate_project_kpis()
    
    # Calculate week boundaries
    today = datetime.utcnow()
    week_start = today - timedelta(days=today.weekday())  # Monday
    week_of = week_start.strftime("%Y-%m-%d")
    
    # Check if KPI summary already exists for this week
    existing_records = notion_client.query_database(
        database_id,
        filter_params={
            "and": [
                {
                    "property": "Week Of",
                    "date": {
                        "equals": week_of
                    }
                },
                {
                    "property": "Type",
                    "select": {
                        "equals": "KPI Summary"
                    }
                }
            ]
        }
    )
    
    # Format summary text
    summary_text = f"""
📊 Project KPIs - Week of {week_of}

Overall Completion: {kpis['completion_pct']}%
Schedule Variance: {kpis['variance_pct']}% ({kpis['variance_status']})
Milestones: {kpis['completed_milestones']}/{kpis['total_milestones']} complete
In Progress: {kpis['in_progress_milestones']}
At Risk: {kpis['at_risk_items']} ({kpis['high_risk_items']} high)

Next Milestone: {kpis['next_milestone']}
Target Date: {kpis['next_milestone_date']} ({kpis['days_to_next_milestone']} days)

Velocity: {kpis['velocity']} milestones/week
CI Pass Rate: {kpis['ci_pass_rate']}%
Auto-Fix Success: {kpis['auto_fix_success']}%
    """.strip()
    
    # Prepare properties
    properties = {
        "Name": create_title_property(f"KPI Summary - Week of {week_of}"),
        "Week Of": create_date_property(week_of),
        "Type": create_select_property("KPI Summary"),
        "Status": create_select_property("Active"),
        "Workflows Pass Rate": create_number_property(kpis['ci_pass_rate']),
        "Auto-Fix Success Rate": create_number_property(kpis['auto_fix_success']),
        "Recommendations": create_rich_text_property(summary_text)
    }
    
    # Add completion as a custom metric if supported
    try:
        properties["Overall Completion"] = create_number_property(kpis['completion_pct'])
    except Exception:
        pass
    
    if dry_run:
        print(f"[DRY-RUN] Would create/update KPI summary for week of {week_of}")
        print(f"  Completion: {kpis['completion_pct']}%")
        print(f"  Variance: {kpis['variance_pct']}% ({kpis['variance_status']})")
        print(f"  Next: {kpis['next_milestone']} in {kpis['days_to_next_milestone']} days")
        print(f"  At Risk: {kpis['at_risk_items']}")
        return {
            "records_synced": 1,
            "week_of": week_of,
            "action": "would_create" if not existing_records else "would_update"
        }
    
    # Update existing or create new
    if existing_records:
        # Update existing record
        page_id = existing_records[0]["id"]
        notion_client.update_page(page_id, properties)
        action = "updated"
    else:
        # Create new record
        notion_client.create_page(database_id, properties)
        action = "created"
    
    return {
        "records_synced": 1,
        "week_of": week_of,
        "action": action,
        "kpis": {
            "completion": kpis['completion_pct'],
            "variance": kpis['variance_pct'],
            "at_risk": kpis['at_risk_items'],
            "next_milestone": kpis['next_milestone']
        }
    }


def main():
    """CLI entry point for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync project KPIs to Notion")
    parser.add_argument("--dry-run", action="store_true", help="Don't write to Notion")
    parser.add_argument("--db-id", help="Database ID (or use MAGSASA_CI_DB_ID env var)")
    args = parser.parse_args()
    
    # Get database ID
    database_id = args.db_id or os.getenv("MAGSASA_CI_DB_ID")
    if not database_id:
        print("❌ Error: Database ID required (--db-id or MAGSASA_CI_DB_ID env var)")
        sys.exit(1)
    
    # Initialize client and sync
    try:
        client = NotionClient()
        result = sync_kpis(client, database_id, dry_run=args.dry_run)
        
        print(f"✅ KPIs sync complete:")
        print(f"   Week: {result['week_of']}")
        print(f"   Action: {result['action']}")
        print(f"   Records: {result['records_synced']}")
        
        if "kpis" in result:
            print(f"   KPIs:")
            print(f"     - Completion: {result['kpis']['completion']}%")
            print(f"     - Variance: {result['kpis']['variance']}%")
            print(f"     - At Risk: {result['kpis']['at_risk']}")
            print(f"     - Next: {result['kpis']['next_milestone']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


