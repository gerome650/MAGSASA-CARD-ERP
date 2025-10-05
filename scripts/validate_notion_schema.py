#!/usr/bin/env python3
"""
Notion Database Schema Validator

Validates that required Notion database properties exist and match expected types.
Fails CI if schema drift is detected.

Features:
- Property existence checks
- Property type validation
- Actionable diff output
- CI-friendly exit codes
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Set, Optional
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.notion_client import NotionClient


@dataclass
class PropertySchema:
    """Expected property schema definition."""
    name: str
    type: str
    required: bool = True


# Expected database schemas
EXPECTED_SCHEMAS = {
    "MAGSASA_CI_DB_ID": {
        "name": "CI Reports Database",
        "properties": [
            PropertySchema("Name", "title", required=True),
            PropertySchema("Week Of", "date", required=True),
            PropertySchema("Workflows Pass Rate", "number", required=True),
            PropertySchema("Auto-Fix Success Rate", "number", required=True),
            PropertySchema("Avg MTTR (minutes)", "number", required=True),
            PropertySchema("Total Runs", "number", required=False),
            PropertySchema("Failed Runs", "number", required=False),
            PropertySchema("Top Failures", "rich_text", required=True),
            PropertySchema("Recommendations", "rich_text", required=True),
            PropertySchema("Status", "select", required=True),
            PropertySchema("Type", "select", required=True),
        ]
    },
    "MAGSASA_ROADMAP_DB_ID": {
        "name": "Roadmap Database",
        "properties": [
            PropertySchema("Name", "title", required=True),
            PropertySchema("Stage Name", "rich_text", required=False),
            PropertySchema("Status", "select", required=True),
            PropertySchema("Target Date", "date", required=True),
            PropertySchema("Progress", "number", required=True),
            PropertySchema("Next Action", "rich_text", required=True),
            PropertySchema("Risk Level", "select", required=True),
            PropertySchema("Drift (days)", "number", required=False),
        ]
    },
    "AI_STUDIO_MILESTONES_DB_ID": {
        "name": "AI Studio Milestones Database",
        "properties": [
            PropertySchema("Stage Name", "title", required=True),
            PropertySchema("Target Date", "date", required=True),
            PropertySchema("Status", "select", required=True),
            PropertySchema("Description", "rich_text", required=False),
            PropertySchema("Progress", "number", required=False),
        ]
    }
}


class SchemaValidator:
    """Validates Notion database schemas against expected definitions."""
    
    def __init__(self):
        """Initialize the validator."""
        self.notion_client = NotionClient()
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_database(self, env_var: str, expected_schema: Dict[str, Any]) -> bool:
        """
        Validate a single database schema.
        
        Args:
            env_var: Environment variable name for database ID
            expected_schema: Expected schema definition
        
        Returns:
            True if valid, False if errors found
        """
        database_id = os.getenv(env_var)
        db_name = expected_schema["name"]
        
        print(f"\n🔍 Validating {db_name}...")
        
        if not database_id:
            self.errors.append(f"❌ {env_var} not set in environment")
            print(f"  ❌ Environment variable {env_var} not set")
            return False
        
        try:
            # Get database metadata
            database = self.notion_client.get_database(database_id)
            actual_properties = database.get("properties", {})
            
            # Check each expected property
            expected_props = expected_schema["properties"]
            missing_props = []
            type_mismatches = []
            
            for prop_schema in expected_props:
                prop_name = prop_schema.name
                expected_type = prop_schema.type
                required = prop_schema.required
                
                if prop_name not in actual_properties:
                    if required:
                        missing_props.append(prop_name)
                        print(f"  ❌ Missing required property: '{prop_name}' (type: {expected_type})")
                    else:
                        self.warnings.append(f"⚠️ {db_name}: Missing optional property '{prop_name}'")
                        print(f"  ⚠️ Missing optional property: '{prop_name}'")
                else:
                    actual_type = actual_properties[prop_name].get("type")
                    if actual_type != expected_type:
                        type_mismatches.append((prop_name, expected_type, actual_type))
                        print(f"  ❌ Type mismatch for '{prop_name}': expected {expected_type}, got {actual_type}")
                    else:
                        print(f"  ✅ '{prop_name}' ({expected_type})")
            
            # Report summary for this database
            if missing_props or type_mismatches:
                self.errors.append(f"❌ {db_name}: Schema validation failed")
                
                if missing_props:
                    self.errors.append(f"   Missing properties: {', '.join(missing_props)}")
                
                if type_mismatches:
                    for prop, expected, actual in type_mismatches:
                        self.errors.append(f"   Type mismatch: {prop} (expected {expected}, got {actual})")
                
                print(f"\n  ❌ Validation failed for {db_name}")
                return False
            else:
                print(f"  ✅ All required properties present and correct")
                return True
        
        except Exception as e:
            self.errors.append(f"❌ {db_name}: Failed to retrieve database - {e}")
            print(f"  ❌ Error: {e}")
            return False
    
    def print_remediation_guide(self):
        """Print actionable remediation steps."""
        if not self.errors:
            return
        
        print("\n" + "="*70)
        print("📋 REMEDIATION GUIDE")
        print("="*70)
        print("\nSchema drift detected. To fix:")
        print("\n1. Go to your Notion workspace")
        print("2. Navigate to the affected database(s)")
        print("3. Add/update the missing/mismatched properties:")
        print()
        
        for error in self.errors:
            print(f"   {error}")
        
        print("\n4. Property type mapping:")
        print("   - title: Title property (one per database)")
        print("   - rich_text: Text property")
        print("   - number: Number property")
        print("   - date: Date property")
        print("   - select: Select property")
        print("   - multi_select: Multi-select property")
        print()
        print("5. After fixing, re-run: python scripts/validate_notion_schema.py")
        print("="*70)
    
    def validate_all(self) -> bool:
        """
        Validate all configured databases.
        
        Returns:
            True if all valid, False if any errors
        """
        print("🔍 Validating Notion Database Schemas")
        print("="*70)
        
        all_valid = True
        
        for env_var, schema in EXPECTED_SCHEMAS.items():
            valid = self.validate_database(env_var, schema)
            all_valid = all_valid and valid
        
        print("\n" + "="*70)
        
        if all_valid:
            print("✅ All database schemas validated successfully!")
            if self.warnings:
                print(f"\n⚠️ {len(self.warnings)} warning(s):")
                for warning in self.warnings:
                    print(f"   {warning}")
            return True
        else:
            print(f"❌ Schema validation failed with {len(self.errors)} error(s)")
            self.print_remediation_guide()
            return False


def main():
    """Main entry point."""
    try:
        validator = SchemaValidator()
        is_valid = validator.validate_all()
        
        # Exit with appropriate code
        sys.exit(0 if is_valid else 1)
    
    except Exception as e:
        print(f"\n❌ Fatal error during validation: {e}")
        print("\nPossible causes:")
        print("  - NOTION_API_KEY not set or invalid")
        print("  - Network connectivity issues")
        print("  - Notion API rate limiting")
        print("\nTroubleshooting:")
        print("  1. Check your .env file or environment variables")
        print("  2. Test connection: python scripts/test_notion_connection.py")
        print("  3. Verify API key has database access permissions")
        sys.exit(1)


if __name__ == "__main__":
    main()


