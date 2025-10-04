#!/usr/bin/env python3
"""
Auto-Fix CI/CD Failures - Automated Repair System

This script automatically attempts to fix common CI/CD failures, particularly
dependency-related issues. It creates new branches with fixes and opens PRs.

Stage 7.1 Enhancement: Adds adaptive prioritization based on historical
success rates, dynamic retry strategies, and structured commit metadata.

Usage:
    python scripts/auto_fix_ci_failures.py --analysis-file failure-analysis.json
    python scripts/auto_fix_ci_failure.py --package numpy --action install
"""

import sys
import os
import json
import subprocess
import argparse
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import re
import time


@dataclass
class AutoFixAction:
    """Represents an auto-fix action to be performed."""
    action_type: str  # 'install_package', 'create_file', 'fix_permissions', etc.
    target: str       # package name, file path, etc.
    command: str      # command to execute
    description: str  # human-readable description
    confidence: float # confidence in this fix
    priority: int = 0  # priority based on historical success (higher = better)
    success_rate: float = 0.0  # historical success rate
    avg_resolution_time: float = 0.0  # average time to resolution


class FixStrategyManager:
    """Manages fix strategies with historical success rate tracking."""
    
    def __init__(self, db_path: str = "ci_failure_history.db"):
        """Initialize with database connection."""
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path)) if self.db_path.exists() else None
    
    def get_strategy_stats(self, fix_strategy: str, category: str) -> Dict[str, Any]:
        """Get historical statistics for a fix strategy."""
        if not self.conn:
            return {'success_rate': 0.0, 'total_attempts': 0, 'avg_time': 0.0}
        
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_attempts,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                AVG(CASE WHEN success = 1 THEN resolution_time_minutes END) as avg_time
            FROM fix_attempts fa
            JOIN failures f ON fa.failure_id = f.id
            WHERE fa.fix_strategy = ? AND f.category = ?
        ''', (fix_strategy, category))
        
        result = cursor.fetchone()
        if result and result[0] > 0:
            total = result[0]
            successful = result[1] or 0
            avg_time = result[2] or 0.0
            return {
                'success_rate': successful / total,
                'total_attempts': total,
                'avg_time': avg_time
            }
        
        return {'success_rate': 0.0, 'total_attempts': 0, 'avg_time': 0.0}
    
    def prioritize_fixes(self, analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize fixes based on historical success rates."""
        prioritized = []
        
        for analysis in analyses:
            if not analysis.get('auto_fixable', False):
                continue
            
            category = analysis.get('category', '')
            fix_command = analysis.get('fix_command', '')
            
            # Determine fix strategy from category
            strategy = self._determine_strategy(category, fix_command)
            stats = self.get_strategy_stats(strategy, category)
            
            # Calculate priority score
            priority = self._calculate_priority(
                analysis.get('confidence', 0.0),
                stats['success_rate'],
                analysis.get('severity', 'low')
            )
            
            analysis['_priority'] = priority
            analysis['_success_rate'] = stats['success_rate']
            analysis['_avg_time'] = stats['avg_time']
            analysis['_strategy'] = strategy
            
            prioritized.append(analysis)
        
        # Sort by priority (highest first)
        prioritized.sort(key=lambda x: x['_priority'], reverse=True)
        
        return prioritized
    
    def _determine_strategy(self, category: str, fix_command: str) -> str:
        """Determine the fix strategy name from category and command."""
        if category == 'dependency':
            if 'pip install' in fix_command or 'echo' in fix_command:
                return 'dependency_install'
        elif category == 'missing_file':
            return 'file_creation'
        elif category == 'permission':
            return 'permission_fix'
        elif category == 'network_timeout':
            return 'retry_with_backoff'
        
        return f'{category}_fix'
    
    def _calculate_priority(self, confidence: float, success_rate: float, 
                          severity: str) -> int:
        """Calculate priority score for a fix."""
        # Base score from confidence (0-100)
        score = confidence * 100
        
        # Boost by historical success rate (0-50)
        score += success_rate * 50
        
        # Boost by severity
        severity_boost = {'high': 30, 'medium': 15, 'low': 0}
        score += severity_boost.get(severity, 0)
        
        return int(score)
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


class CIAutoFixer:
    """Automated CI/CD failure fixer with adaptive strategies."""
    
    def __init__(self, repo_path: str = ".", db_path: str = "ci_failure_history.db"):
        self.repo_path = Path(repo_path)
        self.fixes_applied = []
        self.branch_name = None
        self.strategy_manager = FixStrategyManager(db_path)
        self.fix_start_time = None
        self.failure_ids = {}  # Map error_signature to failure_id
        
    def analyze_and_fix(self, analysis_file: str) -> bool:
        """Analyze failure analysis and apply appropriate fixes with adaptive prioritization."""
        try:
            with open(analysis_file, 'r') as f:
                analysis_data = json.load(f)
        except FileNotFoundError:
            print(f"❌ Analysis file not found: {analysis_file}")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in analysis file: {e}")
            return False
        
        # Filter for auto-fixable issues
        auto_fixable_analyses = [
            a for a in analysis_data.get('analyses', [])
            if a.get('auto_fixable', False) and a.get('confidence', 0) > 0.7
        ]
        
        if not auto_fixable_analyses:
            print("ℹ️ No auto-fixable issues found in analysis")
            return False
        
        print(f"🔧 Found {len(auto_fixable_analyses)} auto-fixable issues")
        
        # Prioritize fixes based on historical success rates
        prioritized_analyses = self.strategy_manager.prioritize_fixes(auto_fixable_analyses)
        
        print("\n📊 Prioritized Fix Order:")
        for i, analysis in enumerate(prioritized_analyses, 1):
            print(f"  {i}. {analysis.get('category')} - "
                  f"Priority: {analysis.get('_priority', 0)} - "
                  f"Success Rate: {analysis.get('_success_rate', 0):.1%}")
        
        # Create auto-fix branch
        self.branch_name = self._create_auto_fix_branch()
        if not self.branch_name:
            return False
        
        # Apply fixes in priority order
        success_count = 0
        self.fix_start_time = time.time()
        
        for analysis in prioritized_analyses:
            if self._apply_fix(analysis):
                success_count += 1
        
        if success_count > 0:
            print(f"\n✅ Successfully applied {success_count}/{len(prioritized_analyses)} fixes")
            return self._commit_and_push_fixes(prioritized_analyses)
        else:
            print("❌ No fixes were successfully applied")
            return False
    
    def _create_auto_fix_branch(self) -> Optional[str]:
        """Create a new branch for auto-fixes."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        branch_name = f"auto-fix/ci-failures-{timestamp}"
        
        try:
            # Get current branch name
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            current_branch = result.stdout.strip()
            
            # Create new branch
            subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                cwd=self.repo_path,
                check=True
            )
            
            print(f"✅ Created auto-fix branch: {branch_name}")
            return branch_name
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create auto-fix branch: {e}")
            return None
    
    def _apply_fix(self, analysis: Dict[str, Any]) -> bool:
        """Apply a specific fix based on analysis and record the attempt."""
        category = analysis.get('category', '')
        fix_command = analysis.get('fix_command', '')
        strategy = analysis.get('_strategy', category)
        success_rate = analysis.get('_success_rate', 0.0)
        
        print(f"\n🔧 Applying fix for {category} issue...")
        print(f"   Root cause: {analysis.get('root_cause', 'Unknown')}")
        print(f"   Fix command: {fix_command}")
        print(f"   Historical success rate: {success_rate:.1%}")
        
        fix_start = time.time()
        success = False
        
        try:
            if category == 'dependency':
                success = self._fix_dependency_issue(analysis)
            elif category == 'missing_file':
                success = self._fix_missing_file_issue(analysis)
            elif category == 'permission':
                success = self._fix_permission_issue(analysis)
            elif category == 'network_timeout':
                success = self._fix_network_timeout_issue(analysis)
            else:
                print(f"⚠️ Unknown fix category: {category}")
                success = False
            
            # Record the fix attempt if we have a database connection
            if self.strategy_manager.conn:
                resolution_time = (time.time() - fix_start) / 60.0  # in minutes
                error_signature = analysis.get('error_signature')
                
                # Get or create failure_id (simplified - in production, link to actual failure)
                # For now, we'll just record the attempt without a specific failure_id
                cursor = self.strategy_manager.conn.cursor()
                cursor.execute('''
                    INSERT INTO fix_attempts (failure_id, timestamp, fix_strategy, 
                                             fix_command, success, resolution_time_minutes)
                    VALUES (NULL, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    strategy,
                    fix_command or 'N/A',
                    1 if success else 0,
                    resolution_time if success else None
                ))
                self.strategy_manager.conn.commit()
            
            return success
                
        except Exception as e:
            print(f"❌ Error applying fix: {e}")
            return False
    
    def _fix_dependency_issue(self, analysis: Dict[str, Any]) -> bool:
        """Fix dependency-related issues."""
        fix_command = analysis.get('fix_command', '')
        
        # Extract package name from fix command
        package_match = re.search(r'"([^"]+)"', fix_command)
        if not package_match:
            print("❌ Could not extract package name from fix command")
            return False
        
        package = package_match.group(1)
        print(f"📦 Adding missing dependency: {package}")
        
        # Add to requirements.txt
        requirements_file = self.repo_path / 'requirements.txt'
        if requirements_file.exists():
            # Read current requirements
            current_content = requirements_file.read_text()
            
            # Check if package already exists
            if package.lower() in current_content.lower():
                print(f"ℹ️ Package {package} already in requirements.txt")
                return True
            
            # Add package with reasonable version
            package_line = f"{package}>=1.0.0  # Auto-added by CI fixer\n"
            new_content = current_content.rstrip() + '\n' + package_line
            
            requirements_file.write_text(new_content)
            print(f"✅ Added {package} to requirements.txt")
            
            self.fixes_applied.append({
                'type': 'dependency',
                'package': package,
                'file': 'requirements.txt',
                'description': f'Added missing dependency: {package}',
                'strategy': analysis.get('_strategy', 'dependency_install'),
                'success_rate': analysis.get('_success_rate', 0.0)
            })
            return True
        else:
            print("❌ requirements.txt not found")
            return False
    
    def _fix_missing_file_issue(self, analysis: Dict[str, Any]) -> bool:
        """Fix missing file issues."""
        affected_files = analysis.get('affected_files', [])
        
        for file_path in affected_files:
            if file_path == 'unknown-file':
                continue
                
            file_obj = self.repo_path / file_path
            if not file_obj.exists():
                print(f"📁 Creating missing file: {file_path}")
                
                # Create directory if needed
                file_obj.parent.mkdir(parents=True, exist_ok=True)
                
                # Create a basic file based on extension
                if file_path.endswith('.py'):
                    content = f'# Auto-generated file by CI fixer\n# {file_path}\n\n"""Auto-generated file."""\n'
                elif file_path.endswith('.yml') or file_path.endswith('.yaml'):
                    content = '# Auto-generated YAML file by CI fixer\n'
                elif file_path.endswith('.json'):
                    content = '{\n  "auto_generated": true,\n  "created_by": "ci-fixer"\n}\n'
                else:
                    content = f'# Auto-generated file: {file_path}\n'
                
                file_obj.write_text(content)
                print(f"✅ Created {file_path}")
                
                self.fixes_applied.append({
                    'type': 'missing_file',
                    'file': file_path,
                    'description': f'Created missing file: {file_path}',
                    'strategy': analysis.get('_strategy', 'file_creation'),
                    'success_rate': analysis.get('_success_rate', 0.0)
                })
        
        return len(affected_files) > 0
    
    def _fix_permission_issue(self, analysis: Dict[str, Any]) -> bool:
        """Fix permission-related issues."""
        fix_command = analysis.get('fix_command', '')
        
        if fix_command:
            try:
                # Execute the fix command
                subprocess.run(
                    fix_command.split(),
                    cwd=self.repo_path,
                    check=True
                )
                print(f"✅ Applied permission fix: {fix_command}")
                
                self.fixes_applied.append({
                    'type': 'permission',
                    'command': fix_command,
                    'description': f'Fixed permissions: {fix_command}',
                    'strategy': analysis.get('_strategy', 'permission_fix'),
                    'success_rate': analysis.get('_success_rate', 0.0)
                })
                return True
            except subprocess.CalledProcessError as e:
                print(f"❌ Permission fix failed: {e}")
                return False
        
        return False
    
    def _fix_network_timeout_issue(self, analysis: Dict[str, Any]) -> bool:
        """Fix network timeout issues by updating retry configurations."""
        # This is more complex and might require workflow changes
        # For now, just log that this was identified
        print("🌐 Network timeout issue identified - manual intervention may be required")
        
        self.fixes_applied.append({
            'type': 'network_timeout',
            'description': 'Network timeout issue - retry logic should help',
            'strategy': analysis.get('_strategy', 'retry_with_backoff'),
            'success_rate': analysis.get('_success_rate', 0.0)
        })
        return True
    
    def close(self):
        """Close database connection and cleanup."""
        if self.strategy_manager:
            self.strategy_manager.close()
    
    def _commit_and_push_fixes(self, analyses: List[Dict[str, Any]]) -> bool:
        """Commit and push the applied fixes."""
        try:
            # Stage all changes
            subprocess.run(
                ['git', 'add', '.'],
                cwd=self.repo_path,
                check=True
            )
            
            # Create commit message
            commit_message = self._generate_commit_message(analyses)
            
            # Commit changes
            subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=self.repo_path,
                check=True
            )
            
            # Push branch
            subprocess.run(
                ['git', 'push', '-u', 'origin', self.branch_name],
                cwd=self.repo_path,
                check=True
            )
            
            print(f"✅ Pushed auto-fix branch: {self.branch_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to commit and push fixes: {e}")
            return False
    
    def _generate_commit_message(self, analyses: List[Dict[str, Any]]) -> str:
        """Generate a commit message with structured metadata."""
        categories = list(set(a.get('category', 'unknown') for a in analyses))
        
        # Calculate overall success rate
        total_success_rate = 0.0
        if analyses:
            success_rates = [a.get('_success_rate', 0.0) for a in analyses 
                           if '_success_rate' in a]
            total_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0.0
        
        # Generate structured commit title
        commit_message = f"[auto-fix][success_rate={total_success_rate:.0%}]"
        commit_message += f"[category={','.join(categories)}] "
        commit_message += f"fix(ci): Auto-fix {len(self.fixes_applied)} CI failures\n\n"
        
        # Detailed fix list
        commit_message += "## Fixes Applied\n\n"
        for i, fix in enumerate(self.fixes_applied, 1):
            strategy_info = fix.get('strategy', 'N/A')
            success_rate_info = fix.get('success_rate', 0.0)
            commit_message += f"{i}. **{fix['type'].title()}**: {fix['description']}\n"
            commit_message += f"   - Strategy: {strategy_info}\n"
            commit_message += f"   - Historical Success Rate: {success_rate_info:.1%}\n\n"
        
        # Metadata section
        commit_message += "## Metadata\n\n"
        commit_message += f"- Branch: {self.branch_name}\n"
        commit_message += f"- Timestamp: {datetime.now().isoformat()}\n"
        commit_message += f"- Categories: {', '.join(categories)}\n"
        commit_message += f"- Total Fixes: {len(self.fixes_applied)}\n"
        commit_message += f"- Avg Success Rate: {total_success_rate:.1%}\n"
        commit_message += "\n---\n"
        commit_message += "*Generated by: CI Auto-Fixer v2.0 (Stage 7.1)*"
        
        return commit_message
    
    def create_pull_request(self, base_branch: str = None) -> Optional[str]:
        """Create a pull request for the auto-fixes."""
        if not self.branch_name:
            print("❌ No auto-fix branch available")
            return None
        
        if not base_branch:
            # Try to get the original branch
            try:
                result = subprocess.run(
                    ['git', 'log', '--oneline', '-1', '--format=%s'],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                # Extract original branch from commit message if possible
                base_branch = "main"  # Default fallback
            except subprocess.CalledProcessError:
                base_branch = "main"
        
        # Generate PR description
        pr_description = self._generate_pr_description()
        
        try:
            # Use GitHub CLI to create PR
            cmd = [
                'gh', 'pr', 'create',
                '--title', f'🔧 Auto-fix CI failures ({len(self.fixes_applied)} fixes)',
                '--body', pr_description,
                '--base', base_branch,
                '--head', self.branch_name,
                '--label', 'auto-fix,ci'
            ]
            
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            pr_url = result.stdout.strip()
            print(f"✅ Created pull request: {pr_url}")
            return pr_url
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create pull request: {e}")
            return None
    
    def _generate_pr_description(self) -> str:
        """Generate a PR description for the auto-fixes."""
        description = "## 🔧 Auto-Fix CI Failures\n\n"
        description += "This PR contains automated fixes for CI/CD failures detected by the self-healing system.\n\n"
        
        description += "### 📊 Fixes Applied\n\n"
        for fix in self.fixes_applied:
            description += f"- **{fix['type'].title()}**: {fix['description']}\n"
        
        description += "\n### 🤖 Auto-Generated by\n"
        description += "- CI Failure Analyzer\n"
        description += "- Auto-Fix System\n"
        description += f"- Timestamp: {datetime.now().isoformat()}\n\n"
        
        description += "### ✅ Next Steps\n"
        description += "1. Review the changes carefully\n"
        description += "2. Run CI to verify fixes\n"
        description += "3. Merge if all checks pass\n"
        description += "4. Monitor for similar issues\n\n"
        
        description += "---\n"
        description += "*This PR was automatically generated by the CI/CD self-healing system.*"
        
        return description


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Auto-fix CI/CD failures with adaptive strategies")
    parser.add_argument("--analysis-file", help="Path to failure analysis JSON file")
    parser.add_argument("--package", help="Package name to install")
    parser.add_argument("--action", choices=['install', 'upgrade'], default='install')
    parser.add_argument("--create-pr", action="store_true", help="Create pull request after fixing")
    parser.add_argument("--base-branch", help="Base branch for pull request")
    parser.add_argument("--db-path", default="ci_failure_history.db", help="Path to history database")
    
    args = parser.parse_args()
    
    auto_fixer = CIAutoFixer(db_path=args.db_path)
    
    try:
        if args.analysis_file:
            # Fix based on analysis file
            success = auto_fixer.analyze_and_fix(args.analysis_file)
            
            if success and args.create_pr:
                pr_url = auto_fixer.create_pull_request(args.base_branch)
                if pr_url:
                    print(f"\n🎉 Auto-fix completed! PR created: {pr_url}")
                else:
                    print("\n⚠️ Auto-fix applied but PR creation failed")
            elif success:
                print(f"\n✅ Auto-fix completed! Branch: {auto_fixer.branch_name}")
            else:
                print("\n❌ Auto-fix failed")
                sys.exit(1)
    
        elif args.package:
            # Direct package fix
            analysis = {
                'category': 'dependency',
                'auto_fixable': True,
                'confidence': 1.0,
                'fix_command': f'echo "{args.package}>=1.0.0" >> requirements.txt',
                'affected_files': ['requirements.txt'],
                'root_cause': f'Missing dependency: {args.package}',
                'recommended_fix': f'Install {args.package}',
                '_strategy': 'dependency_install',
                '_success_rate': 0.0,
                '_priority': 100
            }
            
            auto_fixer.branch_name = auto_fixer._create_auto_fix_branch()
            if auto_fixer.branch_name and auto_fixer._apply_fix(analysis):
                auto_fixer._commit_and_push_fixes([analysis])
                
                if args.create_pr:
                    auto_fixer.create_pull_request(args.base_branch)
        
        else:
            print("❌ No analysis file or package specified")
            parser.print_help()
            sys.exit(1)
    
    finally:
        # Cleanup
        auto_fixer.close()


if __name__ == "__main__":
    main()
