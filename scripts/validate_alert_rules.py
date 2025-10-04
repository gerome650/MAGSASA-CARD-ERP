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
Runtime Intelligence: CI Alert Rules Validation
Stage 6.8 - CI script to validate PromQL alert rules and coverage

This script validates:
- PromQL syntax correctness
- Alert rule completeness
- Service coverage requirements
- Best practices compliance
"""

import os
import sys
import yaml
import json
import logging
import argparse
import re
from typing import Dict, List, Set, Tuple, Any
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AlertRuleValidator:
    """Validator for Prometheus alert rules"""
    
    def __init__(self, rules_file: str):
        """
        Initialize the validator.
        
        Args:
            rules_file: Path to the alert rules YAML file
        """
        self.rules_file = rules_file
        self.rules_data = None
        self.validation_results = {
            'syntax_errors': [],
            'coverage_issues': [],
            'best_practice_violations': [],
            'required_alerts_missing': [],
            'warnings': []
        }
        
        # Required alerts for MAGSASA-CARD-ERP
        self.required_alerts = {
            'ServiceDown',
            'CriticalHighErrorRate', 
            'HighRequestLatency',
            'RequestVolumeSpike',
            'HighCPUUsage',
            'HighMemoryUsage',
            'HighDiskUsage'
        }
        
        # Required labels for all alerts
        self.required_labels = {
            'severity',
            'service', 
            'team',
            'category'
        }
        
        # Required annotations for all alerts
        self.required_annotations = {
            'summary',
            'description'
        }
        
        # Best practice patterns
        self.best_practice_patterns = {
            'for_duration': r'for:\s*\d+[smh]',  # Should have 'for' duration
            'runbook_url': r'runbook_url',       # Should have runbook
            'grafana_url': r'grafana_url',       # Should have dashboard link
            'threshold_annotation': r'threshold', # Should specify threshold
        }
    
    def load_rules(self) -> bool:
        """Load and parse the alert rules YAML file"""
        try:
            with open(self.rules_file, 'r') as f:
                self.rules_data = yaml.safe_load(f)
            
            logger.info(f"Loaded alert rules from {self.rules_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load alert rules: {e}")
            self.validation_results['syntax_errors'].append(f"YAML parsing error: {e}")
            return False
    
    def validate_yaml_syntax(self) -> bool:
        """Validate YAML syntax and structure"""
        if not self.rules_data:
            return False
        
        errors = []
        
        # Check for required top-level structure
        if 'groups' not in self.rules_data:
            errors.append("Missing 'groups' section")
        
        if not isinstance(self.rules_data['groups'], list):
            errors.append("'groups' must be a list")
        
        # Validate each group
        for i, group in enumerate(self.rules_data.get('groups', [])):
            group_name = group.get('name', f'group-{i}')
            
            if 'rules' not in group:
                errors.append(f"Group '{group_name}' missing 'rules' section")
                continue
            
            if not isinstance(group['rules'], list):
                errors.append(f"Group '{group_name}' rules must be a list")
                continue
            
            # Validate each rule
            for j, rule in enumerate(group['rules']):
                rule_name = rule.get('alert', f'rule-{j}')
                
                if 'alert' not in rule:
                    errors.append(f"Rule {j} in group '{group_name}' missing 'alert' field")
                
                if 'expr' not in rule:
                    errors.append(f"Rule '{rule_name}' missing 'expr' field")
                
                if 'labels' not in rule:
                    errors.append(f"Rule '{rule_name}' missing 'labels' field")
                
                if 'annotations' not in rule:
                    errors.append(f"Rule '{rule_name}' missing 'annotations' field")
        
        self.validation_results['syntax_errors'].extend(errors)
        return len(errors) == 0
    
    def validate_promql_syntax(self) -> bool:
        """Validate PromQL expressions (basic syntax check)"""
        errors = []
        
        for group in self.rules_data.get('groups', []):
            for rule in group.get('rules', []):
                alert_name = rule.get('alert', 'unknown')
                expr = rule.get('expr', '')
                
                if not expr:
                    continue
                
                # Basic PromQL syntax validation
                if not self._validate_promql_basic(expr):
                    errors.append(f"Rule '{alert_name}' has invalid PromQL syntax: {expr[:100]}...")
        
        self.validation_results['syntax_errors'].extend(errors)
        return len(errors) == 0
    
    def _validate_promql_basic(self, expr: str) -> bool:
        """Basic PromQL syntax validation"""
        # Check for balanced parentheses
        if expr.count('(') != expr.count(')'):
            return False
        
        # Check for balanced braces
        if expr.count('{') != expr.count('}'):
            return False
        
        # Check for balanced brackets
        if expr.count('[') != expr.count(']'):
            return False
        
        # Check for basic PromQL keywords and functions
        valid_patterns = [
            r'\bup\b',
            r'\brate\b',
            r'\bincrease\b',
            r'\bhistogram_quantile\b',
            r'\bavg_over_time\b',
            r'\bsum\b',
            r'\bby\b',
            r'\babsent\b',
            r'\b{.*}\b',
            r'\[.*\]'
        ]
        
        # At least one valid pattern should be present
        for pattern in valid_patterns:
            if re.search(pattern, expr):
                return True
        
        return False
    
    def validate_alert_coverage(self) -> bool:
        """Validate that required alerts are present"""
        issues = []
        
        # Collect all alert names
        present_alerts = set()
        for group in self.rules_data.get('groups', []):
            for rule in group.get('rules', []):
                if 'alert' in rule:
                    present_alerts.add(rule['alert'])
        
        # Check for missing required alerts
        missing_alerts = self.required_alerts - present_alerts
        if missing_alerts:
            issues.append(f"Missing required alerts: {', '.join(missing_alerts)}")
        
        # Check for coverage completeness
        total_alerts = len(present_alerts)
        required_count = len(self.required_alerts)
        coverage_percentage = (len(present_alerts & self.required_alerts) / required_count) * 100
        
        if coverage_percentage < 80:
            issues.append(f"Alert coverage is only {coverage_percentage:.1f}% (minimum: 80%)")
        
        self.validation_results['coverage_issues'].extend(issues)
        return len(issues) == 0
    
    def validate_labels_and_annotations(self) -> bool:
        """Validate that all alerts have required labels and annotations"""
        issues = []
        
        for group in self.rules_data.get('groups', []):
            for rule in group.get('rules', []):
                alert_name = rule.get('alert', 'unknown')
                
                # Check labels
                labels = rule.get('labels', {})
                missing_labels = self.required_labels - set(labels.keys())
                if missing_labels:
                    issues.append(f"Alert '{alert_name}' missing required labels: {', '.join(missing_labels)}")
                
                # Check annotations
                annotations = rule.get('annotations', {})
                missing_annotations = self.required_annotations - set(annotations.keys())
                if missing_annotations:
                    issues.append(f"Alert '{alert_name}' missing required annotations: {', '.join(missing_annotations)}")
        
        self.validation_results['coverage_issues'].extend(issues)
        return len(issues) == 0
    
    def validate_best_practices(self) -> bool:
        """Validate best practices compliance"""
        violations = []
        warnings = []
        
        for group in self.rules_data.get('groups', []):
            group_name = group.get('name', 'unknown')
            
            # Check group has reasonable interval
            interval = group.get('interval', '')
            if not interval:
                violations.append(f"Group '{group_name}' should specify 'interval'")
            elif not re.match(r'\d+[smh]', interval):
                violations.append(f"Group '{group_name}' has invalid interval format: {interval}")
            
            for rule in group.get('rules', []):
                alert_name = rule.get('alert', 'unknown')
                
                # Check for 'for' duration
                if 'for' not in rule:
                    violations.append(f"Alert '{alert_name}' should specify 'for' duration")
                
                # Check for runbook URL
                annotations = rule.get('annotations', {})
                if 'runbook_url' not in annotations:
                    warnings.append(f"Alert '{alert_name}' should include runbook_url annotation")
                
                # Check for Grafana dashboard URL
                if 'grafana_url' not in annotations and 'dashboard_url' not in annotations:
                    warnings.append(f"Alert '{alert_name}' should include grafana_url or dashboard_url annotation")
                
                # Check severity levels
                labels = rule.get('labels', {})
                severity = labels.get('severity', '')
                if severity not in ['critical', 'warning', 'info']:
                    violations.append(f"Alert '{alert_name}' has invalid severity: {severity}")
                
                # Check for threshold annotations where appropriate
                expr = rule.get('expr', '')
                if re.search(r'[><=]\s*\d+', expr) and 'threshold' not in annotations:
                    warnings.append(f"Alert '{alert_name}' should specify threshold in annotations")
        
        self.validation_results['best_practice_violations'].extend(violations)
        self.validation_results['warnings'].extend(warnings)
        return len(violations) == 0
    
    def validate_service_coverage(self, services: List[str]) -> bool:
        """Validate that all services have appropriate alert coverage"""
        issues = []
        
        # This would check if alerts cover all specified services
        # For now, we'll do a basic check
        for service in services:
            service_alerts = []
            for group in self.rules_data.get('groups', []):
                for rule in group.get('rules', []):
                    labels = rule.get('labels', {})
                    if labels.get('service') == service:
                        service_alerts.append(rule.get('alert'))
            
            if len(service_alerts) < 3:  # Minimum 3 alerts per service
                issues.append(f"Service '{service}' has insufficient alert coverage ({len(service_alerts)} alerts)")
        
        self.validation_results['coverage_issues'].extend(issues)
        return len(issues) == 0
    
    def run_validation(self, services: List[str] = None) -> Dict[str, Any]:
        """
        Run complete validation.
        
        Args:
            services: List of services to check coverage for
            
        Returns:
            Validation results dictionary
        """
        logger.info("🔍 Starting alert rules validation...")
        
        # Load and validate rules
        if not self.load_rules():
            return self.validation_results
        
        # Run all validations
        syntax_valid = self.validate_yaml_syntax()
        promql_valid = self.validate_promql_syntax()
        coverage_valid = self.validate_alert_coverage()
        labels_valid = self.validate_labels_and_annotations()
        best_practices_valid = self.validate_best_practices()
        
        if services:
            service_coverage_valid = self.validate_service_coverage(services)
        else:
            service_coverage_valid = True
        
        # Calculate overall status
        all_valid = all([
            syntax_valid,
            promql_valid, 
            coverage_valid,
            labels_valid,
            best_practices_valid,
            service_coverage_valid
        ])
        
        # Generate summary
        total_issues = (
            len(self.validation_results['syntax_errors']) +
            len(self.validation_results['coverage_issues']) +
            len(self.validation_results['best_practice_violations']) +
            len(self.validation_results['required_alerts_missing'])
        )
        
        summary = {
            'validation_passed': all_valid,
            'total_issues': total_issues,
            'warnings': len(self.validation_results['warnings']),
            'syntax_errors': len(self.validation_results['syntax_errors']),
            'coverage_issues': len(self.validation_results['coverage_issues']),
            'best_practice_violations': len(self.validation_results['best_practice_violations']),
            'details': self.validation_results
        }
        
        return summary
    
    def print_results(self, results: Dict[str, Any]):
        """Print validation results in a readable format"""
        print("\n" + "=" * 60)
        print("🚨 ALERT RULES VALIDATION RESULTS")
        print("=" * 60)
        
        if results['validation_passed']:
            print("✅ VALIDATION PASSED - Alert rules are valid")
        else:
            print("❌ VALIDATION FAILED - Issues found in alert rules")
        
        print(f"\n📊 SUMMARY:")
        print(f"  Total Issues: {results['total_issues']}")
        print(f"  Warnings: {results['warnings']}")
        print(f"  Syntax Errors: {results['syntax_errors']}")
        print(f"  Coverage Issues: {results['coverage_issues']}")
        print(f"  Best Practice Violations: {results['best_practice_violations']}")
        
        details = results['details']
        
        if details['syntax_errors']:
            print(f"\n🔴 SYNTAX ERRORS:")
            for error in details['syntax_errors']:
                print(f"  • {error}")
        
        if details['coverage_issues']:
            print(f"\n🟡 COVERAGE ISSUES:")
            for issue in details['coverage_issues']:
                print(f"  • {issue}")
        
        if details['best_practice_violations']:
            print(f"\n🟠 BEST PRACTICE VIOLATIONS:")
            for violation in details['best_practice_violations']:
                print(f"  • {violation}")
        
        if details['warnings']:
            print(f"\n⚠️  WARNINGS:")
            for warning in details['warnings']:
                print(f"  • {warning}")
        
        print("\n" + "=" * 60)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Validate Prometheus alert rules')
    parser.add_argument('rules_file', help='Path to alert rules YAML file')
    parser.add_argument('--services', nargs='+', default=['magsasa-card-erp'],
                       help='Services to check coverage for')
    parser.add_argument('--output', help='Output results to JSON file')
    parser.add_argument('--strict', action='store_true',
                       help='Treat warnings as errors')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate rules file exists
    if not os.path.exists(args.rules_file):
        logger.error(f"Rules file not found: {args.rules_file}")
        sys.exit(1)
    
    # Run validation
    validator = AlertRuleValidator(args.rules_file)
    results = validator.run_validation(args.services)
    
    # Print results
    validator.print_results(results)
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {args.output}")
    
    # Exit with appropriate code
    if args.strict and results['warnings'] > 0:
        logger.error("Validation failed due to warnings in strict mode")
        sys.exit(1)
    elif not results['validation_passed']:
        logger.error("Validation failed due to errors")
        sys.exit(1)
    else:
        logger.info("Validation passed successfully")
        sys.exit(0)


if __name__ == '__main__':
    main()
