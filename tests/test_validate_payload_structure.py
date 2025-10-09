#!/usr/bin/env python3
"""
Test Suite for Slack Payload Validation
=======================================

Tests the Slack payload validation, schema checking, and diff reporting.
"""

import json
import os
import sys
import unittest

# Add scripts directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from schema_diff_reporter import SchemaDiffReporter, Severity
from validate_slack_payload import SlackPayloadValidator


class TestSlackPayloadValidator(unittest.TestCase):
    """Test Slack payload validation functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = SlackPayloadValidator()

    def test_validate_valid_payload(self):
        """Test validation of a valid payload."""
        payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Test Header",
                        "emoji": True,
                    },
                }
            ],
            "color": "#56d364",
            "metadata": {"merge_score": 85, "status": "ON TRACK"},
        }

        is_valid, errors = self.validator.validate_payload(payload)

        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_validate_missing_blocks(self):
        """Test validation fails when blocks are missing."""
        payload = {"color": "#56d364"}

        is_valid, errors = self.validator.validate_payload(payload)

        self.assertFalse(is_valid)
        self.assertIn("Missing required 'blocks' field", errors[0])

    def test_validate_invalid_block_type(self):
        """Test validation fails with invalid block type."""
        payload = {
            "blocks": [
                {"type": "invalid_type", "text": {"type": "plain_text", "text": "Test"}}
            ]
        }

        is_valid, errors = self.validator.validate_payload(payload)

        self.assertFalse(is_valid)
        self.assertTrue(any("Invalid type" in error for error in errors))

    def test_validate_header_block(self):
        """Test validation of header blocks."""
        # Valid header
        payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Header Text",
                        "emoji": True,
                    },
                }
            ]
        }

        is_valid, errors = self.validator.validate_payload(payload)
        self.assertTrue(is_valid)

        # Invalid header - missing text
        payload = {"blocks": [{"type": "header"}]}

        is_valid, errors = self.validator.validate_payload(payload)
        self.assertFalse(is_valid)
        self.assertTrue(
            any("Missing required 'text' field" in error for error in errors)
        )

    def test_validate_section_block(self):
        """Test validation of section blocks."""
        # Valid section with fields
        payload = {
            "blocks": [
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": "*Field 1*\nValue 1"},
                        {"type": "mrkdwn", "text": "*Field 2*\nValue 2"},
                    ],
                }
            ]
        }

        is_valid, errors = self.validator.validate_payload(payload)
        self.assertTrue(is_valid)

        # Invalid section - missing text and fields
        payload = {"blocks": [{"type": "section"}]}

        is_valid, errors = self.validator.validate_payload(payload)
        self.assertFalse(is_valid)
        self.assertTrue(
            any("Must have either 'text' or 'fields'" in error for error in errors)
        )

    def test_validate_actions_block(self):
        """Test validation of actions blocks."""
        # Valid actions block
        payload = {
            "blocks": [
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Click Me",
                                "emoji": True,
                            },
                            "url": "https://example.com",
                        }
                    ],
                }
            ]
        }

        is_valid, errors = self.validator.validate_payload(payload)
        self.assertTrue(is_valid)

        # Invalid actions block - too many elements
        payload = {
            "blocks": [
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": f"Button {i}"},
                            "url": "https://example.com",
                        }
                        for i in range(6)
                    ],
                }
            ]
        }

        is_valid, errors = self.validator.validate_payload(payload)
        self.assertFalse(is_valid)
        self.assertTrue(
            any("cannot have more than 5 items" in error for error in errors)
        )

    def test_validate_context_block(self):
        """Test validation of context blocks."""
        # Valid context block
        payload = {
            "blocks": [
                {
                    "type": "context",
                    "elements": [{"type": "mrkdwn", "text": "Context information"}],
                }
            ]
        }

        is_valid, errors = self.validator.validate_payload(payload)
        self.assertTrue(is_valid)

        # Invalid context block - empty elements
        payload = {"blocks": [{"type": "context", "elements": []}]}

        is_valid, errors = self.validator.validate_payload(payload)
        self.assertFalse(is_valid)
        self.assertTrue(any("cannot be empty" in error for error in errors))

    def test_validate_button_element(self):
        """Test validation of button elements."""
        # Valid button with URL
        payload = {
            "blocks": [
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Click Me"},
                            "url": "https://example.com",
                        }
                    ],
                }
            ]
        }

        is_valid, errors = self.validator.validate_payload(payload)
        self.assertTrue(is_valid)

        # Invalid button - both url and action_id
        payload = {
            "blocks": [
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Click Me"},
                            "url": "https://example.com",
                            "action_id": "button_click",
                        }
                    ],
                }
            ]
        }

        is_valid, errors = self.validator.validate_payload(payload)
        self.assertFalse(is_valid)
        self.assertTrue(any("Cannot have both" in error for error in errors))

    def test_validate_color_field(self):
        """Test validation of color field."""
        # Valid color
        payload = {
            "blocks": [
                {"type": "header", "text": {"type": "plain_text", "text": "Test"}}
            ],
            "color": "#56d364",
        }

        is_valid, errors = self.validator.validate_payload(payload)
        self.assertTrue(is_valid)

        # Invalid color - wrong format
        payload["color"] = "56d364"  # Missing #
        is_valid, errors = self.validator.validate_payload(payload)
        self.assertFalse(is_valid)
        self.assertTrue(any("Color must start with #" in error for error in errors))

        # Invalid color - wrong length
        payload["color"] = "#56d"
        is_valid, errors = self.validator.validate_payload(payload)
        self.assertFalse(is_valid)
        self.assertTrue(any("Color must be 7 characters" in error for error in errors))

    def test_validate_text_object(self):
        """Test validation of text objects."""
        # Valid text object
        text_obj = {"type": "plain_text", "text": "Test text", "emoji": True}

        errors = self.validator._validate_text_object(text_obj, "test.text")
        self.assertEqual(len(errors), 0)

        # Invalid - missing type
        text_obj = {"text": "Test text"}

        errors = self.validator._validate_text_object(text_obj, "test.text")
        self.assertTrue(
            any("Missing required 'type' field" in error for error in errors)
        )

        # Invalid - wrong type
        text_obj = {"type": "invalid_type", "text": "Test text"}

        errors = self.validator._validate_text_object(text_obj, "test.text")
        self.assertTrue(any("Invalid type" in error for error in errors))

        # Invalid - text too long
        text_obj = {"type": "plain_text", "text": "x" * 3001}

        errors = self.validator._validate_text_object(text_obj, "test.text")
        self.assertTrue(
            any("cannot exceed 3000 characters" in error for error in errors)
        )

    def test_suggest_fixes(self):
        """Test fix suggestions."""
        payload = {"color": "invalid"}

        is_valid, errors = self.validator.validate_payload(payload)
        self.assertFalse(is_valid)

        suggestions = self.validator.suggest_fixes(payload, errors)
        self.assertGreater(len(suggestions), 0)
        self.assertTrue(
            any("blocks" in suggestion.lower() for suggestion in suggestions)
        )

    def test_create_example_payload(self):
        """Test example payload creation."""
        example = self.validator.create_example_payload()

        # Validate the example
        is_valid, errors = self.validator.validate_payload(example)
        self.assertTrue(is_valid, f"Example payload should be valid. Errors: {errors}")
        self.assertIn("blocks", example)
        self.assertIn("color", example)
        self.assertIn("metadata", example)


class TestSchemaDiffReporter(unittest.TestCase):
    """Test schema diff reporter functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.reporter = SchemaDiffReporter()

    def test_compare_valid_payload(self):
        """Test comparison of valid payload."""
        payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "Test Header"},
                }
            ]
        }

        schema = {"properties": {"blocks": {}, "color": {}, "metadata": {}}}

        issues = self.reporter.compare_payload_to_schema(payload, schema)

        # Should have issues for missing optional fields
        self.assertIsInstance(issues, list)

    def test_compare_missing_blocks(self):
        """Test comparison detects missing blocks."""
        payload = {"color": "#56d364"}

        schema = {"properties": {"blocks": {}, "color": {}, "metadata": {}}}

        issues = self.reporter.compare_payload_to_schema(payload, schema)

        # Should have issues for missing blocks
        blocks_issues = [i for i in issues if i.path == "blocks"]
        self.assertGreater(len(blocks_issues), 0)
        self.assertEqual(blocks_issues[0].severity, Severity.CRITICAL)

    def test_validate_header_block(self):
        """Test header block validation."""
        # Valid header
        block = {"type": "header", "text": {"type": "plain_text", "text": "Header"}}

        issues = self.reporter._validate_header_block(block, "blocks[0]")
        self.assertEqual(len(issues), 0)

        # Invalid header - missing text
        block = {"type": "header"}

        issues = self.reporter._validate_header_block(block, "blocks[0]")
        self.assertGreater(len(issues), 0)
        self.assertEqual(issues[0].severity, Severity.CRITICAL)

    def test_validate_section_block(self):
        """Test section block validation."""
        # Valid section with text
        block = {"type": "section", "text": {"type": "mrkdwn", "text": "Section text"}}

        issues = self.reporter._validate_section_block(block, "blocks[0]")
        self.assertEqual(len(issues), 0)

        # Invalid section - missing text and fields
        block = {"type": "section"}

        issues = self.reporter._validate_section_block(block, "blocks[0]")
        self.assertGreater(len(issues), 0)
        self.assertEqual(issues[0].severity, Severity.HIGH)

    def test_validate_actions_block(self):
        """Test actions block validation."""
        # Valid actions
        block = {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Click"},
                    "url": "https://example.com",
                }
            ],
        }

        issues = self.reporter._validate_actions_block(block, "blocks[0]")
        self.assertEqual(len(issues), 0)

        # Invalid actions - empty elements
        block = {"type": "actions", "elements": []}

        issues = self.reporter._validate_actions_block(block, "blocks[0]")
        self.assertGreater(len(issues), 0)

    def test_validate_button_element(self):
        """Test button element validation."""
        # Valid button
        element = {
            "type": "button",
            "text": {"type": "plain_text", "text": "Click"},
            "url": "https://example.com",
        }

        issues = self.reporter._validate_button_element(
            element, "blocks[0].elements[0]"
        )
        self.assertEqual(len(issues), 0)

        # Invalid button - both url and action_id
        element = {
            "type": "button",
            "text": {"type": "plain_text", "text": "Click"},
            "url": "https://example.com",
            "action_id": "click_action",
        }

        issues = self.reporter._validate_button_element(
            element, "blocks[0].elements[0]"
        )
        self.assertGreater(len(issues), 0)

        # Invalid button - neither url nor action_id
        element = {"type": "button", "text": {"type": "plain_text", "text": "Click"}}

        issues = self.reporter._validate_button_element(
            element, "blocks[0].elements[0]"
        )
        self.assertGreater(len(issues), 0)

    def test_severity_ordering(self):
        """Test that issues are ordered by severity."""
        payload = {
            "blocks": [
                {"type": "invalid_type"},  # CRITICAL
                {"type": "section"},  # HIGH - missing text/fields
            ],
            "color": "invalid",  # HIGH - invalid color
        }

        schema = {}
        issues = self.reporter.compare_payload_to_schema(payload, schema)

        # First issues should be CRITICAL
        if len(issues) > 0:
            self.assertIn(issues[0].severity, [Severity.CRITICAL, Severity.HIGH])

    def test_field_severity_classification(self):
        """Test field severity classification."""
        # Critical fields
        self.assertEqual(self.reporter._get_field_severity("blocks"), Severity.CRITICAL)

        # High importance fields
        self.assertEqual(self.reporter._get_field_severity("color"), Severity.HIGH)

        # Other fields
        severity = self.reporter._get_field_severity("some_other_field")
        self.assertIn(severity, [Severity.MEDIUM, Severity.LOW, Severity.INFO])


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete validation flow."""

    def test_validate_and_diff_example_payload(self):
        """Test validation and diff reporting on example payload."""
        # Load example payload
        example_file = os.path.join(
            os.path.dirname(__file__), "..", "example_payload.json"
        )

        if os.path.exists(example_file):
            with open(example_file) as f:
                payload = json.load(f)

            # Validate with validator
            validator = SlackPayloadValidator()
            is_valid, errors = validator.validate_payload(payload)

            # Example payload should be valid
            self.assertTrue(
                is_valid, f"Example payload should be valid. Errors: {errors}"
            )

            # Check with diff reporter
            reporter = SchemaDiffReporter()
            issues = reporter.compare_payload_to_schema(payload, {})

            # Should have minimal issues
            critical_issues = [i for i in issues if i.severity == Severity.CRITICAL]
            self.assertEqual(
                len(critical_issues),
                0,
                "Example payload should have no critical issues",
            )

    def test_full_validation_workflow(self):
        """Test complete validation workflow."""
        # Create a payload
        payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📊 Merge Quality Report",
                        "emoji": True,
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": "*Score:*\n`85%` ✅"},
                        {"type": "mrkdwn", "text": "*Status:*\nON TRACK"},
                    ],
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View Dashboard",
                                "emoji": True,
                            },
                            "url": "https://example.com/dashboard",
                        }
                    ],
                },
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": "Generated by Merge Quality System"}
                    ],
                },
            ],
            "color": "#56d364",
            "metadata": {
                "merge_score": 85,
                "status": "ON TRACK",
                "auto_fail": False,
                "early_warning": False,
            },
        }

        # Step 1: Validate with validator
        validator = SlackPayloadValidator()
        is_valid, errors = validator.validate_payload(payload)
        self.assertTrue(is_valid, f"Payload should be valid. Errors: {errors}")

        # Step 2: Check with diff reporter
        reporter = SchemaDiffReporter()
        issues = reporter.compare_payload_to_schema(payload, {})

        # Should have no critical issues
        critical_issues = [i for i in issues if i.severity == Severity.CRITICAL]
        self.assertEqual(len(critical_issues), 0, "Should have no critical issues")


if __name__ == "__main__":
    unittest.main()
