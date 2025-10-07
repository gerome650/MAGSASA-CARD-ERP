#!/usr/bin/env python3
"""
Slack Payload Validator
=======================

Validates Slack Block Kit payloads against JSON Schema and provides
suggestions for fixes. Supports both validation-only and fix-suggestion modes.
"""

import argparse
import json
import os
import sys


class SlackPayloadValidator:
    """Validates Slack Block Kit payloads against schema."""

    def __init__(self, schema_path: str | None = None):
        self.schema_path = schema_path or "slack_payload_schema.json"
        self.schema = self._load_schema()

        # Common validation rules
        self.block_types = {
            "header",
            "section",
            "divider",
            "context",
            "actions",
            "input",
            "file",
            "image",
            "video",
            "audio",
        }

        self.element_types = {
            "button",
            "static_select",
            "multi_static_select",
            "datepicker",
            "timepicker",
            "datetimepicker",
            "checkboxes",
            "radio_buttons",
            "plain_text_input",
            "conversations_select",
            "channels_select",
            "users_select",
            "external_select",
            "multi_external_select",
            "overflow",
            "image",
        }

    def _load_schema(self) -> dict:
        """Load JSON schema for validation."""
        if os.path.exists(self.schema_path):
            try:
                with open(self.schema_path) as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                print(f"Warning: Could not load schema from {self.schema_path}: {e}")

        # Return default schema if file doesn't exist
        return self._get_default_schema()

    def _get_default_schema(self) -> dict:
        """Get default JSON schema for Slack Block Kit payloads."""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["blocks"],
            "properties": {
                "blocks": {"type": "array", "items": {"$ref": "#/definitions/block"}},
                "color": {"type": "string", "pattern": "^#[0-9a-fA-F]{6}$"},
                "metadata": {"type": "object"},
            },
            "definitions": {
                "block": {
                    "type": "object",
                    "required": ["type"],
                    "properties": {
                        "type": {"type": "string", "enum": list(self.block_types)},
                        "text": {"$ref": "#/definitions/text_object"},
                        "fields": {
                            "type": "array",
                            "items": {"$ref": "#/definitions/text_object"},
                        },
                        "elements": {
                            "type": "array",
                            "items": {"$ref": "#/definitions/element"},
                        },
                    },
                },
                "text_object": {
                    "type": "object",
                    "required": ["type", "text"],
                    "properties": {
                        "type": {"type": "string", "enum": ["plain_text", "mrkdwn"]},
                        "text": {"type": "string"},
                        "emoji": {"type": "boolean"},
                        "verbatim": {"type": "boolean"},
                    },
                },
                "element": {
                    "type": "object",
                    "required": ["type"],
                    "properties": {
                        "type": {"type": "string", "enum": list(self.element_types)},
                        "text": {"$ref": "#/definitions/text_object"},
                        "url": {"type": "string", "format": "uri"},
                        "value": {"type": "string"},
                        "action_id": {"type": "string"},
                        "placeholder": {"$ref": "#/definitions/text_object"},
                    },
                },
            },
        }

    def validate_payload(self, payload: dict) -> tuple[bool, list[str]]:
        """
        Validate payload against schema.

        Args:
            payload: Slack payload to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Basic structure validation
        if not isinstance(payload, dict):
            errors.append("Payload must be a JSON object")
            return False, errors

        if "blocks" not in payload:
            errors.append("Missing required 'blocks' field")
            return False, errors

        if not isinstance(payload["blocks"], list):
            errors.append("'blocks' must be an array")
            return False, errors

        # Validate each block
        for i, block in enumerate(payload["blocks"]):
            block_errors = self._validate_block(block, i)
            errors.extend(block_errors)

        # Validate color if present
        if "color" in payload:
            color_error = self._validate_color(payload["color"])
            if color_error:
                errors.append(color_error)

        return len(errors) == 0, errors

    def _validate_block(self, block: dict, block_index: int) -> list[str]:
        """Validate individual block."""
        errors = []

        if not isinstance(block, dict):
            errors.append(f"Block {block_index}: Must be an object")
            return errors

        if "type" not in block:
            errors.append(f"Block {block_index}: Missing required 'type' field")
            return errors

        block_type = block["type"]
        if block_type not in self.block_types:
            errors.append(f"Block {block_index}: Invalid type '{block_type}'")
            return errors

        # Type-specific validation
        if block_type == "header":
            errors.extend(self._validate_header_block(block, block_index))
        elif block_type == "section":
            errors.extend(self._validate_section_block(block, block_index))
        elif block_type == "actions":
            errors.extend(self._validate_actions_block(block, block_index))
        elif block_type == "context":
            errors.extend(self._validate_context_block(block, block_index))

        return errors

    def _validate_header_block(self, block: dict, block_index: int) -> list[str]:
        """Validate header block."""
        errors = []

        if "text" not in block:
            errors.append(
                f"Block {block_index} (header): Missing required 'text' field"
            )
        else:
            text_errors = self._validate_text_object(
                block["text"], f"Block {block_index} (header).text"
            )
            errors.extend(text_errors)

        return errors

    def _validate_section_block(self, block: dict, block_index: int) -> list[str]:
        """Validate section block."""
        errors = []

        has_text = "text" in block
        has_fields = "fields" in block

        if not has_text and not has_fields:
            errors.append(
                f"Block {block_index} (section): Must have either 'text' or 'fields'"
            )

        if has_text:
            text_errors = self._validate_text_object(
                block["text"], f"Block {block_index} (section).text"
            )
            errors.extend(text_errors)

        if has_fields:
            if not isinstance(block["fields"], list):
                errors.append(
                    f"Block {block_index} (section): 'fields' must be an array"
                )
            else:
                for i, field in enumerate(block["fields"]):
                    field_errors = self._validate_text_object(
                        field, f"Block {block_index} (section).fields[{i}]"
                    )
                    errors.extend(field_errors)

        return errors

    def _validate_actions_block(self, block: dict, block_index: int) -> list[str]:
        """Validate actions block."""
        errors = []

        if "elements" not in block:
            errors.append(
                f"Block {block_index} (actions): Missing required 'elements' field"
            )
        else:
            if not isinstance(block["elements"], list):
                errors.append(
                    f"Block {block_index} (actions): 'elements' must be an array"
                )
            elif len(block["elements"]) == 0:
                errors.append(
                    f"Block {block_index} (actions): 'elements' cannot be empty"
                )
            elif len(block["elements"]) > 5:
                errors.append(
                    f"Block {block_index} (actions): 'elements' cannot have more than 5 items"
                )
            else:
                for i, element in enumerate(block["elements"]):
                    element_errors = self._validate_element(
                        element, f"Block {block_index} (actions).elements[{i}]"
                    )
                    errors.extend(element_errors)

        return errors

    def _validate_context_block(self, block: dict, block_index: int) -> list[str]:
        """Validate context block."""
        errors = []

        if "elements" not in block:
            errors.append(
                f"Block {block_index} (context): Missing required 'elements' field"
            )
        else:
            if not isinstance(block["elements"], list):
                errors.append(
                    f"Block {block_index} (context): 'elements' must be an array"
                )
            elif len(block["elements"]) == 0:
                errors.append(
                    f"Block {block_index} (context): 'elements' cannot be empty"
                )
            elif len(block["elements"]) > 10:
                errors.append(
                    f"Block {block_index} (context): 'elements' cannot have more than 10 items"
                )
            else:
                for i, element in enumerate(block["elements"]):
                    element_errors = self._validate_text_object(
                        element, f"Block {block_index} (context).elements[{i}]"
                    )
                    errors.extend(element_errors)

        return errors

    def _validate_element(self, element: dict, path: str) -> list[str]:
        """Validate interactive element."""
        errors = []

        if not isinstance(element, dict):
            errors.append(f"{path}: Must be an object")
            return errors

        if "type" not in element:
            errors.append(f"{path}: Missing required 'type' field")
            return errors

        element_type = element["type"]
        if element_type not in self.element_types:
            errors.append(f"{path}: Invalid type '{element_type}'")
            return errors

        # Validate button element
        if element_type == "button":
            if "text" not in element:
                errors.append(f"{path}: Missing required 'text' field")
            else:
                text_errors = self._validate_text_object(
                    element["text"], f"{path}.text"
                )
                errors.extend(text_errors)

            if "url" in element and "action_id" in element:
                errors.append(f"{path}: Cannot have both 'url' and 'action_id'")
            elif "url" not in element and "action_id" not in element:
                errors.append(f"{path}: Must have either 'url' or 'action_id'")

        return errors

    def _validate_text_object(self, text_obj: dict, path: str) -> list[str]:
        """Validate text object."""
        errors = []

        if not isinstance(text_obj, dict):
            errors.append(f"{path}: Must be an object")
            return errors

        if "type" not in text_obj:
            errors.append(f"{path}: Missing required 'type' field")
        elif text_obj["type"] not in ["plain_text", "mrkdwn"]:
            errors.append(f"{path}: Invalid type '{text_obj['type']}'")

        if "text" not in text_obj:
            errors.append(f"{path}: Missing required 'text' field")
        elif not isinstance(text_obj["text"], str):
            errors.append(f"{path}: 'text' must be a string")
        elif len(text_obj["text"]) > 3000:
            errors.append(f"{path}: 'text' cannot exceed 3000 characters")

        return errors

    def _validate_color(self, color: str) -> str | None:
        """Validate color format."""
        if not isinstance(color, str):
            return "Color must be a string"

        if not color.startswith("#"):
            return "Color must start with #"

        if len(color) != 7:
            return "Color must be 7 characters (#RRGGBB)"

        try:
            int(color[1:], 16)
        except ValueError:
            return "Color must be valid hex (#RRGGBB)"

        return None

    def suggest_fixes(self, payload: dict, errors: list[str]) -> list[str]:
        """
        Suggest fixes for validation errors.

        Args:
            payload: Original payload
            errors: List of validation errors

        Returns:
            List of suggested fixes
        """
        suggestions = []

        for error in errors:
            if "Missing required 'blocks' field" in error:
                suggestions.append("Add 'blocks' array to payload root")

            elif "blocks' must be an array" in error:
                suggestions.append("Change 'blocks' to an array format: []")

            elif "Missing required 'type' field" in error:
                suggestions.append("Add 'type' field to block with valid block type")

            elif "Invalid type" in error:
                suggestions.append(
                    "Use valid block type: header, section, divider, context, actions"
                )

            elif "Missing required 'text' field" in error:
                suggestions.append("Add 'text' field with type and text properties")

            elif "text' must be a string" in error:
                suggestions.append("Change text field to string value")

            elif "Color must be" in error:
                suggestions.append("Use valid hex color format: #RRGGBB")

            elif "cannot exceed 3000 characters" in error:
                suggestions.append("Shorten text content to under 3000 characters")

            else:
                suggestions.append(f"Review and fix: {error}")

        return suggestions

    def create_example_payload(self) -> dict:
        """Create example valid payload."""
        return {
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
                        {"type": "mrkdwn", "text": "*Merge Score:*\n`85%` ✅"},
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
            "metadata": {"merge_score": 85, "status": "ON TRACK"},
        }


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Validate Slack Block Kit payloads")
    parser.add_argument("payload", help="Payload JSON file to validate")
    parser.add_argument("--schema", help="Custom schema file path")
    parser.add_argument(
        "--suggest-fixes",
        action="store_true",
        help="Suggest fixes for validation errors",
    )
    parser.add_argument(
        "--create-example", action="store_true", help="Create example payload file"
    )
    parser.add_argument("--output", help="Output file for suggestions or example")

    args = parser.parse_args()

    validator = SlackPayloadValidator(schema_path=args.schema)

    # Create example payload if requested
    if args.create_example:
        example = validator.create_example_payload()
        output_file = args.output or "example_payload.json"

        with open(output_file, "w") as f:
            json.dump(example, f, indent=2)

        print(f"✅ Example payload created: {output_file}")
        return

    # Validate payload
    try:
        with open(args.payload) as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"❌ Error loading payload file: {e}")
        sys.exit(1)

    is_valid, errors = validator.validate_payload(payload)

    if is_valid:
        print("✅ Payload is valid!")
    else:
        print("❌ Payload validation failed:")
        for error in errors:
            print(f"  - {error}")

        if args.suggest_fixes:
            suggestions = validator.suggest_fixes(payload, errors)
            print("\n💡 Suggested fixes:")
            for suggestion in suggestions:
                print(f"  - {suggestion}")

            if args.output:
                with open(args.output, "w") as f:
                    json.dump(
                        {"errors": errors, "suggestions": suggestions}, f, indent=2
                    )
                print(f"\n📝 Suggestions saved to: {args.output}")

        sys.exit(1)


if __name__ == "__main__":
    main()
