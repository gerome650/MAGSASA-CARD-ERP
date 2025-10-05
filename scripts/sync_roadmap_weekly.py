#!/usr/bin/env python3
"""
Roadmap Milestones → Notion Sync

Syncs project roadmap milestones with progress tracking, risk assessment,
and next action items.

Features:
- Progress calculation (completion %)
- Risk identification (at-risk items)
- Drift tracking (days behind schedule)
- Next action recommendations
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.notion_client import (
    NotionClient,
    create_number_property,
    create_rich_text_property,
    create_select_property,
    extract_date_value,
    extract_select_value,
    extract_title_value,
)


def calculate_milestone_progress(milestone: dict[str, Any]) -> dict[str, Any]:
    """
    Calculate progress metrics for a milestone.

    Args:
        milestone: Notion page object with milestone data

    Returns:
        Dict with progress, risk_level, next_action, drift_days
    """
    properties = milestone.get("properties", {})

    # Extract current values
    status = extract_select_value(properties.get("Status", {}))
    target_date_str = extract_date_value(properties.get("Target Date", {}))

    # Default values
    progress = 0
    risk_level = "Low"
    next_action = "Begin implementation"
    drift_days = 0

    # Calculate based on status
    status_progress = {
        "Not Started": 0,
        "Planning": 15,
        "In Progress": 50,
        "Testing": 80,
        "Completed": 100,
        "Blocked": 25,
    }
    progress = status_progress.get(status, 0)

    # Calculate drift if target date exists
    if target_date_str:
        try:
            target_date = datetime.fromisoformat(target_date_str.replace("Z", "+00:00"))
            today = datetime.utcnow().replace(tzinfo=target_date.tzinfo)

            if status != "Completed":
                if today > target_date:
                    # Overdue
                    drift_days = (today - target_date).days
                    risk_level = "High" if drift_days > 7 else "Medium"
                elif (target_date - today).days < 7 and progress < 80:
                    # Due soon but not nearly done
                    risk_level = "Medium"
        except Exception:
            pass

    # Determine next action
    if status == "Completed":
        next_action = "Done - Monitor stability"
    elif status == "Blocked":
        next_action = "Resolve blockers ASAP"
    elif status == "Testing":
        next_action = "Complete testing & validation"
    elif status == "In Progress":
        next_action = "Continue implementation"
    elif risk_level in ["High", "Medium"]:
        next_action = "Accelerate - at risk"

    return {
        "progress": progress,
        "risk_level": risk_level,
        "next_action": next_action,
        "drift_days": drift_days,
    }


def sync_roadmap(
    notion_client: NotionClient, database_id: str, dry_run: bool = False
) -> dict[str, Any]:
    """
    Sync roadmap milestones with updated progress and risk metrics.

    Args:
        notion_client: Initialized Notion client
        database_id: Target roadmap database ID
        dry_run: If True, skip actual writes

    Returns:
        Dict with sync results
    """
    # Query all roadmap items
    milestones = notion_client.query_database(database_id)

    synced_count = 0
    at_risk_count = 0
    completed_count = 0

    for milestone in milestones:
        try:
            # Calculate progress metrics
            metrics = calculate_milestone_progress(milestone)

            # Track stats
            if metrics["risk_level"] in ["High", "Medium"]:
                at_risk_count += 1
            if metrics["progress"] == 100:
                completed_count += 1

            # Prepare update properties
            update_props = {
                "Progress": create_number_property(metrics["progress"]),
                "Risk Level": create_select_property(metrics["risk_level"]),
                "Next Action": create_rich_text_property(metrics["next_action"]),
            }

            # Add drift if significant
            if metrics["drift_days"] > 0:
                update_props["Drift (days)"] = create_number_property(
                    metrics["drift_days"]
                )

            if dry_run:
                milestone_name = extract_title_value(
                    milestone["properties"].get("Name", {})
                )
                print(f"[DRY-RUN] Would update: {milestone_name}")
                print(f"  Progress: {metrics['progress']}%")
                print(f"  Risk: {metrics['risk_level']}")
                print(f"  Next: {metrics['next_action']}")
            else:
                # Update the milestone
                notion_client.update_page(milestone["id"], update_props)

            synced_count += 1

        except Exception as e:
            print(f"⚠️ Warning: Failed to update milestone {milestone['id'][:8]}: {e}")
            continue

    # Calculate overall stats
    total_milestones = len(milestones)
    completion_rate = (
        (completed_count / total_milestones * 100) if total_milestones > 0 else 0
    )

    return {
        "records_synced": synced_count,
        "total_milestones": total_milestones,
        "completed": completed_count,
        "at_risk": at_risk_count,
        "completion_rate": round(completion_rate, 1),
        "action": "updated" if not dry_run else "would_update",
    }


def main():
    """CLI entry point for testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Sync roadmap to Notion")
    parser.add_argument("--dry-run", action="store_true", help="Don't write to Notion")
    parser.add_argument(
        "--db-id", help="Database ID (or use MAGSASA_ROADMAP_DB_ID env var)"
    )
    args = parser.parse_args()

    # Get database ID
    database_id = args.db_id or os.getenv("MAGSASA_ROADMAP_DB_ID")
    if not database_id:
        print(
            "❌ Error: Database ID required (--db-id or MAGSASA_ROADMAP_DB_ID env var)"
        )
        sys.exit(1)

    # Initialize client and sync
    try:
        client = NotionClient()
        result = sync_roadmap(client, database_id, dry_run=args.dry_run)

        print("✅ Roadmap sync complete:")
        print(
            f"   Milestones Updated: {result['records_synced']}/{result['total_milestones']}"
        )
        print(f"   Completed: {result['completed']} ({result['completion_rate']}%)")
        print(f"   At Risk: {result['at_risk']}")
        print(f"   Action: {result['action']}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
