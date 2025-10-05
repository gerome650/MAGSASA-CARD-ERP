# 🔗 AI Studio Notion Integration

This document describes the standardized Notion API integration for all AI Studio projects (MAGSASA-CARD, KWENTO+, AI Studio Milestones, etc.) using a single master API key and environment-based configuration.

## 🎯 Overview

The Notion integration provides:
- **Centralized API client** with comprehensive error handling
- **Environment-based configuration** for easy deployment across projects
- **Safety checks** for missing keys and database IDs
- **Property helpers** for consistent Notion data formatting
- **Backward compatibility** with existing scripts

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Copy the environment template
cp env.template .env

# Edit .env with your Notion API key and database IDs
# The NOTION_API_KEY will be renamed to "AI Studio Master Automation" in Notion
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Test Connection

```bash
# Test basic connectivity
python scripts/test_notion_connection.py

# Test with write operations (creates test pages)
python scripts/test_notion_connection.py --test-write
```

### 4. Setup Databases

```bash
# Create databases automatically
python scripts/setup_notion_databases.py --create-databases

# Or show schema for manual setup
python scripts/setup_notion_databases.py --show-schema
```

## 📊 Environment Configuration

### Required Variables

```bash
# Master Notion API Key (shared across all AI Studio projects)
NOTION_API_KEY=your_notion_api_key_here

# Notion Parent Page ID (where databases will be created)
NOTION_PARENT_PAGE_ID=your_parent_page_id
```

### Database IDs (Project-Specific)

```bash
# MAGSASA-CARD Project
MAGSASA_CI_DB_ID=database_id_for_ci_reports
MAGSASA_ROADMAP_DB_ID=database_id_for_roadmap

# KWENTO+ Project
KWENTO_ROADMAP_DB_ID=database_id_for_kwento_roadmap

# AI Studio Milestones
AI_STUDIO_MILESTONES_DB_ID=database_id_for_milestones
```

### GitHub Integration (Optional)

```bash
# For two-way sync with GitHub
GITHUB_TOKEN=your_github_token
GITHUB_REPOSITORY=owner/repo-name
```

### Legacy Compatibility

```bash
# Legacy variable names (automatically used as fallback)
NOTION_CI_REPORTS_DB_ID=legacy_ci_database_id
NOTION_ROADMAP_DB_ID=legacy_roadmap_database_id
```

## 🛠️ Usage Examples

### Basic Operations

```python
from utils.notion_client import NotionClient, add_page, query_database

# Initialize client
client = NotionClient()

# Create a page
page_id = add_page("database_id", {
    "Name": create_title_property("My Page"),
    "Status": create_select_property("Active"),
    "Content": create_rich_text_property("Page content here")
})

# Query database
results = query_database("database_id", {
    "filter": {
        "property": "Status",
        "select": {"equals": "Active"}
    }
})
```

### Using Property Helpers

```python
from utils.notion_client import (
    create_title_property,
    create_rich_text_property,
    create_select_property,
    create_date_property,
    create_number_property,
    create_url_property
)

properties = {
    "Title": create_title_property("My Title"),
    "Description": create_rich_text_property("Rich text content"),
    "Status": create_select_property("In Progress"),
    "Due Date": create_date_property("2024-01-15"),
    "Priority": create_number_property(5),
    "Link": create_url_property("https://example.com")
}
```

### Database ID Management

```python
from utils.notion_client import get_safe_database_id, validate_database_access

# Get database ID with validation
db_id = get_safe_database_id("MAGSASA", "CI")

# Validate database access
if validate_database_access(db_id, "MAGSASA CI"):
    print("Database is accessible")
```

## 📋 Available Scripts

### 1. Connection Test

```bash
# Basic connectivity test
python scripts/test_notion_connection.py

# Test with write operations
python scripts/test_notion_connection.py --test-write

# Show configuration status only
python scripts/test_notion_connection.py --config-only
```

### 2. Database Setup

```bash
# Create databases automatically
python scripts/setup_notion_databases.py --create-databases

# Show schema for manual setup
python scripts/setup_notion_databases.py --show-schema
```

### 3. CI Report Sync

```bash
# Sync CI report to Notion
python scripts/sync_ci_report_to_notion.py --sync-notion --report reports/CI_WEEKLY_INTELLIGENCE.md

# Include roadmap milestone updates
python scripts/sync_ci_report_to_notion.py --sync-notion --include-roadmap --milestone "Stage 7.3"

# Show roadmap status
python scripts/sync_ci_report_to_notion.py --roadmap-status
```

### 4. Two-Way GitHub Sync

```bash
# Sync changes from Notion to GitHub
python scripts/notion_two_way_sync.py --sync-from-notion

# Sync changes from GitHub to Notion
python scripts/notion_two_way_sync.py --sync-to-notion

# Full bidirectional sync
python scripts/notion_two_way_sync.py --full-sync

# Dry run to see what would change
python scripts/notion_two_way_sync.py --full-sync --dry-run
```

## 🏗️ Architecture

### Centralized Client

