#!/usr/bin/env python3
"""
Validate Prometheus Alert Rules
Ensures alert rules are syntactically correct and follow best practices.
"""

import sys
import yaml
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple


def validate_alert_rules() -> int:
    """Validate Prometheus alert rules - wrapper for backward compatibility."""
    result = validate_alert_rules_with_results()
    return result['exit_code']


def main():
    """Main entry point with CLI argument support."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate Prometheus alert rules")
    parser.add_argument("--json-output", help="Output results in JSON format to specified file")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress non-error output")
    
    args = parser.parse_args()
    
    # Run validation and capture results
    result_data = validate_alert_rules_with_results()
    exit_code = result_data['exit_code']
    
    # JSON output for CI integration
    if args.json_output:
        with open(args.json_output, 'w') as f:
            json.dump(result_data, f, indent=2)
    
    return exit_code


def validate_alert_rules_with_results() -> Dict[str, Any]:
    """Validate Prometheus alert rules and return detailed results."""
    print("🔍 Validating Prometheus Alert Rules...")
    
    errors: List[str] = []
    warnings: List[str] = []
    
    # Find alert rule files - search more comprehensively
    rule_files = []
    
    # Primary alert rule locations
    primary_paths = [
        Path("observability/alerts/promql_rules.yml"),
        Path("observability/dashboards/alert_rules.yml"),
        Path("observability/alerts/alert_rules.yml"),
        Path("observability/prometheus_rules.yml"),
    ]
    
    # Search for any YAML files in observability/alerts/
    alerts_dir = Path("observability/alerts/")
    if alerts_dir.exists():
        for yaml_file in alerts_dir.glob("*.yml"):
            if yaml_file not in rule_files:
                rule_files.append(yaml_file)
    
    # Add primary paths
    for path in primary_paths:
        if path not in rule_files:
            rule_files.append(path)
    
    for rule_file in rule_files:
        if not rule_file.exists():
            warnings.append(f"Alert rule file not found: {rule_file}")
            continue
        
        print(f"  Checking {rule_file}...")
        
        try:
            with open(rule_file, 'r') as f:
                rules = yaml.safe_load(f)
            
            # Validate structure
            if not isinstance(rules, dict):
                errors.append(f"{rule_file}: Root element must be a dict")
                continue
            
            # Check for groups
            if 'groups' not in rules:
                errors.append(f"{rule_file}: Missing 'groups' key")
                continue
            
            # Validate each group
            for group in rules['groups']:
                if 'name' not in group:
                    errors.append(f"{rule_file}: Group missing 'name' field")
                
                if 'rules' not in group:
                    errors.append(f"{rule_file}: Group '{group.get('name', 'unknown')}' missing 'rules' field")
                    continue
                
                # Validate each rule
                for rule in group['rules']:
                    if 'alert' in rule:
                        # Alerting rule
                        required_fields = ['alert', 'expr']
                        for field in required_fields:
                            if field not in rule:
                                errors.append(
                                    f"{rule_file}: Alert rule missing required field '{field}'"
                                )
                        
                        # Check for labels and annotations
                        if 'labels' not in rule:
                            warnings.append(
                                f"{rule_file}: Alert '{rule.get('alert', 'unknown')}' missing labels"
                            )
                        
                        if 'annotations' not in rule:
                            warnings.append(
                                f"{rule_file}: Alert '{rule.get('alert', 'unknown')}' missing annotations"
                            )
                        
                        # Check for required annotations
                        if 'annotations' in rule:
                            required_annotations = ['summary']
                            for req_ann in required_annotations:
                                if req_ann not in rule['annotations']:
                                    warnings.append(
                                        f"{rule_file}: Alert '{rule.get('alert', 'unknown')}' missing recommended annotation '{req_ann}'"
                                    )
                        
                        # Check for 'for' duration
                        if 'for' not in rule:
                            warnings.append(
                                f"{rule_file}: Alert '{rule.get('alert', 'unknown')}' missing 'for' duration"
                            )
                        
                        # Validate expression syntax (basic check)
                        if 'expr' in rule:
                            expr = rule['expr']
                            if not expr.strip():
                                errors.append(
                                    f"{rule_file}: Alert '{rule.get('alert', 'unknown')}' has empty expression"
                                )
                            elif not any(op in expr for op in ['>', '<', '>=', '<=', '==', '!=']):
                                warnings.append(
                                    f"{rule_file}: Alert '{rule.get('alert', 'unknown')}' expression may be missing comparison operator"
                                )
                    
                    elif 'record' in rule:
                        # Recording rule
                        required_fields = ['record', 'expr']
                        for field in required_fields:
                            if field not in rule:
                                errors.append(
                                    f"{rule_file}: Recording rule missing required field '{field}'"
                                )
            
            print(f"  ✅ {rule_file} is valid")
            
        except yaml.YAMLError as e:
            errors.append(f"{rule_file}: Invalid YAML - {e}")
        except Exception as e:
            errors.append(f"{rule_file}: Validation error - {e}")
    
    # Print summary
    print("\n📊 Validation Summary:")
    print(f"  Files checked: {len([f for f in rule_files if f.exists()])}")
    print(f"  Errors: {len(errors)}")
    print(f"  Warnings: {len(warnings)}")
    
    if errors:
        print("\n❌ Errors found:")
        for error in errors:
            print(f"  - {error}")
    
    if warnings:
        print("\n⚠️ Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not errors:
        print("\n✅ All alert rules are valid!")
        exit_code = 0
    else:
        print("\n❌ Alert rule validation failed!")
        exit_code = 1
    
    return {
        "exit_code": exit_code,
        "errors": errors,
        "warnings": warnings,
        "files_checked": len([f for f in rule_files if f.exists()]),
        "total_files_found": len(rule_files)
    }


if __name__ == "__main__":
    sys.exit(main())
