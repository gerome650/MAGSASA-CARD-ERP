#!/usr/bin/env python3
"""
Centralized Notion Client Utility for AI Studio Projects

This module provides a standardized interface for interacting with Notion databases
across all AI Studio projects (MAGSASA-CARD, KWENTO+, AI Studio Milestones, etc.).

Features:
- Single master API key configuration
- Environment-based database ID management
- Comprehensive error handling
- Support for all major Notion operations (create, read, update, query)
- Safety checks for missing keys and database IDs

Usage:
    from utils.notion_client import add_page, query_database, NotionClient

    # Simple operations
    page_id = add_page("database_id", {"Name": {"title": [{"text": {"content": "Test"}}]}})
    results = query_database("database_id", {"filter": {"property": "Status", "select": {"equals": "Active"}}})

    # Advanced operations
    client = NotionClient()
    client.update_page(page_id, {"Status": {"select": {"name": "Completed"}}})
"""

import logging
import os
import sys
from dataclasses import dataclass
from typing import Any

import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class NotionConfig:
    """Configuration for Notion API access."""

    api_key: str
    base_url: str = "https://api.notion.com/v1"
    version: str = "2022-06-28"

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.api_key:
            raise ValueError("❌ NOTION_API_KEY is required but not provided")


class NotionClient:
    """
    Centralized Notion API client with comprehensive error handling.

    This client provides a standardized interface for all Notion operations
    across AI Studio projects, with built-in safety checks and error handling.
    """

    def __init__(self, api_key: str | None = None):
        """
        Initialize Notion client.

        Args:
            api_key: Notion API key. If not provided, will attempt to load from environment.

        Raises:
            ValueError: If API key is not available from any source.
        """
        self.api_key = api_key or self._get_api_key()
        self.config = NotionConfig(api_key=self.api_key)
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": self.config.version,
        }

        logger.info("✅ Notion client initialized successfully")

    def _get_api_key(self) -> str:
        """
        Get API key from environment variables.

        Returns:
            str: The Notion API key

        Raises:
            ValueError: If API key is not found in environment
        """
        api_key = os.getenv("NOTION_API_KEY")
        if not api_key:
            raise ValueError(
                "❌ NOTION_API_KEY is not set. Please update your .env file or set the environment variable.\n"
                "You can copy env.template to .env and fill in your API key."
            )
        return api_key

    def _validate_database_id(
        self, database_id: str, operation: str = "operation"
    ) -> None:
        """
        Validate that a database ID is provided.

        Args:
            database_id: The database ID to validate
            operation: Description of the operation being performed

        Raises:
            ValueError: If database ID is not provided
        """
        if not database_id:
            raise ValueError(
                f"❌ Database ID is required for {operation}. Please set the appropriate *_DB_ID environment variable."
            )

    def _make_request(self, method: str, url: str, **kwargs) -> dict[str, Any]:
        """
        Make a request to the Notion API with error handling.

        Args:
            method: HTTP method (GET, POST, PATCH, etc.)
            url: Full URL for the request
            **kwargs: Additional arguments for the request

        Returns:
            Dict containing the API response

        Raises:
            requests.RequestException: For HTTP errors
            ValueError: For API-specific errors
        """
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg = error_detail.get("message", str(e))
                    logger.error(f"❌ Notion API error: {error_msg}")
                    raise ValueError(f"Notion API error: {error_msg}")
                except ValueError:
                    pass
            logger.error(f"❌ Request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            raise

    def create_page(
        self, database_id: str, properties: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Create a new page in a Notion database.

        Args:
            database_id: The ID of the database to create the page in
            properties: Dictionary of properties for the new page

        Returns:
            Dict containing the created page data

        Raises:
            ValueError: If database ID is invalid or API call fails
        """
        self._validate_database_id(database_id, "page creation")

        url = f"{self.config.base_url}/pages"
        payload = {"parent": {"database_id": database_id}, "properties": properties}

        logger.info(f"Creating page in database {database_id[:8]}...")
        result = self._make_request("POST", url, json=payload)
        logger.info(f"✅ Page created successfully: {result['id']}")
        return result

    def update_page(self, page_id: str, properties: dict[str, Any]) -> dict[str, Any]:
        """
        Update an existing Notion page.

        Args:
            page_id: The ID of the page to update
            properties: Dictionary of properties to update

        Returns:
            Dict containing the updated page data

        Raises:
            ValueError: If page ID is invalid or API call fails
        """
        if not page_id:
            raise ValueError("❌ Page ID is required for page updates")

        url = f"{self.config.base_url}/pages/{page_id}"
        payload = {"properties": properties}

        logger.info(f"Updating page {page_id[:8]}...")
        result = self._make_request("PATCH", url, json=payload)
        logger.info(f"✅ Page updated successfully: {page_id[:8]}")
        return result

    def query_database(
        self,
        database_id: str,
        filter_params: dict | None = None,
        sort_params: list[dict] | None = None,
        page_size: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Query a Notion database with optional filtering and sorting.

        Args:
            database_id: The ID of the database to query
            filter_params: Optional filter criteria
            sort_params: Optional sorting criteria
            page_size: Number of results per page (max 100)

        Returns:
            List of database pages matching the query

        Raises:
            ValueError: If database ID is invalid or API call fails
        """
        self._validate_database_id(database_id, "database query")

        url = f"{self.config.base_url}/databases/{database_id}/query"
        payload = {"page_size": page_size}

        if filter_params:
            payload["filter"] = filter_params
        if sort_params:
            payload["sorts"] = sort_params

        all_results = []
        has_more = True
        start_cursor = None

        logger.info(f"Querying database {database_id[:8]}...")

        while has_more:
            if start_cursor:
                payload["start_cursor"] = start_cursor

            result = self._make_request("POST", url, json=payload)
            all_results.extend(result["results"])

            has_more = result.get("has_more", False)
            start_cursor = result.get("next_cursor")

        logger.info(f"✅ Retrieved {len(all_results)} pages from database")
        return all_results

    def get_database(self, database_id: str) -> dict[str, Any]:
        """
        Get database metadata and schema.

        Args:
            database_id: The ID of the database to retrieve

        Returns:
            Dict containing database metadata

        Raises:
            ValueError: If database ID is invalid or API call fails
        """
        self._validate_database_id(database_id, "database retrieval")

        url = f"{self.config.base_url}/databases/{database_id}"

        logger.info(f"Retrieving database {database_id[:8]}...")
        result = self._make_request("GET", url)
        logger.info("✅ Database retrieved successfully")
        return result

    def get_page(self, page_id: str) -> dict[str, Any]:
        """
        Get a specific page by ID.

        Args:
            page_id: The ID of the page to retrieve

        Returns:
            Dict containing page data

        Raises:
            ValueError: If page ID is invalid or API call fails
        """
        if not page_id:
            raise ValueError("❌ Page ID is required for page retrieval")

        url = f"{self.config.base_url}/pages/{page_id}"

        logger.info(f"Retrieving page {page_id[:8]}...")
        result = self._make_request("GET", url)
        logger.info("✅ Page retrieved successfully")
        return result

    def create_database(
        self,
        parent_page_id: str,
        title: str,
        description: str,
        properties: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Create a new Notion database.

        Args:
            parent_page_id: The ID of the parent page
            title: Title of the database
            description: Description of the database
            properties: Dictionary of database properties/schema

        Returns:
            Dict containing the created database data

        Raises:
            ValueError: If required parameters are invalid or API call fails
        """
        if not parent_page_id:
            raise ValueError("❌ Parent page ID is required for database creation")

        url = f"{self.config.base_url}/databases"
        payload = {
            "parent": {"page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": title}}],
            "description": [{"type": "text", "text": {"content": description}}],
            "properties": properties,
        }

        logger.info(f"Creating database '{title}'...")
        result = self._make_request("POST", url, json=payload)
        logger.info(f"✅ Database created successfully: {result['id']}")
        return result

    def search(
        self, query: str = "", filter_params: dict | None = None
    ) -> list[dict[str, Any]]:
        """
        Search across all accessible Notion content.

        Args:
            query: Search query string
            filter_params: Optional filter criteria

        Returns:
            List of matching pages and databases

        Raises:
            ValueError: If API call fails
        """
        url = f"{self.config.base_url}/search"
        payload = {"query": query}

        if filter_params:
            payload.update(filter_params)

        logger.info(f"Searching for: '{query}'...")
        result = self._make_request("POST", url, json=payload)

        results = result.get("results", [])
        logger.info(f"✅ Found {len(results)} results")
        return results


# Global client instance for convenience
_global_client = None


def get_client() -> NotionClient:
    """
    Get or create the global Notion client instance.

    Returns:
        NotionClient: The global client instance
    """
    global _global_client
    if _global_client is None:
        _global_client = NotionClient()
    return _global_client


def add_page(database_id: str, properties: dict[str, Any]) -> str:
    """
    Convenience function to create a page and return its ID.

    Args:
        database_id: The ID of the database to create the page in
        properties: Dictionary of properties for the new page

    Returns:
        str: The ID of the created page

    Raises:
        ValueError: If database ID is invalid or API call fails
    """
    client = get_client()
    result = client.create_page(database_id, properties)
    return result["id"]


def query_database(
    database_id: str, filter_params: dict | None = None
) -> list[dict[str, Any]]:
    """
    Convenience function to query a database.

    Args:
        database_id: The ID of the database to query
        filter_params: Optional filter criteria

    Returns:
        List of database pages matching the query

    Raises:
        ValueError: If database ID is invalid or API call fails
    """
    client = get_client()
    return client.query_database(database_id, filter_params)


def update_page(page_id: str, properties: dict[str, Any]) -> dict[str, Any]:
    """
    Convenience function to update a page.

    Args:
        page_id: The ID of the page to update
        properties: Dictionary of properties to update

    Returns:
        Dict containing the updated page data

    Raises:
        ValueError: If page ID is invalid or API call fails
    """
    client = get_client()
    return client.update_page(page_id, properties)


def get_database_id(project: str, database_type: str) -> str | None:
    """
    Get database ID for a specific project and database type.

    Args:
        project: Project name (e.g., 'MAGSASA', 'KWENTO', 'AI_STUDIO')
        database_type: Type of database (e.g., 'CI', 'ROADMAP', 'MILESTONES')

    Returns:
        Optional[str]: Database ID if found, None otherwise
    """
    env_var_name = f"{project}_{database_type}_DB_ID"
    return os.getenv(env_var_name)


def validate_database_access(database_id: str, project: str = "Unknown") -> bool:
    """
    Validate that we can access a specific database.

    Args:
        database_id: The database ID to validate
        project: Project name for logging

    Returns:
        bool: True if database is accessible, False otherwise
    """
    if not database_id:
        logger.warning(f"⚠️ No database ID provided for {project}")
        return False

    try:
        client = get_client()
        client.get_database(database_id)
        logger.info(f"✅ Database access validated for {project}")
        return True
    except Exception as e:
        logger.error(f"❌ Database access failed for {project}: {e}")
        return False


def get_safe_database_id(project: str, database_type: str) -> str | None:
    """
    Safely get database ID with validation.

    Args:
        project: Project name (e.g., 'MAGSASA', 'KWENTO', 'AI_STUDIO')
        database_type: Type of database (e.g., 'CI', 'ROADMAP', 'MILESTONES')

    Returns:
        Optional[str]: Validated database ID if accessible, None otherwise
    """
    database_id = get_database_id(project, database_type)
    if database_id and validate_database_access(
        database_id, f"{project} {database_type}"
    ):
        return database_id
    return None


# Utility functions for common operations
def create_title_property(text: str) -> dict[str, Any]:
    """Create a Notion title property."""
    return {"title": [{"text": {"content": text}}]}


def create_rich_text_property(text: str) -> dict[str, Any]:
    """Create a Notion rich text property."""
    return {"rich_text": [{"text": {"content": text}}]}


def create_select_property(option: str) -> dict[str, Any]:
    """Create a Notion select property."""
    return {"select": {"name": option}}


def create_date_property(date_string: str) -> dict[str, Any]:
    """Create a Notion date property."""
    return {"date": {"start": date_string}}


def create_number_property(number: int | float) -> dict[str, Any]:
    """Create a Notion number property."""
    return {"number": number}


def create_url_property(url: str) -> dict[str, Any]:
    """Create a Notion URL property."""
    return {"url": url}


def extract_title_value(property_data: dict[str, Any]) -> str:
    """Extract text value from a Notion title property."""
    if "title" in property_data and property_data["title"]:
        return property_data["title"][0].get("text", {}).get("content", "")
    return ""


def extract_select_value(property_data: dict[str, Any]) -> str:
    """Extract value from a Notion select property."""
    if "select" in property_data and property_data["select"]:
        return property_data["select"].get("name", "")
    return ""


def extract_rich_text_value(property_data: dict[str, Any]) -> str:
    """Extract text value from a Notion rich text property."""
    if "rich_text" in property_data and property_data["rich_text"]:
        return "".join(
            [
                item.get("text", {}).get("content", "")
                for item in property_data["rich_text"]
            ]
        )
    return ""


def extract_date_value(property_data: dict[str, Any]) -> str:
    """Extract date value from a Notion date property."""
    if "date" in property_data and property_data["date"]:
        return property_data["date"].get("start", "")
    return ""


def extract_number_value(property_data: dict[str, Any]) -> int | float | None:
    """Extract number value from a Notion number property."""
    if "number" in property_data:
        return property_data["number"]
    return None


def extract_url_value(property_data: dict[str, Any]) -> str:
    """Extract URL value from a Notion URL property."""
    if "url" in property_data:
        return property_data["url"]
    return ""


if __name__ == "__main__":
    """Test the Notion client functionality."""
    try:
        # Test basic functionality
        print("🧪 Testing Notion client...")

        client = NotionClient()
        print("✅ Client initialized successfully")

        # Test API key validation
        api_key = client.api_key
        print(f"✅ API key loaded: {api_key[:20]}...")

        # Test database ID helpers
        test_db_id = get_database_id("MAGSASA", "CI")
        print(f"✅ Database ID helper works: {test_db_id or 'Not set'}")

        print("🎉 All tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
