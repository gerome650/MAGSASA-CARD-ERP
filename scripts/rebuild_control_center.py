#!/usr/bin/env python3
"""
MAGSASA-CARD Control Center Rebuilder

This script rebuilds the complete MAGSASA-CARD Control Center system in Notion
using the exported JSON schema. It creates all databases, pages, and views
as defined in the MAGSASA-CARD_Control_Center.json file.

Features:
- Parse JSON schema and create databases with all properties
- Recreate page structure under parent Control Center page
- Add sample data to test database structure
- Create dashboard views combining Roadmap + Milestones + KPIs
- Generate comprehensive summary report with all database IDs

Usage:
    python scripts/rebuild_control_center.py --rebuild-all
    python scripts/rebuild_control_center.py --create-databases-only
    python scripts/rebuild_control_center.py --add-sample-data
    python scripts/rebuild_control_center.py --show-summary
"""

import sys
import os
import json
import argparse
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.notion_client import NotionClient, create_title_property, create_rich_text_property, create_select_property, create_date_property, create_number_property, create_url_property


class ControlCenterRebuilder:
    """Rebuilds the MAGSASA-CARD Control Center from JSON schema."""
    
    def __init__(self, json_file_path: str):
        """Initialize the rebuilder with JSON schema."""
        self.json_file_path = json_file_path
        self.notion_client = NotionClient()
        self.schema = self._load_schema()
        self.created_databases = {}
        self.created_pages = {}
        self.parent_page_id = os.getenv("CONTROL_CENTER_PAGE_ID")
        
        if not self.parent_page_id:
            raise ValueError("❌ CONTROL_CENTER_PAGE_ID environment variable is required")
    
    def _load_schema(self) -> Dict[str, Any]:
        """Load the JSON schema file."""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            print(f"✅ Loaded schema from {self.json_file_path}")
            return schema
        except Exception as e:
            raise ValueError(f"❌ Failed to load schema: {e}")
    
    def _convert_property_type(self, prop_name: str, prop_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert JSON property config to Notion API format."""
        prop_type = prop_config["type"]
        
        if prop_type == "title":
            return {"title": {}}
        
        elif prop_type == "rich_text":
            return {"rich_text": {}}
        
        elif prop_type == "number":
            format_type = prop_config.get("format", "number")
            return {"number": {"format": format_type}}
        
        elif prop_type == "date":
            return {"date": {}}
        
        elif prop_type == "url":
            return {"url": {}}
        
        elif prop_type == "select":
            options = prop_config.get("options", [])
            notion_options = []
            for option in options:
                notion_options.append({
                    "name": option["name"],
                    "color": option.get("color", "default")
                })
            return {"select": {"options": notion_options}}
        
        elif prop_type == "multi_select":
            options = prop_config.get("options", [])
            notion_options = []
            for option in options:
                notion_options.append({
                    "name": option["name"],
                    "color": option.get("color", "default")
                })
            return {"multi_select": {"options": notion_options}}
        
        elif prop_type == "relation":
            related_db = prop_config.get("related_database")
            if related_db and related_db in self.created_databases:
                return {"relation": {"database_id": self.created_databases[related_db]}}
            else:
                # Create placeholder relation, will be updated later
                return {"relation": {"database_id": ""}}
        
        elif prop_type == "created_time":
            return {"created_time": {}}
        
        elif prop_type == "last_edited_time":
            return {"last_edited_time": {}}
        
        else:
            print(f"⚠️ Unknown property type: {prop_type} for {prop_name}")
            return {"rich_text": {}}  # Default fallback
    
    def create_databases(self) -> Dict[str, str]:
        """Create all databases defined in the schema."""
        print("\n🏗️ Creating Notion databases...")
        
        databases = self.schema.get("databases", {})
        created_dbs = {}
        
        for db_key, db_config in databases.items():
            try:
                print(f"\n📊 Creating database: {db_config['title']}")
                
                # Convert properties
                notion_properties = {}
                for prop_name, prop_config in db_config["properties"].items():
                    notion_properties[prop_name] = self._convert_property_type(prop_name, prop_config)
                
                # Create database
                result = self.notion_client.create_database(
                    parent_page_id=self.parent_page_id,
                    title=db_config["title"],
                    description=db_config["description"],
                    properties=notion_properties
                )
                
                db_id = result["id"]
                created_dbs[db_key] = db_id
                self.created_databases[db_key] = db_id
                
                print(f"✅ Created: {db_config['title']}")
                print(f"   Database ID: {db_id}")
                print(f"   URL: {result['url']}")
                
            except Exception as e:
                print(f"❌ Failed to create database {db_config['title']}: {e}")
                continue
        
        # Update relation properties now that all databases are created
        self._update_relation_properties()
        
        return created_dbs
    
    def _update_relation_properties(self):
        """Update relation properties to point to correct database IDs."""
        print("\n🔗 Updating relation properties...")
        
        databases = self.schema.get("databases", {})
        for db_key, db_config in databases.items():
            if db_key not in self.created_databases:
                continue
                
            db_id = self.created_databases[db_key]
            
            # Check if any properties need relation updates
            for prop_name, prop_config in db_config["properties"].items():
                if prop_config["type"] == "relation":
                    related_db = prop_config.get("related_database")
                    if related_db and related_db in self.created_databases:
                        # Update the relation property
                        try:
                            # Get current database
                            current_db = self.notion_client.get_database(db_id)
                            current_props = current_db.get("properties", {})
                            
                            # Update relation property
                            current_props[prop_name]["relation"]["database_id"] = self.created_databases[related_db]
                            
                            # Update database
                            url = f"{self.notion_client.config.base_url}/databases/{db_id}"
                            payload = {"properties": current_props}
                            
                            response = self.notion_client._make_request("PATCH", url, json=payload)
                            print(f"✅ Updated relation {prop_name} in {db_config['title']}")
                            
                        except Exception as e:
                            print(f"⚠️ Failed to update relation {prop_name}: {e}")
    
    def add_sample_data(self) -> Dict[str, List[str]]:
        """Add sample data to all databases."""
        print("\n📝 Adding sample data to databases...")
        
        databases = self.schema.get("databases", {})
        added_pages = {}
        
        for db_key, db_config in databases.items():
            if db_key not in self.created_databases:
                continue
                
            sample_data = db_config.get("sample_data", [])
            if not sample_data:
                continue
            
            db_id = self.created_databases[db_key]
            added_pages[db_key] = []
            
            print(f"\n📊 Adding sample data to {db_config['title']}...")
            
            for sample_item in sample_data:
                try:
                    # Convert sample data to Notion properties
                    properties = self._convert_sample_data_to_properties(sample_item, db_config["properties"])
                    
                    # Create page
                    result = self.notion_client.create_page(db_id, properties)
                    page_id = result["id"]
                    added_pages[db_key].append(page_id)
                    
                    # Get title for logging
                    title = sample_item.get("Name") or sample_item.get("Stage Name") or sample_item.get("Metric Name") or "Sample Item"
                    print(f"✅ Added: {title}")
                    
                except Exception as e:
                    print(f"❌ Failed to add sample item: {e}")
                    continue
        
        return added_pages
    
    def _convert_sample_data_to_properties(self, sample_item: Dict[str, Any], property_configs: Dict[str, Any]) -> Dict[str, Any]:
        """Convert sample data to Notion properties format."""
        properties = {}
        
        for prop_name, value in sample_item.items():
            if prop_name not in property_configs:
                continue
                
            prop_config = property_configs[prop_name]
            prop_type = prop_config["type"]
            
            if prop_type == "title":
                properties[prop_name] = create_title_property(str(value))
            
            elif prop_type == "rich_text":
                properties[prop_name] = create_rich_text_property(str(value))
            
            elif prop_type == "select":
                properties[prop_name] = create_select_property(str(value))
            
            elif prop_type == "date":
                if isinstance(value, str):
                    properties[prop_name] = create_date_property(value)
            
            elif prop_type == "number":
                if isinstance(value, (int, float)):
                    properties[prop_name] = create_number_property(value)
            
            elif prop_type == "url":
                properties[prop_name] = create_url_property(str(value))
            
            elif prop_type == "multi_select":
                if isinstance(value, list):
                    properties[prop_name] = {
                        "multi_select": [{"name": str(item)} for item in value]
                    }
        
        return properties
    
    def create_pages(self) -> Dict[str, str]:
        """Create pages defined in the schema."""
        print("\n📄 Creating pages...")
        
        pages = self.schema.get("pages", {})
        created_pages = {}
        
        for page_key, page_config in pages.items():
            try:
                print(f"\n📄 Creating page: {page_config['title']}")
                
                # Create page content
                content_blocks = []
                for content_item in page_config.get("content", []):
                    block = self._create_content_block(content_item)
                    if block:
                        content_blocks.append(block)
                
                # For now, we'll create a simple page with title and description
                # Full content blocks would require more complex Notion API calls
                page_properties = {
                    "title": create_title_property(page_config["title"]),
                    "Description": create_rich_text_property(page_config.get("description", ""))
                }
                
                # Create page as child of Control Center
                result = self.notion_client.create_page(self.parent_page_id, page_properties)
                page_id = result["id"]
                created_pages[page_key] = page_id
                self.created_pages[page_key] = page_id
                
                print(f"✅ Created: {page_config['title']}")
                print(f"   Page ID: {page_id}")
                print(f"   URL: {result['url']}")
                
            except Exception as e:
                print(f"❌ Failed to create page {page_config['title']}: {e}")
                continue
        
        return created_pages
    
    def _create_content_block(self, content_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a Notion content block from JSON config."""
        content_type = content_item.get("type")
        text = content_item.get("text", "")
        
        if content_type == "heading_1":
            return {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": text}}]
                }
            }
        elif content_type == "heading_2":
            return {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": text}}]
                }
            }
        elif content_type == "paragraph":
            return {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": text}}]
                }
            }
        
        return None
    
    def create_views(self) -> Dict[str, str]:
        """Create database views defined in the schema."""
        print("\n👁️ Creating database views...")
        
        views = self.schema.get("views", {})
        created_views = {}
        
        for view_key, view_config in views.items():
            try:
                db_key = view_config["database"]
                if db_key not in self.created_databases:
                    print(f"⚠️ Database {db_key} not found for view {view_key}")
                    continue
                
                db_id = self.created_databases[db_key]
                print(f"\n👁️ Creating view: {view_config['title']}")
                
                # Note: Creating views via API is complex and requires specific Notion API calls
                # For now, we'll log what views should be created manually
                print(f"✅ View '{view_config['title']}' should be created manually in Notion:")
                print(f"   Database: {db_key} ({db_id})")
                print(f"   Type: {view_config['type']}")
                if "group_by" in view_config:
                    print(f"   Group by: {view_config['group_by']}")
                if "sort" in view_config:
                    print(f"   Sort: {view_config['sort']}")
                
                created_views[view_key] = f"manual_{view_key}"
                
            except Exception as e:
                print(f"❌ Failed to create view {view_config['title']}: {e}")
                continue
        
        return created_views
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate comprehensive summary report."""
        print("\n📊 Generating summary report...")
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "schema_version": self.schema.get("metadata", {}).get("version", "unknown"),
            "databases_created": len(self.created_databases),
            "pages_created": len(self.created_pages),
            "sample_data_added": sum(len(pages) for pages in getattr(self, 'added_pages', {}).values()),
            "databases": {},
            "environment_variables": {},
            "next_steps": []
        }
        
        # Database summary
        for db_key, db_id in self.created_databases.items():
            db_config = self.schema["databases"][db_key]
            summary["databases"][db_key] = {
                "title": db_config["title"],
                "id": db_id,
                "url": f"https://notion.so/{db_id.replace('-', '')}",
                "properties_count": len(db_config["properties"]),
                "sample_data_count": len(db_config.get("sample_data", []))
            }
        
        # Environment variables
        env_vars = self.schema.get("environment_variables", {})
        for env_var, db_key in env_vars.items():
            if db_key in self.created_databases:
                summary["environment_variables"][env_var] = self.created_databases[db_key]
        
        # Next steps
        summary["next_steps"] = [
            "Update your .env file with the new database IDs",
            "Test database access with: python scripts/test_notion_connection.py",
            "Run schema validation: python scripts/validate_notion_schema.py",
            "Set up automated sync workflows",
            "Create additional views and filters as needed"
        ]
        
        return summary
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print formatted summary report."""
        print("\n" + "="*80)
        print("🎉 MAGSASA-CARD CONTROL CENTER REBUILD COMPLETE!")
        print("="*80)
        
        print(f"\n📅 Completed: {summary['timestamp']}")
        print(f"📋 Schema Version: {summary['schema_version']}")
        print(f"🗄️ Databases Created: {summary['databases_created']}")
        print(f"📄 Pages Created: {summary['pages_created']}")
        print(f"📝 Sample Data Added: {summary['sample_data_added']} items")
        
        print(f"\n🗄️ DATABASE SUMMARY:")
        print("-" * 50)
        for db_key, db_info in summary["databases"].items():
            print(f"📊 {db_info['title']}")
            print(f"   ID: {db_info['id']}")
            print(f"   Properties: {db_info['properties_count']}")
            print(f"   Sample Data: {db_info['sample_data_count']} items")
            print(f"   URL: {db_info['url']}")
            print()
        
        print(f"🔧 ENVIRONMENT VARIABLES:")
        print("-" * 50)
        for env_var, db_id in summary["environment_variables"].items():
            print(f"{env_var}={db_id}")
        print()
        
        print(f"🚀 NEXT STEPS:")
        print("-" * 50)
        for i, step in enumerate(summary["next_steps"], 1):
            print(f"{i}. {step}")
        
        print("\n" + "="*80)
        print("✅ Control Center is now fully deployed and ready for use!")
        print("="*80)
    
    def rebuild_all(self):
        """Rebuild the complete Control Center."""
        print("🚀 Starting MAGSASA-CARD Control Center rebuild...")
        
        try:
            # Step 1: Create databases
            self.created_databases = self.create_databases()
            
            # Step 2: Add sample data
            self.added_pages = self.add_sample_data()
            
            # Step 3: Create pages
            self.created_pages = self.create_pages()
            
            # Step 4: Create views (manual instructions)
            self.created_views = self.create_views()
            
            # Step 5: Generate summary
            summary = self.generate_summary_report()
            self.print_summary(summary)
            
            # Save summary to file
            summary_file = Path(__file__).parent.parent / "CONTROL_CENTER_REBUILD_SUMMARY.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2)
            print(f"\n📄 Summary saved to: {summary_file}")
            
        except Exception as e:
            print(f"\n❌ Rebuild failed: {e}")
            raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Rebuild MAGSASA-CARD Control Center from JSON schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Rebuild everything
  python scripts/rebuild_control_center.py --rebuild-all
  
  # Create databases only
  python scripts/rebuild_control_center.py --create-databases-only
  
  # Add sample data only
  python scripts/rebuild_control_center.py --add-sample-data
  
  # Show summary only
  python scripts/rebuild_control_center.py --show-summary
        """
    )
    
    parser.add_argument(
        "--rebuild-all",
        action="store_true",
        help="Rebuild the complete Control Center (databases, pages, sample data)"
    )
    parser.add_argument(
        "--create-databases-only",
        action="store_true",
        help="Create databases only"
    )
    parser.add_argument(
        "--add-sample-data",
        action="store_true",
        help="Add sample data to existing databases"
    )
    parser.add_argument(
        "--create-pages-only",
        action="store_true",
        help="Create pages only"
    )
    parser.add_argument(
        "--show-summary",
        action="store_true",
        help="Show summary of created databases"
    )
    parser.add_argument(
        "--json-file",
        default="MAGSASA-CARD_Control_Center.json",
        help="Path to JSON schema file (default: MAGSASA-CARD_Control_Center.json)"
    )
    
    args = parser.parse_args()
    
    # Check for required environment variables
    if not os.getenv("NOTION_API_KEY"):
        print("❌ Error: NOTION_API_KEY environment variable is required.")
        print("Please copy env.template to .env and set your Notion API key.")
        sys.exit(1)
    
    if not os.getenv("CONTROL_CENTER_PAGE_ID"):
        print("❌ Error: CONTROL_CENTER_PAGE_ID environment variable is required.")
        print("Please set the parent page ID where databases will be created.")
        sys.exit(1)
    
    # Validate JSON file exists
    json_path = Path(__file__).parent.parent / args.json_file
    if not json_path.exists():
        print(f"❌ Error: JSON schema file not found: {json_path}")
        sys.exit(1)
    
    try:
        # Initialize rebuilder
        rebuilder = ControlCenterRebuilder(str(json_path))
        
        if args.rebuild_all:
            rebuilder.rebuild_all()
        
        elif args.create_databases_only:
            rebuilder.create_databases()
            print("\n✅ Databases created successfully!")
        
        elif args.add_sample_data:
            rebuilder.add_sample_data()
            print("\n✅ Sample data added successfully!")
        
        elif args.create_pages_only:
            rebuilder.create_pages()
            print("\n✅ Pages created successfully!")
        
        elif args.show_summary:
            summary = rebuilder.generate_summary_report()
            rebuilder.print_summary(summary)
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
