#!/usr/bin/env python3
"""
Stage 7.3.1 - Interactive Notion API Key Setup

This script helps users configure their Notion API key correctly.
It provides step-by-step guidance and validates the key before saving.

Usage:
    python scripts/setup_notion_api_key.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def print_banner(_):
    """Print welcome banner."""
    print("=" * 80)
    print("🔑 Notion API Key Setup Wizard")
    print("=" * 80)
    print()
    print("This wizard will help you configure your Notion API key.")
    print()


def print_instructions(_):
    """Print instructions for getting an API key."""
    print("📝 How to Get Your Notion API Key:")
    print("-" * 80)
    print()
    print("1. Open your browser and go to:")
    print("   👉 https://www.notion.so/my-integrations")
    print()
    print("2. Find or create your integration:")
    print("   • Look for 'AI Studio Master Automation'")
    print("   • If it doesn't exist, click '+ New integration'")
    print()
    print("3. Configure the integration:")
    print("   • Name: AI Studio Master Automation")
    print("   • Type: Internal Integration")
    print("   • Capabilities: Read, Update, Insert content")
    print()
    print("4. Get your API key:")
    print("   • Click on your integration")
    print("   • Find the 'Secrets' section")
    print("   • Click 'Show' to reveal the secret")
    print("   • Copy the ENTIRE key (starts with 'secret_ntn_')")
    print()
    print("5. IMPORTANT - Share databases with integration:")
    print("   • Open each database in Notion:")
    print("     - CI Intelligence Reports")
    print("     - MAGSASA-CARD ERP Roadmap")
    print("     - AI Studio Strategic Milestones")
    print("   • Click '...' → 'Add connections'")
    print("   • Select 'AI Studio Master Automation'")
    print()
    print("-" * 80)
    print()


def validate_api_key(api_key: str) -> tuple[bool, str]:
    """
    Validate the API key format and connectivity.

    Args:
        api_key: The API key to validate

    Returns:
        Tuple of (is_valid, message)
    """
    # Basic format validation
    if not api_key:
        return False, "API key cannot be empty"

    if not api_key.startswith("secret_"):
        return False, "API key should start with 'secret_'"

    if len(api_key) < 50:
        return False, "API key seems too short - make sure you copied the complete key"

    # Test connectivity
    print("\n🔍 Testing API key with Notion...")
    try:
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

        response = requests.post(
            "https://api.notion.com/v1/search", headers=headers, json={"page_size": 1}
        )

        if response.status_code == 401:
            error_data = response.json()
            error_msg = error_data.get("message", "Unauthorized")
            return False, f"API key is invalid: {error_msg}"

        elif response.status_code == 403:
            return False, "API key lacks necessary permissions"

        elif response.status_code != 200:
            return False, f"API returned unexpected status: {response.status_code}"

        # Check if any databases are accessible
        data = response.json()
        results = data.get("results", [])

        if len(results) == 0:
            return (
                True,
                "⚠️  API key is valid, but no databases are accessible yet. Remember to share databases with your integration!",
            )

        return True, f"✅ API key is valid! Found {len(results)} accessible resource(s)"

    except requests.exceptions.RequestException as e:
        return False, f"Network error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def update_env_file(api_key: str) -> bool:
    """
    Update the .env file with the new API key.

    Args:
        api_key: The validated API key

    Returns:
        True if successful, False otherwise
    """
    env_file = Path(__file__).parent.parent / ".env"

    try:
        # Read existing .env file
        if env_file.exists():
            with open(env_file) as f:
                lines = f.readlines()
        else:
            # If .env doesn't exist, copy from template
            template_file = Path(__file__).parent.parent / "env.template"
            if template_file.exists():
                with open(template_file) as f:
                    lines = f.readlines()
            else:
                lines = []

        # Update or add NOTION_API_KEY
        updated = False
        for _i, line in enumerate(lines):
            if line.startswith("NOTION_API_KEY="):
                lines[i] = f"NOTION_API_KEY={api_key}\n"
                updated = True
                break

        if not updated:
            lines.append(f"\nNOTION_API_KEY={api_key}\n")

        # Write back to .env
        with open(env_file, "w") as f:
            f.writelines(lines)

        print(f"\n✅ Updated {env_file}")
        return True

    except Exception as e:
        print(f"\n❌ Failed to update .env file: {e}")
        return False


def main(_):
    """Main entry point."""
    print_banner()

    # Check if requests is available
    try:
        import requests  # noqa: F401
    except ImportError:
        print("❌ Error: 'requests' module not found")
        print("Please install it: pip install requests")
        return 1

    print_instructions()

    # Get API key from user
    print("Please paste your Notion API key below:")
    print("(The key will be hidden as you type for security)")
    print()

    try:
        # Try to use getpass for hidden input
        import getpass

        api_key = getpass.getpass("API Key: ").strip()
    except Exception:
        # Fallback to regular input if getpass doesn't work
        api_key = input("API Key: ").strip()

    if not api_key:
        print("\n❌ No API key provided. Exiting.")
        return 1

    # Validate the API key
    is_valid, message = validate_api_key(api_key)
    print(f"\n{message}")

    if not is_valid:
        print("\n❌ API key validation failed. Please try again.")
        print("\nTips:")
        print("  • Make sure you copied the COMPLETE key")
        print("  • The key should start with 'secret_'")
        print("  • Check that the integration is active in Notion")
        print("  • Verify you have the right integration selected")
        return 1

    # Ask for confirmation
    print("\n" + "=" * 80)
    print("📝 Summary:")
    print("-" * 80)
    print(f"API Key: {api_key[:20]}...{api_key[-10:]}")
    print("Status: ✅ Valid")
    print("=" * 80)
    print()

    confirm = input("Save this API key to .env file? (y/n): ").strip().lower()

    if confirm != "y":
        print("\n⚠️  API key not saved. Exiting.")
        return 0

    # Update .env file
    if update_env_file(api_key):
        print("\n" + "=" * 80)
        print("🎉 SUCCESS!")
        print("=" * 80)
        print()
        print("Your Notion API key has been configured successfully!")
        print()
        print("📋 Next Steps:")
        print()
        print("1. Share databases with your integration:")
        print("   • Open each database in Notion")
        print("   • Click '...' → 'Add connections'")
        print("   • Select 'AI Studio Master Automation'")
        print()
        print("2. Run the access audit:")
        print("   python scripts/audit_notion_access.py --json")
        print()
        print("3. If audit passes, run sanity check:")
        print("   python scripts/notion_cli.py sanity-check")
        print()
        print("4. Test sync with dry-run:")
        print("   python scripts/notion_cli.py sync --all --dry-run")
        print()
        print("=" * 80)

        # Offer to run audit automatically
        run_audit = input("\nRun access audit now? (y/n): ").strip().lower()

        if run_audit == "y":
            print("\n🚀 Running access audit...\n")
            try:
                # Import and run audit
                sys.path.insert(0, str(Path(__file__).parent))
                from audit_notion_access import main as audit_main

                return audit_main()
            except Exception as e:
                print(f"⚠️  Could not run audit automatically: {e}")
                print("Please run manually: python scripts/audit_notion_access.py")
                return 0

        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
