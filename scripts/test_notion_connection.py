#!/usr/bin/env python3
"""
Test Notion Connection and Database Access

Quick test script to verify:
- Notion API key is valid
- Required databases are accessible
- Schema validation passes

Usage:
    python scripts/test_notion_connection.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.notion_client import NotionClient


def test_api_key():
    """Test if API key is valid and can authenticate."""
    print("🔑 Testing Notion API key...")
    try:
        client = NotionClient()
        print(f"   ✅ API key loaded: {client.api_key[:20]}...")
        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False


def test_database_access(client: NotionClient, db_name: str, env_var: str):
    """Test access to a specific database."""
    print(f"\n📊 Testing {db_name}...")
    
    db_id = os.getenv(env_var)
    if not db_id:
        print(f"   ⚠️ {env_var} not set in environment")
        return False
    
    try:
        database = client.get_database(db_id)
        title = database.get("title", [{}])[0].get("plain_text", "Unknown")
        property_count = len(database.get("properties", {}))
        
        print(f"   ✅ Database accessible")
        print(f"      Title: {title}")
        print(f"      ID: {db_id[:8]}...")
        print(f"      Properties: {property_count}")
        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False


def test_search(client: NotionClient):
    """Test Notion search API."""
    print("\n🔍 Testing search API...")
    try:
        results = client.search(query="", filter_params={"value": "database", "property": "object"})
        print(f"   ✅ Search successful")
        print(f"      Found {len(results)} accessible databases")
        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False


def main():
    """Run all connection tests."""
    print("="*70)
    print("🧪 Testing Notion Connection")
    print("="*70)
    
    # Test 1: API Key
    if not test_api_key():
        print("\n❌ Cannot proceed without valid API key")
        print("\nTroubleshooting:")
        print("  1. Check your .env file exists")
        print("  2. Verify NOTION_API_KEY is set correctly")
        print("  3. API key should start with 'secret_'")
        sys.exit(1)
    
    # Initialize client for remaining tests
    client = NotionClient()
    
    # Test 2: Database Access
    databases = [
        ("CI Reports Database", "MAGSASA_CI_DB_ID"),
        ("Roadmap Database", "MAGSASA_ROADMAP_DB_ID"),
        ("AI Studio Milestones Database", "AI_STUDIO_MILESTONES_DB_ID"),
    ]
    
    db_results = []
    for db_name, env_var in databases:
        result = test_database_access(client, db_name, env_var)
        db_results.append(result)
    
    # Test 3: Search API
    search_ok = test_search(client)
    
    # Summary
    print("\n" + "="*70)
    print("📊 Test Summary")
    print("="*70)
    
    total_tests = 1 + len(databases) + 1  # API + DBs + Search
    passed_tests = sum([1] + db_results + [search_ok])
    
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("✅ All tests passed! Notion integration is ready.")
        print("\nNext steps:")
        print("  1. Validate schemas: python scripts/validate_notion_schema.py")
        print("  2. Dry-run sync: python scripts/notion_weekly_sync.py --all --dry-run")
        print("  3. Live sync: python scripts/notion_weekly_sync.py --all")
        sys.exit(0)
    else:
        print("⚠️ Some tests failed. See errors above.")
        print("\nCommon issues:")
        print("  - Database not shared with integration")
        print("  - Incorrect database IDs")
        print("  - API key lacks permissions")
        print("\nTroubleshooting:")
        print("  1. Share databases with your Notion integration")
        print("  2. Verify database IDs from Notion URLs")
        print("  3. Check integration permissions in Notion settings")
        sys.exit(1)


if __name__ == "__main__":
    main()
