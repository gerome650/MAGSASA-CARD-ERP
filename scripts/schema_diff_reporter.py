#!/usr/bin/env python3
"""
Schema Diff Reporter
====================

Shows field-by-field differences between payloads and schema with severity ranking.
Helps identify missing fields, incorrect types, and validation issues.
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any


class Severity(Enum):
    """Severity levels for validation issues."""

    CRITICAL = "critical"  # Blocking issues
    HIGH = "high"  # Important issues
    MEDIUM = "medium"  # Moderate issues
    LOW = "low"  # Minor issues
    INFO = "info"  # Informational


@dataclass
class DiffIssue:
    """Represents a single diff issue."""

    path: str
    severity: Severity
    message: str
    expected: str | None = None
    actual: str | None = None
    suggestion: str | None = None


class SchemaDiffReporter:
    """Reports differences between payloads and schema with severity ranking."""

    def __init__(self):
        self.severity_colors = {
            Severity.CRITICAL: "🔴",
            Severity.HIGH: "🟠",
            Severity.MEDIUM: "🟡",
            Severity.LOW: "🔵",
            Severity.INFO: "⚪",
        }

        # Field importance mapping
        self.critical_fields = {
            "blocks",
            "blocks[*].type",
            "blocks[*].text.type",
            "blocks[*].text.text",
        }

        self.high_importance_fields = {
            "blocks[*].text",
            "blocks[*].fields",
            "blocks[*].elements",
            "color",
        }

    def compare_payload_to_schema(self, payload: dict, schema: dict) -> list[DiffIssue]:
        """
        Compare payload against schema and return diff issues.

        Args:
            payload: Payload to validate
            schema: JSON schema to compare against

        Returns:
            List of diff issues sorted by severity
        """
        issues = []

        # Check required fields
        required_fields = schema.get("properties", {}).keys()
        for field in required_fields:
            if field not in payload:
                severity = self._get_field_severity(field)
                issues.append(
                    DiffIssue(
                        path=field,
                        severity=severity,
                        message=f"Missing required field: {field}",
                        suggestion=f"Add '{field}' field to payload",
                    )
                )

        # Validate payload structure
        issues.extend(self._validate_payload_structure(payload, schema))

        # Sort by severity
        severity_order = [
            Severity.CRITICAL,
            Severity.HIGH,
            Severity.MEDIUM,
            Severity.LOW,
            Severity.INFO,
        ]
        issues.sort(key=lambda x: severity_order.index(x.severity))

        return issues

    def _get_field_severity(self, field_path: str) -> Severity:
        """Get severity level for a field path."""
        if field_path in self.critical_fields:
            return Severity.CRITICAL
        elif field_path in self.high_importance_fields:
            return Severity.HIGH
        elif "blocks[*]" in field_path:
            return Severity.MEDIUM
        else:
            return Severity.LOW

    def _validate_payload_structure(
        self, payload: dict, schema: dict
    ) -> list[DiffIssue]:
        """Validate payload structure against schema."""
        issues = []

        # Validate blocks array
        if "blocks" in payload:
            blocks = payload["blocks"]
            if not isinstance(blocks, list):
                issues.append(
                    DiffIssue(
                        path="blocks",
                        severity=Severity.CRITICAL,
                        message="'blocks' must be an array",
                        actual=type(blocks).__name__,
                        expected="array",
                        suggestion="Change 'blocks' to an array: []",
                    )
                )
            else:
                # Validate each block
                for i, block in enumerate(blocks):
                    block_issues = self._validate_block(block, i, schema)
                    issues.extend(block_issues)

        # Validate color field
        if "color" in payload:
            color_issues = self._validate_color_field(payload["color"])
            issues.extend(color_issues)

        return issues

    def _validate_block(
        self, block: dict, block_index: int, schema: dict
    ) -> list[DiffIssue]:
        """Validate individual block."""
        issues = []
        block_path = f"blocks[{block_index}]"

        if not isinstance(block, dict):
            issues.append(
                DiffIssue(
                    path=block_path,
                    severity=Severity.CRITICAL,
                    message="Block must be an object",
                    actual=type(block).__name__,
                    expected="object",
                    suggestion="Change block to object format: {}",
                )
            )
            return issues

        # Validate block type
        if "type" not in block:
            issues.append(
                DiffIssue(
                    path=f"{block_path}.type",
                    severity=Severity.CRITICAL,
                    message="Missing required 'type' field",
                    suggestion="Add 'type' field with valid block type",
                )
            )
        else:
            block_type = block["type"]
            valid_types = [
                "header",
                "section",
                "divider",
                "context",
                "actions",
                "input",
            ]
            if block_type not in valid_types:
                issues.append(
                    DiffIssue(
                        path=f"{block_path}.type",
                        severity=Severity.HIGH,
                        message=f"Invalid block type: {block_type}",
                        actual=block_type,
                        expected=f"One of: {', '.join(valid_types)}",
                        suggestion=f"Use valid block type: {', '.join(valid_types)}",
                    )
                )

        # Type-specific validation
        block_type = block.get("type", "")
        if block_type == "header":
            issues.extend(self._validate_header_block(block, block_path))
        elif block_type == "section":
            issues.extend(self._validate_section_block(block, block_path))
        elif block_type == "actions":
            issues.extend(self._validate_actions_block(block, block_path))
        elif block_type == "context":
            issues.extend(self._validate_context_block(block, block_path))

        return issues

    def _validate_header_block(self, block: dict, block_path: str) -> list[DiffIssue]:
        """Validate header block."""
        issues = []

        if "text" not in block:
            issues.append(
                DiffIssue(
                    path=f"{block_path}.text",
                    severity=Severity.CRITICAL,
                    message="Header block missing required 'text' field",
                    suggestion="Add 'text' field with type and text properties",
                )
            )
        else:
            text_issues = self._validate_text_object(
                block["text"], f"{block_path}.text"
            )
            issues.extend(text_issues)

        return issues

    def _validate_section_block(self, block: dict, block_path: str) -> list[DiffIssue]:
        """Validate section block."""
        issues = []

        has_text = "text" in block
        has_fields = "fields" in block

        if not has_text and not has_fields:
            issues.append(
                DiffIssue(
                    path=block_path,
                    severity=Severity.HIGH,
                    message="Section block must have either 'text' or 'fields'",
                    suggestion="Add either 'text' or 'fields' property to section block",
                )
            )

        if has_text:
            text_issues = self._validate_text_object(
                block["text"], f"{block_path}.text"
            )
            issues.extend(text_issues)

        if has_fields:
            fields = block["fields"]
            if not isinstance(fields, list):
                issues.append(
                    DiffIssue(
                        path=f"{block_path}.fields",
                        severity=Severity.HIGH,
                        message="'fields' must be an array",
                        actual=type(fields).__name__,
                        expected="array",
                        suggestion="Change 'fields' to an array: []",
                    )
                )
            else:
                if len(fields) > 10:
                    issues.append(
                        DiffIssue(
                            path=f"{block_path}.fields",
                            severity=Severity.MEDIUM,
                            message=f"Too many fields: {len(fields)} (max 10)",
                            actual=str(len(fields)),
                            expected="≤ 10",
                            suggestion="Reduce number of fields to 10 or fewer",
                        )
                    )

                for i, field in enumerate(fields):
                    field_issues = self._validate_text_object(
                        field, f"{block_path}.fields[{i}]"
                    )
                    issues.extend(field_issues)

        return issues

    def _validate_actions_block(self, block: dict, block_path: str) -> list[DiffIssue]:
        """Validate actions block."""
        issues = []

        if "elements" not in block:
            issues.append(
                DiffIssue(
                    path=f"{block_path}.elements",
                    severity=Severity.CRITICAL,
                    message="Actions block missing required 'elements' field",
                    suggestion="Add 'elements' array with interactive elements",
                )
            )
        else:
            elements = block["elements"]
            if not isinstance(elements, list):
                issues.append(
                    DiffIssue(
                        path=f"{block_path}.elements",
                        severity=Severity.HIGH,
                        message="'elements' must be an array",
                        actual=type(elements).__name__,
                        expected="array",
                        suggestion="Change 'elements' to an array: []",
                    )
                )
            else:
                if len(elements) == 0:
                    issues.append(
                        DiffIssue(
                            path=f"{block_path}.elements",
                            severity=Severity.MEDIUM,
                            message="'elements' array is empty",
                            suggestion="Add at least one interactive element",
                        )
                    )
                elif len(elements) > 5:
                    issues.append(
                        DiffIssue(
                            path=f"{block_path}.elements",
                            severity=Severity.MEDIUM,
                            message=f"Too many elements: {len(elements)} (max 5)",
                            actual=str(len(elements)),
                            expected="≤ 5",
                            suggestion="Reduce number of elements to 5 or fewer",
                        )
                    )

                for i, element in enumerate(elements):
                    element_issues = self._validate_element(
                        element, f"{block_path}.elements[{i}]"
                    )
                    issues.extend(element_issues)

        return issues

    def _validate_context_block(self, block: dict, block_path: str) -> list[DiffIssue]:
        """Validate context block."""
        issues = []

        if "elements" not in block:
            issues.append(
                DiffIssue(
                    path=f"{block_path}.elements",
                    severity=Severity.CRITICAL,
                    message="Context block missing required 'elements' field",
                    suggestion="Add 'elements' array with text objects",
                )
            )
        else:
            elements = block["elements"]
            if not isinstance(elements, list):
                issues.append(
                    DiffIssue(
                        path=f"{block_path}.elements",
                        severity=Severity.HIGH,
                        message="'elements' must be an array",
                        actual=type(elements).__name__,
                        expected="array",
                        suggestion="Change 'elements' to an array: []",
                    )
                )
            else:
                if len(elements) > 10:
                    issues.append(
                        DiffIssue(
                            path=f"{block_path}.elements",
                            severity=Severity.MEDIUM,
                            message=f"Too many elements: {len(elements)} (max 10)",
                            actual=str(len(elements)),
                            expected="≤ 10",
                            suggestion="Reduce number of elements to 10 or fewer",
                        )
                    )

                for i, element in enumerate(elements):
                    element_issues = self._validate_text_object(
                        element, f"{block_path}.elements[{i}]"
                    )
                    issues.extend(element_issues)

        return issues

    def _validate_element(self, element: dict, element_path: str) -> list[DiffIssue]:
        """Validate interactive element."""
        issues = []

        if not isinstance(element, dict):
            issues.append(
                DiffIssue(
                    path=element_path,
                    severity=Severity.CRITICAL,
                    message="Element must be an object",
                    actual=type(element).__name__,
                    expected="object",
                    suggestion="Change element to object format: {}",
                )
            )
            return issues

        if "type" not in element:
            issues.append(
                DiffIssue(
                    path=f"{element_path}.type",
                    severity=Severity.CRITICAL,
                    message="Element missing required 'type' field",
                    suggestion="Add 'type' field with valid element type",
                )
            )
        else:
            element_type = element["type"]
            valid_types = ["button", "static_select", "datepicker", "overflow", "image"]
            if element_type not in valid_types:
                issues.append(
                    DiffIssue(
                        path=f"{element_path}.type",
                        severity=Severity.HIGH,
                        message=f"Invalid element type: {element_type}",
                        actual=element_type,
                        expected=f"One of: {', '.join(valid_types)}",
                        suggestion=f"Use valid element type: {', '.join(valid_types)}",
                    )
                )

            # Validate button element
            if element_type == "button":
                button_issues = self._validate_button_element(element, element_path)
                issues.extend(button_issues)

        return issues

    def _validate_button_element(
        self, element: dict, element_path: str
    ) -> list[DiffIssue]:
        """Validate button element."""
        issues = []

        if "text" not in element:
            issues.append(
                DiffIssue(
                    path=f"{element_path}.text",
                    severity=Severity.CRITICAL,
                    message="Button missing required 'text' field",
                    suggestion="Add 'text' field with button label",
                )
            )
        else:
            text_issues = self._validate_text_object(
                element["text"], f"{element_path}.text"
            )
            issues.extend(text_issues)

        # Validate button action
        has_url = "url" in element
        has_action_id = "action_id" in element

        if has_url and has_action_id:
            issues.append(
                DiffIssue(
                    path=element_path,
                    severity=Severity.MEDIUM,
                    message="Button cannot have both 'url' and 'action_id'",
                    suggestion="Use either 'url' for external links or 'action_id' for interactions",
                )
            )
        elif not has_url and not has_action_id:
            issues.append(
                DiffIssue(
                    path=element_path,
                    severity=Severity.HIGH,
                    message="Button must have either 'url' or 'action_id'",
                    suggestion="Add either 'url' for external links or 'action_id' for interactions",
                )
            )

        return issues

    def _validate_text_object(self, text_obj: dict, text_path: str) -> list[DiffIssue]:
        """Validate text object."""
        issues = []

        if not isinstance(text_obj, dict):
            issues.append(
                DiffIssue(
                    path=text_path,
                    severity=Severity.CRITICAL,
                    message="Text object must be an object",
                    actual=type(text_obj).__name__,
                    expected="object",
                    suggestion="Change to object format: {}",
                )
            )
            return issues

        if "type" not in text_obj:
            issues.append(
                DiffIssue(
                    path=f"{text_path}.type",
                    severity=Severity.CRITICAL,
                    message="Text object missing required 'type' field",
                    suggestion="Add 'type' field with 'plain_text' or 'mrkdwn'",
                )
            )
        else:
            text_type = text_obj["type"]
            if text_type not in ["plain_text", "mrkdwn"]:
                issues.append(
                    DiffIssue(
                        path=f"{text_path}.type",
                        severity=Severity.HIGH,
                        message=f"Invalid text type: {text_type}",
                        actual=text_type,
                        expected="'plain_text' or 'mrkdwn'",
                        suggestion="Use 'plain_text' or 'mrkdwn' for text type",
                    )
                )

        if "text" not in text_obj:
            issues.append(
                DiffIssue(
                    path=f"{text_path}.text",
                    severity=Severity.CRITICAL,
                    message="Text object missing required 'text' field",
                    suggestion="Add 'text' field with string content",
                )
            )
        else:
            text_content = text_obj["text"]
            if not isinstance(text_content, str):
                issues.append(
                    DiffIssue(
                        path=f"{text_path}.text",
                        severity=Severity.HIGH,
                        message="'text' field must be a string",
                        actual=type(text_content).__name__,
                        expected="string",
                        suggestion="Change text field to string value",
                    )
                )
            elif len(text_content) > 3000:
                issues.append(
                    DiffIssue(
                        path=f"{text_path}.text",
                        severity=Severity.MEDIUM,
                        message=f"Text too long: {len(text_content)} characters (max 3000)",
                        actual=str(len(text_content)),
                        expected="≤ 3000",
                        suggestion="Shorten text content to under 3000 characters",
                    )
                )

        return issues

    def _validate_color_field(self, color: Any) -> list[DiffIssue]:
        """Validate color field."""
        issues = []

        if not isinstance(color, str):
            issues.append(
                DiffIssue(
                    path="color",
                    severity=Severity.HIGH,
                    message="Color must be a string",
                    actual=type(color).__name__,
                    expected="string",
                    suggestion="Change color to string format",
                )
            )
            return issues

        if not color.startswith("#"):
            issues.append(
                DiffIssue(
                    path="color",
                    severity=Severity.HIGH,
                    message="Color must start with #",
                    actual=color,
                    expected="Format: #RRGGBB",
                    suggestion="Use hex color format starting with #",
                )
            )

        if len(color) != 7:
            issues.append(
                DiffIssue(
                    path="color",
                    severity=Severity.HIGH,
                    message=f"Color must be 7 characters, got {len(color)}",
                    actual=color,
                    expected="#RRGGBB",
                    suggestion="Use 6-digit hex color: #RRGGBB",
                )
            )

        try:
            int(color[1:], 16)
        except ValueError:
            issues.append(
                DiffIssue(
                    path="color",
                    severity=Severity.HIGH,
                    message="Color must be valid hex",
                    actual=color,
                    expected="Valid hex color",
                    suggestion="Use valid hex digits (0-9, A-F)",
                )
            )

        return issues

    def print_report(
        self, issues: list[DiffIssue], show_suggestions: bool = True
    ) -> None:
        """Print formatted diff report."""
        if not issues:
            print("✅ No issues found - payload matches schema!")
            return

        # Group by severity
        severity_groups = {}
        for issue in issues:
            if issue.severity not in severity_groups:
                severity_groups[issue.severity] = []
            severity_groups[issue.severity].append(issue)

        print(f"📊 Schema Diff Report - {len(issues)} issue(s) found\n")

        # Print by severity
        for severity in [
            Severity.CRITICAL,
            Severity.HIGH,
            Severity.MEDIUM,
            Severity.LOW,
            Severity.INFO,
        ]:
            if severity not in severity_groups:
                continue

            emoji = self.severity_colors[severity]
            count = len(severity_groups[severity])
            print(
                f"{emoji} {severity.value.upper()} ({count} issue{'s' if count != 1 else ''}):"
            )

            for issue in severity_groups[severity]:
                print(f"  📍 {issue.path}")
                print(f"     {issue.message}")
                if issue.expected and issue.actual:
                    print(f"     Expected: {issue.expected}")
                    print(f"     Actual: {issue.actual}")
                if show_suggestions and issue.suggestion:
                    print(f"     💡 {issue.suggestion}")
                print()

        # Summary
        critical_count = len(severity_groups.get(Severity.CRITICAL, []))
        high_count = len(severity_groups.get(Severity.HIGH, []))

        if critical_count > 0:
            print(f"🚨 {critical_count} critical issue(s) must be fixed")
        elif high_count > 0:
            print(f"⚠️  {high_count} high-priority issue(s) should be fixed")
        else:
            print("✅ No critical or high-priority issues")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Generate schema diff report")
    parser.add_argument("payload", help="Payload JSON file to analyze")
    parser.add_argument("--schema", help="Schema JSON file (optional)")
    parser.add_argument("--output", help="Output file for report")
    parser.add_argument(
        "--no-suggestions", action="store_true", help="Hide suggestions"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    # Load payload
    try:
        with open(args.payload) as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"❌ Error loading payload: {e}")
        sys.exit(1)

    # Load schema (optional)
    schema = {}
    if args.schema and os.path.exists(args.schema):
        try:
            with open(args.schema) as f:
                schema = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"⚠️  Warning: Could not load schema: {e}")

    # Generate diff report
    reporter = SchemaDiffReporter()
    issues = reporter.compare_payload_to_schema(payload, schema)

    if args.json:
        # Output as JSON
        report_data = {
            "issues": [
                {
                    "path": issue.path,
                    "severity": issue.severity.value,
                    "message": issue.message,
                    "expected": issue.expected,
                    "actual": issue.actual,
                    "suggestion": issue.suggestion,
                }
                for issue in issues
            ],
            "summary": {
                "total_issues": len(issues),
                "critical": len([i for i in issues if i.severity == Severity.CRITICAL]),
                "high": len([i for i in issues if i.severity == Severity.HIGH]),
                "medium": len([i for i in issues if i.severity == Severity.MEDIUM]),
                "low": len([i for i in issues if i.severity == Severity.LOW]),
                "info": len([i for i in issues if i.severity == Severity.INFO]),
            },
        }

        output = json.dumps(report_data, indent=2)
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
        else:
            print(output)
    else:
        # Print formatted report
        if args.output:
            from io import StringIO

            old_stdout = sys.stdout
            sys.stdout = StringIO()
            reporter.print_report(issues, not args.no_suggestions)
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout

            with open(args.output, "w") as f:
                f.write(output)
            print(f"📝 Report saved to: {args.output}")
        else:
            reporter.print_report(issues, not args.no_suggestions)

    # Exit with error code if critical issues found
    critical_issues = [i for i in issues if i.severity == Severity.CRITICAL]
    if critical_issues:
        sys.exit(1)


if __name__ == "__main__":
    main()
