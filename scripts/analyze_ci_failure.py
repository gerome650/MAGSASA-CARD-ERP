#!/usr/bin/env python3
"""
CI/CD Failure Analyzer - Intelligent Failure Diagnosis and Auto-Fix Suggestions

This script analyzes CI/CD failure logs and provides intelligent diagnosis,
root cause analysis, and recommended fixes. It can be run standalone or
integrated into GitHub Actions workflows.

Usage:
    python scripts/analyze_ci_failure.py --ci
    python scripts/analyze_ci_failure.py --analyze-latest
    python scripts/analyze_ci_failure.py --job-logs /path/to/logs
"""

import sys
import os
import json
import re
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import yaml


@dataclass
class FailureAnalysis:
    """Structured failure analysis result."""
    category: str
    severity: str
    root_cause: str
    recommended_fix: str
    affected_files: List[str]
    confidence: float
    auto_fixable: bool
    fix_command: Optional[str] = None
    documentation_links: List[str] = None


class CIFailureAnalyzer:
    """Intelligent CI/CD failure analyzer with ML-inspired pattern recognition."""
    
    def __init__(self):
        self.failure_patterns = {
            'dependency': {
                'patterns': [
                    r'ModuleNotFoundError: No module named \'([^\']+)\'',
                    r'ImportError: cannot import name \'([^\']+)\'',
                    r'pip install ([^\s]+)',
                    r'No module named \'([^\']+)\'',
                    r'PackageNotFoundError',
                    r'Could not find a version that satisfies the requirement',
                    r'ERROR: Could not install packages',
                    r'Requirement already satisfied but import fails',
                ],
                'severity': 'high',
                'auto_fixable': True
            },
            'test_assertion': {
                'patterns': [
                    r'AssertionError',
                    r'FAILED.*test_.*\.py',
                    r'assert.*failed',
                    r'Expected.*but got',
                    r'Test.*failed',
                ],
                'severity': 'medium',
                'auto_fixable': False
            },
            'network_timeout': {
                'patterns': [
                    r'ReadTimeoutError',
                    r'ConnectionTimeout',
                    r'HTTPSConnectionPool.*timeout',
                    r'requests\.exceptions\.Timeout',
                    r'Connection timed out',
                    r'504 Gateway Timeout',
                    r'502 Bad Gateway',
                ],
                'severity': 'low',
                'auto_fixable': True
            },
            'missing_file': {
                'patterns': [
                    r'FileNotFoundError: \[Errno 2\] No such file or directory',
                    r'No such file or directory: \'([^\']+)\'',
                    r'Could not find file',
                    r'Missing file:',
                    r'File does not exist',
                ],
                'severity': 'high',
                'auto_fixable': True
            },
            'schema_validation': {
                'patterns': [
                    r'jsonschema\.exceptions\.ValidationError',
                    r'YAMLError',
                    r'Invalid YAML',
                    r'Schema validation failed',
                    r'Invalid configuration',
                    r'ValidationError',
                ],
                'severity': 'medium',
                'auto_fixable': False
            },
            'permission': {
                'patterns': [
                    r'Permission denied',
                    r'Access denied',
                    r'Not enough permissions',
                    r'chmod.*failed',
                    r'Cannot write to',
                ],
                'severity': 'medium',
                'auto_fixable': True
            },
            'disk_space': {
                'patterns': [
                    r'No space left on device',
                    r'Disk full',
                    r'ENOSPC',
                    r'Out of disk space',
                ],
                'severity': 'high',
                'auto_fixable': False
            }
        }
        
        self.fix_strategies = {
            'dependency': {
                'auto_fix': True,
                'fix_template': 'pip install {package}',
                'file_update': 'requirements.txt',
                'command_template': 'echo "{package}" >> requirements.txt'
            },
            'missing_file': {
                'auto_fix': True,
                'fix_template': 'Create missing file: {file}',
                'file_update': None,
                'command_template': None
            },
            'network_timeout': {
                'auto_fix': True,
                'fix_template': 'Retry with increased timeout',
                'file_update': None,
                'command_template': None
            }
        }

    def analyze_logs(self, log_content: str) -> List[FailureAnalysis]:
        """Analyze log content and return structured failure analysis."""
        analyses = []
        
        for category, config in self.failure_patterns.items():
            for pattern in config['patterns']:
                matches = re.finditer(pattern, log_content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    analysis = self._create_analysis(
                        category, config, match, log_content
                    )
                    if analysis:
                        analyses.append(analysis)
        
        return analyses

    def _create_analysis(self, category: str, config: Dict, match: re.Match, log_content: str) -> Optional[FailureAnalysis]:
        """Create a failure analysis from a pattern match."""
        matched_text = match.group(0)
        captured_groups = match.groups()
        
        # Extract context around the match
        start = max(0, match.start() - 200)
        end = min(len(log_content), match.end() + 200)
        context = log_content[start:end]
        
        # Determine root cause and fix
        root_cause, recommended_fix, affected_files, fix_command = self._determine_fix(
            category, matched_text, captured_groups, context
        )
        
        # Calculate confidence based on pattern specificity and context
        confidence = self._calculate_confidence(match, context, category)
        
        return FailureAnalysis(
            category=category,
            severity=config['severity'],
            root_cause=root_cause,
            recommended_fix=recommended_fix,
            affected_files=affected_files,
            confidence=confidence,
            auto_fixable=config.get('auto_fixable', False),
            fix_command=fix_command,
            documentation_links=self._get_documentation_links(category)
        )

    def _determine_fix(self, category: str, matched_text: str, captured_groups: Tuple, context: str) -> Tuple[str, str, List[str], Optional[str]]:
        """Determine the appropriate fix for a failure category."""
        
        if category == 'dependency':
            package = captured_groups[0] if captured_groups else 'unknown-package'
            root_cause = f"Missing or incompatible dependency: {package}"
            recommended_fix = f"Install missing dependency: pip install {package}"
            affected_files = ['requirements.txt', 'observability/observability_requirements.txt']
            fix_command = f'echo "{package}>=1.0.0" >> requirements.txt'
            
        elif category == 'test_assertion':
            root_cause = "Test assertion failed - logic or expectation error"
            recommended_fix = "Review test logic and expected values"
            affected_files = self._extract_test_files(context)
            fix_command = None
            
        elif category == 'network_timeout':
            root_cause = "Network timeout or connection issue"
            recommended_fix = "Retry with exponential backoff or increase timeout"
            affected_files = []
            fix_command = None
            
        elif category == 'missing_file':
            file_path = captured_groups[0] if captured_groups else 'unknown-file'
            root_cause = f"Missing required file: {file_path}"
            recommended_fix = f"Create or restore missing file: {file_path}"
            affected_files = [file_path]
            fix_command = f'touch {file_path}' if file_path != 'unknown-file' else None
            
        elif category == 'schema_validation':
            root_cause = "Configuration or schema validation error"
            recommended_fix = "Fix YAML/JSON syntax or schema compliance"
            affected_files = self._extract_config_files(context)
            fix_command = None
            
        elif category == 'permission':
            root_cause = "Permission denied or access control issue"
            recommended_fix = "Fix file permissions or access rights"
            affected_files = []
            fix_command = "chmod +x scripts/*.py"
            
        elif category == 'disk_space':
            root_cause = "Insufficient disk space"
            recommended_fix = "Clean up disk space or increase storage"
            affected_files = []
            fix_command = None
            
        else:
            root_cause = f"Unknown failure category: {category}"
            recommended_fix = "Manual investigation required"
            affected_files = []
            fix_command = None
        
        return root_cause, recommended_fix, affected_files, fix_command

    def _extract_test_files(self, context: str) -> List[str]:
        """Extract test file paths from context."""
        test_files = []
        test_pattern = r'test_[^/\s]+\.py'
        matches = re.findall(test_pattern, context)
        test_files.extend(matches)
        return test_files

    def _extract_config_files(self, context: str) -> List[str]:
        """Extract configuration file paths from context."""
        config_files = []
        config_patterns = [
            r'[^/\s]+\.yml',
            r'[^/\s]+\.yaml',
            r'[^/\s]+\.json',
            r'requirements\.txt',
            r'config[^/\s]*\.py'
        ]
        
        for pattern in config_patterns:
            matches = re.findall(pattern, context)
            config_files.extend(matches)
        
        return config_files

    def _calculate_confidence(self, match: re.Match, context: str, category: str) -> float:
        """Calculate confidence score for the analysis."""
        base_confidence = 0.7
        
        # Increase confidence for specific patterns
        if 'ModuleNotFoundError' in match.group(0):
            base_confidence += 0.2
        if 'requirements.txt' in context:
            base_confidence += 0.1
        if category in ['dependency', 'missing_file']:
            base_confidence += 0.1
            
        return min(1.0, base_confidence)

    def _get_documentation_links(self, category: str) -> List[str]:
        """Get relevant documentation links for failure category."""
        links = {
            'dependency': [
                'https://pip.pypa.io/en/stable/user_guide/',
                'https://docs.python.org/3/tutorial/modules.html'
            ],
            'test_assertion': [
                'https://docs.pytest.org/en/stable/',
                'https://docs.python.org/3/library/unittest.html'
            ],
            'network_timeout': [
                'https://requests.readthedocs.io/en/latest/user/quickstart/',
                'https://docs.github.com/en/actions/learn-github-actions/understanding-github-actions'
            ],
            'missing_file': [
                'https://docs.github.com/en/actions/learn-github-actions/understanding-github-actions'
            ]
        }
        
        return links.get(category, [])

    def generate_markdown_report(self, analyses: List[FailureAnalysis]) -> str:
        """Generate a markdown report from failure analyses."""
        if not analyses:
            return "## 🎉 No Critical Failures Detected\n\nAll checks passed successfully!"
        
        # Group by category
        categories = {}
        for analysis in analyses:
            if analysis.category not in categories:
                categories[analysis.category] = []
            categories[analysis.category].append(analysis)
        
        report = ["## 🔍 CI/CD Failure Analysis Report\n"]
        report.append(f"**Analysis Time:** {datetime.now().isoformat()}\n")
        
        # Summary
        total_failures = len(analyses)
        auto_fixable = sum(1 for a in analyses if a.auto_fixable)
        
        report.append("### 📊 Summary\n")
        report.append(f"- **Total Failures:** {total_failures}")
        report.append(f"- **Auto-Fixable:** {auto_fixable}")
        report.append(f"- **Categories:** {', '.join(categories.keys())}\n")
        
        # Detailed analysis by category
        for category, category_analyses in categories.items():
            emoji = self._get_category_emoji(category)
            report.append(f"### {emoji} {category.title()} Issues\n")
            
            for i, analysis in enumerate(category_analyses, 1):
                report.append(f"#### {i}. {analysis.root_cause}\n")
                report.append(f"**Severity:** {analysis.severity.upper()}")
                report.append(f"**Confidence:** {analysis.confidence:.1%}")
                report.append(f"**Auto-Fixable:** {'✅ Yes' if analysis.auto_fixable else '❌ No'}\n")
                
                report.append("**Recommended Fix:**")
                report.append(f"```bash\n{analysis.recommended_fix}\n```\n")
                
                if analysis.affected_files:
                    report.append("**Affected Files:**")
                    for file in analysis.affected_files:
                        report.append(f"- `{file}`")
                    report.append("")
                
                if analysis.fix_command:
                    report.append("**Auto-Fix Command:**")
                    report.append(f"```bash\n{analysis.fix_command}\n```\n")
                
                if analysis.documentation_links:
                    report.append("**Documentation:**")
                    for link in analysis.documentation_links:
                        report.append(f"- {link}")
                    report.append("")
        
        # Next Steps
        report.append("### 🚀 Next Steps\n")
        if auto_fixable > 0:
            report.append("1. **Auto-Fix Available:** Consider running the auto-fix job")
            report.append("2. **Review Changes:** Validate auto-fixes before merging")
        
        report.append("3. **Manual Fixes:** Address non-auto-fixable issues")
        report.append("4. **Retry CI:** Push changes to trigger new CI run")
        report.append("5. **Monitor:** Watch for similar failures in future runs\n")
        
        return "\n".join(report)

    def _get_category_emoji(self, category: str) -> str:
        """Get emoji for failure category."""
        emojis = {
            'dependency': '🐍',
            'test_assertion': '🔥',
            'network_timeout': '🌐',
            'missing_file': '📦',
            'schema_validation': '🛠️',
            'permission': '🔒',
            'disk_space': '💾'
        }
        return emojis.get(category, '❓')


def get_job_logs_from_github(workflow_run_id: str, job_name: str = None) -> str:
    """Get job logs from GitHub Actions API."""
    try:
        # Use GitHub CLI if available
        cmd = ['gh', 'run', 'view', workflow_run_id, '--log']
        if job_name:
            cmd.extend(['--job', job_name])
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback: try to read from local file
        log_file = Path(f"ci-logs-{workflow_run_id}.txt")
        if log_file.exists():
            return log_file.read_text()
        return ""


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Analyze CI/CD failures intelligently")
    parser.add_argument("--ci", action="store_true", help="Run in CI mode (non-interactive)")
    parser.add_argument("--analyze-latest", action="store_true", help="Analyze the latest CI run")
    parser.add_argument("--job-logs", help="Path to job log file")
    parser.add_argument("--workflow-run-id", help="GitHub workflow run ID")
    parser.add_argument("--job-name", help="Specific job name to analyze")
    parser.add_argument("--json-output", help="Output results in JSON format")
    parser.add_argument("--markdown-output", help="Output markdown report to file")
    
    args = parser.parse_args()
    
    # Get log content
    log_content = ""
    
    if args.job_logs:
        log_file = Path(args.job_logs)
        if log_file.exists():
            log_content = log_file.read_text()
        else:
            print(f"❌ Log file not found: {log_file}")
            sys.exit(1)
    elif args.workflow_run_id:
        log_content = get_job_logs_from_github(args.workflow_run_id, args.job_name)
    elif args.analyze_latest:
        # Get latest workflow run ID (requires GitHub CLI)
        try:
            result = subprocess.run(['gh', 'run', 'list', '--limit', '1', '--json', 'databaseId'], 
                                  capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            if data:
                latest_run_id = str(data[0]['databaseId'])
                log_content = get_job_logs_from_github(latest_run_id)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ GitHub CLI not available for latest run analysis")
            sys.exit(1)
    else:
        # Read from stdin or default log file
        if not sys.stdin.isatty():
            log_content = sys.stdin.read()
        else:
            print("❌ No log input provided. Use --job-logs, --workflow-run-id, or pipe logs via stdin")
            sys.exit(1)
    
    if not log_content:
        print("❌ No log content to analyze")
        sys.exit(1)
    
    # Analyze logs
    analyzer = CIFailureAnalyzer()
    analyses = analyzer.analyze_logs(log_content)
    
    # Generate outputs
    if args.json_output:
        result = {
            'timestamp': datetime.now().isoformat(),
            'total_failures': len(analyses),
            'auto_fixable_count': sum(1 for a in analyses if a.auto_fixable),
            'categories': list(set(a.category for a in analyses)),
            'analyses': [
                {
                    'category': a.category,
                    'severity': a.severity,
                    'root_cause': a.root_cause,
                    'recommended_fix': a.recommended_fix,
                    'affected_files': a.affected_files,
                    'confidence': a.confidence,
                    'auto_fixable': a.auto_fixable,
                    'fix_command': a.fix_command,
                    'documentation_links': a.documentation_links
                }
                for a in analyses
            ]
        }
        
        with open(args.json_output, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"✅ Analysis results written to {args.json_output}")
    
    # Generate markdown report
    markdown_report = analyzer.generate_markdown_report(analyses)
    
    if args.markdown_output:
        with open(args.markdown_output, 'w') as f:
            f.write(markdown_report)
        print(f"✅ Markdown report written to {args.markdown_output}")
    
    # Print summary
    if not args.ci:
        print("\n" + "="*60)
        print("📊 FAILURE ANALYSIS SUMMARY")
        print("="*60)
        print(markdown_report)
    
    # Exit with appropriate code
    if analyses:
        critical_failures = [a for a in analyses if a.severity == 'high']
        if critical_failures:
            sys.exit(1)  # Critical failures
        else:
            sys.exit(0)  # Non-critical failures
    else:
        sys.exit(0)  # No failures


if __name__ == "__main__":
    main()