The `utils/notion_client.py` module provides:

- **NotionClient**: Main client class with comprehensive error handling
- **Property Helpers**: Functions to create properly formatted Notion properties
- **Extract Helpers**: Functions to extract values from Notion properties
- **Database ID Management**: Safe retrieval and validation of database IDs
- **Global Client Instance**: Convenience functions for common operations

### Safety Features

- **API Key Validation**: Checks for valid API key on initialization
- **Database ID Validation**: Validates database access before operations
- **Error Handling**: Comprehensive error messages with actionable guidance
- **Fallback Support**: Automatic fallback to legacy environment variables

### Environment-Based Configuration

- **Single API Key**: One master key for all AI Studio projects
- **Project-Specific Databases**: Separate database IDs for each project
- **Legacy Compatibility**: Automatic fallback to old variable names
- **Optional GitHub Integration**: For two-way sync capabilities

## 🔧 Customization

### Adding New Projects

To add support for a new project:

1. **Add environment variables** to `env.template`:
   ```bash
   NEW_PROJECT_CI_DB_ID=
   NEW_PROJECT_ROADMAP_DB_ID=
   ```

2. **Update scripts** to use the new database IDs:
   ```python
   db_id = get_safe_database_id("NEW_PROJECT", "CI")
   ```

3. **Test the integration**:
   ```bash
   python scripts/test_notion_connection.py --test-write
   ```

### Custom Property Types

Add new property helpers to `utils/notion_client.py`:

```python
def create_checkbox_property(checked: bool) -> Dict[str, Any]:
    """Create a Notion checkbox property."""
    return {"checkbox": checked}

def create_relation_property(related_ids: List[str]) -> Dict[str, Any]:
    """Create a Notion relation property."""
    return {
        "relation": [{"id": page_id} for page_id in related_ids]
    }
```

## 🐛 Troubleshooting

### Common Issues

1. **API Key Not Set**
   ```
   ❌ NOTION_API_KEY is not set. Please update your .env file.
   ```
   **Solution**: Copy `env.template` to `.env` and set your API key.

2. **Database ID Not Found**
   ```
   ❌ Database ID is required for operation. Please set the appropriate *_DB_ID environment variable.
   ```
   **Solution**: Set the correct database ID in your `.env` file.

3. **Database Access Denied**
   ```
   ❌ Database access failed: Notion API error: Unauthorized
   ```
   **Solution**: Ensure your API key has access to the database and the database ID is correct.

4. **Property Format Error**
   ```
   ❌ Notion API error: Invalid property format
   ```
   **Solution**: Use the provided property helper functions instead of manually formatting properties.

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Connection Test

Always run the connection test when setting up:

```bash
python scripts/test_notion_connection.py --test-write
```

## 📚 API Reference

### NotionClient Class

```python
class NotionClient:
    def __init__(self, api_key: Optional[str] = None)
    def create_page(self, database_id: str, properties: Dict[str, Any]) -> Dict[str, Any]
    def update_page(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]
    def query_database(self, database_id: str, filter_params: Optional[Dict] = None) -> List[Dict[str, Any]]
    def get_database(self, database_id: str) -> Dict[str, Any]
    def get_page(self, page_id: str) -> Dict[str, Any]
    def create_database(self, parent_page_id: str, title: str, description: str, properties: Dict[str, Any]) -> Dict[str, Any]
    def search(self, query: str = "", filter_params: Optional[Dict] = None) -> List[Dict[str, Any]]
```

### Convenience Functions

```python
def get_client() -> NotionClient
def add_page(database_id: str, properties: Dict[str, Any]) -> str
def query_database(database_id: str, filter_params: Optional[Dict] = None) -> List[Dict[str, Any]]
def update_page(page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]
def get_database_id(project: str, database_type: str) -> Optional[str]
def validate_database_access(database_id: str, project: str = "Unknown") -> bool
def get_safe_database_id(project: str, database_type: str) -> Optional[str]
```

### Property Helpers

```python
def create_title_property(text: str) -> Dict[str, Any]
def create_rich_text_property(text: str) -> Dict[str, Any]
def create_select_property(option: str) -> Dict[str, Any]
def create_date_property(date_string: str) -> Dict[str, Any]
def create_number_property(number: Union[int, float]) -> Dict[str, Any]
def create_url_property(url: str) -> Dict[str, Any]
```

### Extract Helpers

```python
def extract_title_value(property_data: Dict[str, Any]) -> str
def extract_select_value(property_data: Dict[str, Any]) -> str
def extract_rich_text_value(property_data: Dict[str, Any]) -> str
def extract_date_value(property_data: Dict[str, Any]) -> str
def extract_number_value(property_data: Dict[str, Any]) -> Union[int, float, None]
def extract_url_value(property_data: Dict[str, Any]) -> str
```

## 🎉 Success!

Your AI Studio Notion integration is now ready! All projects can use the same master API key with project-specific database configurations, making it easy to deploy and maintain across your entire AI Studio ecosystem.

For questions or issues, please refer to the troubleshooting section or run the connection test script.

