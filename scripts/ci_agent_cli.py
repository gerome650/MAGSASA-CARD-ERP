#!/usr/bin/env python3
"""
CI Intelligence Agent CLI - Developer Interface

A command-line interface for interacting with the CI Intelligence Agent.
Provides quick access to failure analysis, reports, and trends.

Stage 7.1: Self-Healing CI Intelligence Agent

Usage:
    python scripts/ci_agent_cli.py --analyze-latest
    python scripts/ci_agent_cli.py --generate-report
    python scripts/ci_agent_cli.py --show-trends
    python scripts/ci_agent_cli.py --stats
"""

import sys
import os
import json
import sqlite3
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timedelta
from tabulate import tabulate


class CIAgentCLI:
    """Command-line interface for CI Intelligence Agent."""
    
    def __init__(self, db_path: str = "ci_failure_history.db"):
        """Initialize CLI with database connection."""
        self.db_path = Path(db_path)
        self.conn = None
        
        if self.db_path.exists():
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row
    
    def analyze_latest(self):
        """Analyze the latest CI run."""
        print("🔍 Analyzing latest CI run...\n")
        
        try:
            # Get latest workflow run
            result = subprocess.run(
                ['gh', 'run', 'list', '--limit', '1', '--json', 'databaseId,status,conclusion'],
                capture_output=True,
                text=True,
                check=True
            )
            
            runs = json.loads(result.stdout)
            if not runs:
                print("❌ No recent CI runs found")
                return
            
            run = runs[0]
            run_id = run['databaseId']
            status = run['status']
            conclusion = run['conclusion']
            
            print(f"Latest Run: #{run_id}")
            print(f"Status: {status}")
            print(f"Conclusion: {conclusion}\n")
            
            if conclusion == 'failure':
                print("⚠️ Run failed - initiating analysis...\n")
                
                # Run analyzer
                subprocess.run([
                    sys.executable,
                    'scripts/analyze_ci_failure.py',
                    '--workflow-run-id', str(run_id),
                    '--json-output', 'latest-failure-analysis.json',
                    '--markdown-output', 'latest-failure-analysis.md'
                ])
                
                print("\n✅ Analysis complete!")
                print("📄 JSON: latest-failure-analysis.json")
                print("📄 Markdown: latest-failure-analysis.md")
                
            else:
                print("✅ Latest run passed - no analysis needed")
        
        except subprocess.CalledProcessError as e:
            print(f"❌ Error: {e}")
            print("ℹ️ Make sure GitHub CLI (gh) is installed and authenticated")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def generate_report(self, days: int = 7):
        """Generate intelligence report."""
        print(f"📊 Generating intelligence report for last {days} days...\n")
        
        if not self.db_path.exists():
            print("❌ No history database found")
            print("ℹ️ Run some CI analyses first to populate the database")
            return
        
        try:
            # Ensure reports directory exists
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            
            output_file = reports_dir / "CI_WEEKLY_INTELLIGENCE.md"
            
            subprocess.run([
                sys.executable,
                'scripts/generate_ci_intelligence_report.py',
                '--days', str(days),
                '--output', str(output_file)
            ], check=True)
            
            print(f"✅ Report generated: {output_file}\n")
            
            # Show preview
            print("=" * 60)
            with open(output_file, 'r') as f:
                lines = f.readlines()[:30]  # Show first 30 lines
                print("".join(lines))
                if len(lines) >= 30:
                    print("\n... (see full report in file)")
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Error generating report: {e}")
    
    def show_trends(self, days: int = 7):
        """Show top 3 failure categories with trend arrows."""
        print(f"📈 Failure Trends (Last {days} days)\n")
        
        if not self.conn:
            print("❌ No history database found")
            return
        
        try:
            cursor = self.conn.cursor()
            since_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get top categories
            cursor.execute('''
                SELECT 
                    category,
                    COUNT(*) as occurrences
                FROM failures
                WHERE timestamp >= ?
                GROUP BY category
                ORDER BY occurrences DESC
                LIMIT 3
            ''', (since_date,))
            
            trends = []
            for row in cursor.fetchall():
                category = row['category']
                occurrences = row['occurrences']
                
                # Calculate trend
                trend = self._calculate_trend(category, since_date)
                trend_arrow = self._get_trend_arrow(trend)
                
                trends.append({
                    'Category': category.title(),
                    'Occurrences': occurrences,
                    'Trend': f"{trend_arrow} {trend.title()}"
                })
            
            if trends:
                print(tabulate(trends, headers='keys', tablefmt='grid'))
            else:
                print("ℹ️ No failure data available")
        
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_stats(self):
        """Show overall statistics."""
        print("📊 CI Intelligence Statistics\n")
        
        if not self.conn:
            print("❌ No history database found")
            return
        
        try:
            cursor = self.conn.cursor()
            
            # Total failures
            cursor.execute('SELECT COUNT(*) as total FROM failures')
            total_failures = cursor.fetchone()['total']
            
            # Total fix attempts
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
                FROM fix_attempts
            ''')
            fix_row = cursor.fetchone()
            total_attempts = fix_row['total']
            successful_attempts = fix_row['successful'] or 0
            
            # Categories
            cursor.execute('SELECT COUNT(DISTINCT category) as count FROM failures')
            unique_categories = cursor.fetchone()['count']
            
            # Date range
            cursor.execute('SELECT MIN(timestamp) as first, MAX(timestamp) as last FROM failures')
            date_row = cursor.fetchone()
            first_date = date_row['first']
            last_date = date_row['last']
            
            # Display stats
            stats = [
                ['Total Failures Tracked', total_failures],
                ['Unique Failure Categories', unique_categories],
                ['Total Fix Attempts', total_attempts],
                ['Successful Fixes', successful_attempts],
                ['Overall Success Rate', f"{(successful_attempts/total_attempts*100):.1f}%" if total_attempts > 0 else "N/A"],
                ['Data Range', f"{first_date[:10] if first_date else 'N/A'} to {last_date[:10] if last_date else 'N/A'}"]
            ]
            
            print(tabulate(stats, headers=['Metric', 'Value'], tablefmt='grid'))
            print()
            
            # Top categories all-time
            print("📊 Top 5 Failure Categories (All Time):\n")
            cursor.execute('''
                SELECT 
                    category,
                    COUNT(*) as count
                FROM failures
                GROUP BY category
                ORDER BY count DESC
                LIMIT 5
            ''')
            
            top_cats = []
            for i, row in enumerate(cursor.fetchall(), 1):
                top_cats.append([i, row['category'].title(), row['count']])
            
            print(tabulate(top_cats, headers=['#', 'Category', 'Count'], tablefmt='simple'))
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_recent_fixes(self, limit: int = 10):
        """Show recent fix attempts."""
        print(f"🔧 Recent Fix Attempts (Last {limit})\n")
        
        if not self.conn:
            print("❌ No history database found")
            return
        
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('''
                SELECT 
                    fa.timestamp,
                    fa.fix_strategy,
                    fa.success,
                    fa.resolution_time_minutes,
                    f.category
                FROM fix_attempts fa
                LEFT JOIN failures f ON fa.failure_id = f.id
                ORDER BY fa.timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            fixes = []
            for row in cursor.fetchall():
                timestamp = row['timestamp'][:19] if row['timestamp'] else 'N/A'
                strategy = row['fix_strategy'] or 'N/A'
                success = "✅ Success" if row['success'] else "❌ Failed"
                time_taken = f"{row['resolution_time_minutes']:.1f}min" if row['resolution_time_minutes'] else 'N/A'
                category = row['category'] or 'N/A'
                
                fixes.append([
                    timestamp,
                    category.title(),
                    strategy,
                    success,
                    time_taken
                ])
            
            if fixes:
                print(tabulate(fixes, 
                             headers=['Timestamp', 'Category', 'Strategy', 'Result', 'Time'],
                             tablefmt='grid'))
            else:
                print("ℹ️ No fix attempts recorded")
        
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def _calculate_trend(self, category: str, since_date: str) -> str:
        """Calculate trend for a category."""
        cursor = self.conn.cursor()
        
        since_dt = datetime.fromisoformat(since_date)
        mid_point = since_dt + (datetime.now() - since_dt) / 2
        mid_point_str = mid_point.isoformat()
        
        # First half
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM failures
            WHERE category = ? AND timestamp >= ? AND timestamp < ?
        ''', (category, since_date, mid_point_str))
        first_half = cursor.fetchone()['count']
        
        # Second half
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM failures
            WHERE category = ? AND timestamp >= ?
        ''', (category, mid_point_str))
        second_half = cursor.fetchone()['count']
        
        if second_half > first_half * 1.3:
            return "rising"
        elif second_half < first_half * 0.7:
            return "improving"
        else:
            return "stable"
    
    def _get_trend_arrow(self, trend: str) -> str:
        """Get arrow for trend."""
        arrows = {
            'rising': '🔥',
            'improving': '📉',
            'stable': '📊'
        }
        return arrows.get(trend, '→')
    
    def sync_to_notion(self, include_roadmap: bool = False, milestone: str = None):
        """Sync CI report and roadmap to Notion."""
        print("📤 Syncing to Notion...\n")
        
        try:
            # Check if sync script exists
            sync_script = Path("scripts/sync_ci_report_to_notion.py")
            if not sync_script.exists():
                print("❌ Sync script not found: scripts/sync_ci_report_to_notion.py")
                return
            
            # Build command
            cmd = [
                sys.executable,
                str(sync_script),
                "--sync-notion",
                "--report", "reports/CI_WEEKLY_INTELLIGENCE.md"
            ]
            
            if include_roadmap:
                cmd.extend(["--include-roadmap"])
                if milestone:
                    cmd.extend(["--milestone", milestone])
                else:
                    # Extract milestone from current branch or environment
                    milestone = self._detect_current_milestone()
                    if milestone:
                        cmd.extend(["--milestone", milestone])
            
            # Run sync
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(result.stdout)
            
            if result.stderr:
                print(f"⚠️ Warnings: {result.stderr}")
            
            print("✅ Notion sync completed successfully!")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Sync failed: {e}")
            if e.stdout:
                print(f"Output: {e.stdout}")
            if e.stderr:
                print(f"Error: {e.stderr}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_roadmap_status(self):
        """Show roadmap status from Notion."""
        print("🗺️ Engineering Roadmap Status\n")
        
        try:
            sync_script = Path("scripts/sync_ci_report_to_notion.py")
            if not sync_script.exists():
                print("❌ Sync script not found: scripts/sync_ci_report_to_notion.py")
                return
            
            result = subprocess.run([
                sys.executable,
                str(sync_script),
                "--roadmap-status"
            ], capture_output=True, text=True, check=True)
            
            print(result.stdout)
            
            if result.stderr:
                print(f"⚠️ Warnings: {result.stderr}")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to fetch roadmap status: {e}")
            if e.stdout:
                print(f"Output: {e.stdout}")
            if e.stderr:
                print(f"Error: {e.stderr}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def _detect_current_milestone(self) -> str:
        """Detect current milestone from git branch or environment."""
        try:
            # Try to get branch name
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True,
                text=True,
                check=True
            )
            branch = result.stdout.strip()
            
            # Extract milestone from branch name (e.g., feature/stage-7-3)
            if 'stage' in branch.lower():
                # Convert "stage-7-3" to "Stage 7.3"
                import re
                match = re.search(r'stage-?(\d+)-?(\d+)', branch.lower())
                if match:
                    major = match.group(1)
                    minor = match.group(2) if match.group(2) else "0"
                    return f"Stage {major}.{minor}"
            
            return "Stage 7.3"  # Default fallback
            
        except Exception:
            return "Stage 7.3"  # Default fallback
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CI Intelligence Agent - Developer CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze latest CI run
  python scripts/ci_agent_cli.py --analyze-latest
  
  # Generate weekly report
  python scripts/ci_agent_cli.py --generate-report
  
  # Show failure trends
  python scripts/ci_agent_cli.py --show-trends
  
  # Show overall statistics
  python scripts/ci_agent_cli.py --stats
  
  # Show recent fix attempts
  python scripts/ci_agent_cli.py --recent-fixes
  
  # Sync to Notion
  python scripts/ci_agent_cli.py --sync-notion
  
  # Sync with roadmap
  python scripts/ci_agent_cli.py --sync-roadmap --milestone "Stage 7.3"
  
  # Show roadmap status
  python scripts/ci_agent_cli.py --roadmap-status
        """
    )
    
    parser.add_argument(
        '--analyze-latest',
        action='store_true',
        help='Analyze the latest CI run'
    )
    parser.add_argument(
        '--generate-report',
        action='store_true',
        help='Generate intelligence report'
    )
    parser.add_argument(
        '--show-trends',
        action='store_true',
        help='Show top 3 failure categories with trends'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show overall statistics'
    )
    parser.add_argument(
        '--recent-fixes',
        action='store_true',
        help='Show recent fix attempts'
    )
    parser.add_argument(
        '--sync-notion',
        action='store_true',
        help='Sync CI report to Notion'
    )
    parser.add_argument(
        '--sync-roadmap',
        action='store_true',
        help='Sync roadmap milestone to Notion'
    )
    parser.add_argument(
        '--roadmap-status',
        action='store_true',
        help='Show roadmap status from Notion'
    )
    parser.add_argument(
        '--milestone',
        help='Milestone name for roadmap sync'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days for analysis (default: 7)'
    )
    parser.add_argument(
        '--db-path',
        default='ci_failure_history.db',
        help='Path to history database'
    )
    
    args = parser.parse_args()
    
    # If no action specified, show help
    if not any([args.analyze_latest, args.generate_report, args.show_trends, 
                args.stats, args.recent_fixes, args.sync_notion, 
                args.sync_roadmap, args.roadmap_status]):
        parser.print_help()
        sys.exit(0)
    
    cli = CIAgentCLI(db_path=args.db_path)
    
    try:
        if args.analyze_latest:
            cli.analyze_latest()
        
        if args.generate_report:
            cli.generate_report(days=args.days)
        
        if args.show_trends:
            cli.show_trends(days=args.days)
        
        if args.stats:
            cli.show_stats()
        
        if args.recent_fixes:
            cli.show_recent_fixes()
        
        if args.sync_notion:
            cli.sync_to_notion()
        
        if args.sync_roadmap:
            cli.sync_to_notion(include_roadmap=True, milestone=args.milestone)
        
        if args.roadmap_status:
            cli.show_roadmap_status()
    
    finally:
        cli.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Bye!")
        sys.exit(0)

