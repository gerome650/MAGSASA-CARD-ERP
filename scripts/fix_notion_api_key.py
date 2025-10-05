#!/usr/bin/env python3
"""
Quick Notion API Key Fix Script
Fixes the 401 Unauthorized error by updating the API key
"""

import sys
from pathlib import Path

import requests


def validate_api_key(api_key):
    """Test API key against Notion's search endpoint."""
    print(f"🔍 Testing API key: {api_key[:20]}...{api_key[-10:]}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    try:
        response = requests.post(
            "https://api.notion.com/v1/search", headers=headers, json={"page_size": 1}
        )

        if response.status_code == 401:
            print("❌ 401 Unauthorized - API key is invalid")
            return False
        elif response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            print(f"✅ API key is valid! Found {len(results)} accessible resource(s)")
            return True
        else:
            print(f"⚠️ Unexpected status: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Network error: {e}")
        return False


def update_env_file(api_key):
    """Update .env file with new API key."""
    env_file = Path(__file__).parent.parent / ".env"

    try:
        # Read existing .env file
        with open(env_file) as f:
            lines = f.readlines()

        # Update NOTION_API_KEY
        updated = False
        for i, line in enumerate(lines):
            if line.startswith("NOTION_API_KEY="):
                lines[i] = f"NOTION_API_KEY={api_key}\n"
                updated = True
                break

        if not updated:
            lines.append(f"NOTION_API_KEY={api_key}\n")

        # Write back to .env
        with open(env_file, "w") as f:
            f.writelines(lines)

        print(f"✅ Updated {env_file}")
        return True

    except Exception as e:
        print(f"❌ Failed to update .env file: {e}")
        return False


def main():
    print("=" * 80)
    print("🔧 Notion API Key Quick Fix")
    print("=" * 80)
    print()
    print("This script will help you fix the 401 Unauthorized error.")
    print()
    print("📝 To get your API key:")
    print("1. Go to https://www.notion.so/my-integrations")
    print("2. Find or create 'AI Studio Master Automation' integration")
    print("3. Copy the secret key (starts with 'secret_')")
    print()

    # Get API key from command line argument or prompt
    if len(sys.argv) > 1:
        api_key = sys.argv[1].strip()
    else:
        print("Please provide your Notion API key:")
        print("Usage: python scripts/fix_notion_api_key.py YOUR_API_KEY")
        print("Or run: python scripts/fix_notion_api_key.py")
        api_key = input("API Key: ").strip()

    if not api_key:
        print("❌ No API key provided")
        return 1

    # Validate API key
    if not validate_api_key(api_key):
        print("\n❌ API key validation failed")
        print("Please check your API key and try again")
        return 1

    # Update .env file
    if update_env_file(api_key):
        print("\n🎉 SUCCESS! API key has been updated")
        print("\n📋 Next steps:")
        print("1. Make sure to share your databases with the integration")
        print("2. Run: python scripts/audit_notion_access.py")
        print("3. Run: python scripts/notion_cli.py sanity-check")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
