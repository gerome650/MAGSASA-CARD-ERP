#!/usr/bin/env python3
"""
CI Intelligence Report Generator - Weekly Analytics and Insights

This script generates comprehensive weekly intelligence reports from historical
CI/CD failure and fix data. It provides actionable insights, trends, and
recommendations for continuous improvement.

Stage 7.1: Self-Healing CI Intelligence Agent

Usage:
    python scripts/generate_ci_intelligence_report.py
    python scripts/generate_ci_intelligence_report.py --days 7 --output reports/CI_WEEKLY_INTELLIGENCE.md
"""

import sys
import os
import json
import sqlite3
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter


class CIIntelligenceReportGenerator:
    """Generates intelligent weekly reports from CI failure history."""
    
    def __init__(self, db_path: str = "ci_failure_history.db"):
        """Initialize with database connection."""
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
    
    def generate_report(self, days: int = 7) -> str:
        """Generate a comprehensive intelligence report for the specified period."""
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Gather all analytics
        executive_summary = self._generate_executive_summary(since_date, days)
        top_failures = self._get_top_failure_categories(since_date, limit=5)
        auto_fix_stats = self._get_auto_fix_statistics(since_date)
        mttr_trends = self._get_mttr_trends(since_date)
        daily_breakdown = self._get_daily_breakdown(since_date)
        key_learnings = self._generate_key_learnings(since_date, top_failures, auto_fix_stats)
        recommendations = self._generate_recommendations(top_failures, auto_fix_stats, mttr_trends)
        
        # Build markdown report
        report = self._build_markdown_report(
            days=days,
            executive_summary=executive_summary,
            top_failures=top_failures,
            auto_fix_stats=auto_fix_stats,
            mttr_trends=mttr_trends,
            daily_breakdown=daily_breakdown,
            key_learnings=key_learnings,
            recommendations=recommendations
        )
        
        return report
    
    def _generate_executive_summary(self, since_date: str, days: int) -> Dict[str, Any]:
        """Generate executive summary statistics."""
        cursor = self.conn.cursor()
        
        # Total failures
        cursor.execute('''
            SELECT COUNT(*) as total
            FROM failures
            WHERE timestamp >= ?
        ''', (since_date,))
        total_failures = cursor.fetchone()['total']
        
        # Total fix attempts
        cursor.execute('''
            SELECT 
                COUNT(*) as total_attempts,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
            FROM fix_attempts fa
            JOIN failures f ON fa.failure_id = f.id
            WHERE fa.timestamp >= ?
        ''', (since_date,))
        
        fix_data = cursor.fetchone()
        total_attempts = fix_data['total_attempts'] or 0
        successful_fixes = fix_data['successful'] or 0
        
        auto_fix_rate = (successful_fixes / total_attempts * 100) if total_attempts > 0 else 0
        
        # Average MTTR
        cursor.execute('''
            SELECT AVG(resolution_time_minutes) as avg_mttr
            FROM fix_attempts
            WHERE success = 1 AND timestamp >= ?
        ''', (since_date,))
        
        avg_mttr = cursor.fetchone()['avg_mttr'] or 0.0
        
        # Compare with previous period for trends
        prev_since = (datetime.now() - timedelta(days=days*2)).isoformat()
        prev_until = since_date
        
        cursor.execute('''
            SELECT AVG(resolution_time_minutes) as prev_mttr
            FROM fix_attempts
            WHERE success = 1 AND timestamp >= ? AND timestamp < ?
        ''', (prev_since, prev_until))
        
        prev_mttr = cursor.fetchone()['prev_mttr'] or avg_mttr
        mttr_change = ((avg_mttr - prev_mttr) / prev_mttr * 100) if prev_mttr > 0 else 0
        
        # Top recurring issue
        cursor.execute('''
            SELECT category, error_signature, COUNT(*) as count
            FROM failures
            WHERE timestamp >= ?
            GROUP BY category, error_signature
            ORDER BY count DESC
            LIMIT 1
        ''', (since_date,))
        
        top_issue = cursor.fetchone()
        top_recurring = {
            'category': top_issue['category'] if top_issue else 'N/A',
            'count': top_issue['count'] if top_issue else 0
        }
        
        return {
            'total_failures': total_failures,
            'auto_fix_rate': auto_fix_rate,
            'auto_fix_rate_change': 0,  # TODO: Calculate change
            'avg_mttr': avg_mttr,
            'mttr_change': mttr_change,
            'top_recurring': top_recurring
        }
    
    def _get_top_failure_categories(self, since_date: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top failure categories with trends."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT 
                category,
                COUNT(*) as occurrences,
                AVG(confidence) as avg_confidence
            FROM failures
            WHERE timestamp >= ?
            GROUP BY category
            ORDER BY occurrences DESC
            LIMIT ?
        ''', (since_date, limit))
        
        categories = []
        for row in cursor.fetchall():
            category = row['category']
            occurrences = row['occurrences']
            
            # Get auto-fix rate for this category
            cursor.execute('''
                SELECT 
                    COUNT(*) as attempts,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
                FROM fix_attempts fa
                JOIN failures f ON fa.failure_id = f.id
                WHERE f.category = ? AND fa.timestamp >= ?
            ''', (category, since_date))
            
            fix_data = cursor.fetchone()
            attempts = fix_data['attempts'] or 0
            successful = fix_data['successful'] or 0
            auto_fix_rate = (successful / attempts * 100) if attempts > 0 else 0
            
            # Determine trend
            trend = self._get_category_trend(category, since_date)
            
            categories.append({
                'category': category,
                'occurrences': occurrences,
                'auto_fix_rate': auto_fix_rate,
                'trend': trend
            })
        
        return categories
    
    def _get_category_trend(self, category: str, since_date: str) -> str:
        """Determine if category is rising, improving, or stable."""
        cursor = self.conn.cursor()
        
        since_dt = datetime.fromisoformat(since_date)
        mid_point = since_dt + (datetime.now() - since_dt) / 2
        mid_point_str = mid_point.isoformat()
        
        # Count in first half
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM failures
            WHERE category = ? AND timestamp >= ? AND timestamp < ?
        ''', (category, since_date, mid_point_str))
        first_half = cursor.fetchone()['count']
        
        # Count in second half
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
    
    def _get_auto_fix_statistics(self, since_date: str) -> Dict[str, Any]:
        """Get auto-fix performance statistics."""
        cursor = self.conn.cursor()
        
        # Overall stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_attempts,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                COUNT(DISTINCT fix_strategy) as unique_strategies
            FROM fix_attempts
            WHERE timestamp >= ?
        ''', (since_date,))
        
        overall = cursor.fetchone()
        
        # Top strategies
        cursor.execute('''
            SELECT 
                fix_strategy,
                COUNT(*) as attempts,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                AVG(CASE WHEN success = 1 THEN resolution_time_minutes END) as avg_time
            FROM fix_attempts
            WHERE timestamp >= ?
            GROUP BY fix_strategy
            ORDER BY successful DESC
            LIMIT 5
        ''', (since_date,))
        
        top_strategies = []
        for row in cursor.fetchall():
            attempts = row['attempts']
            successful = row['successful'] or 0
            success_rate = (successful / attempts * 100) if attempts > 0 else 0
            
            top_strategies.append({
                'strategy': row['fix_strategy'],
                'attempts': attempts,
                'successful': successful,
                'success_rate': success_rate,
                'avg_time': row['avg_time'] or 0.0
            })
        
        return {
            'total_attempts': overall['total_attempts'],
            'successful': overall['successful'] or 0,
            'unique_strategies': overall['unique_strategies'],
            'top_strategies': top_strategies
        }
    
    def _get_mttr_trends(self, since_date: str) -> Dict[str, Any]:
        """Get MTTR trends over the period."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT 
                DATE(timestamp) as date,
                AVG(resolution_time_minutes) as avg_mttr,
                COUNT(*) as fixes
            FROM fix_attempts
            WHERE success = 1 AND timestamp >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date
        ''', (since_date,))
        
        daily_mttr = []
        for row in cursor.fetchall():
            daily_mttr.append({
                'date': row['date'],
                'avg_mttr': row['avg_mttr'],
                'fixes': row['fixes']
            })
        
        return {
            'daily_mttr': daily_mttr
        }
    
    def _get_daily_breakdown(self, since_date: str) -> List[Dict[str, Any]]:
        """Get daily failure breakdown."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as failures,
                COUNT(DISTINCT category) as categories
            FROM failures
            WHERE timestamp >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date
        ''', (since_date,))
        
        daily_data = []
        for row in cursor.fetchall():
            daily_data.append({
                'date': row['date'],
                'failures': row['failures'],
                'categories': row['categories']
            })
        
        return daily_data
    
    def _generate_key_learnings(self, since_date: str, top_failures: List[Dict], 
                                auto_fix_stats: Dict) -> List[str]:
        """Generate key learnings from the data."""
        learnings = []
        
        # Top category learning
        if top_failures:
            top_cat = top_failures[0]
            learnings.append(
                f"{top_cat['category'].title()} issues remain the #{len(learnings)+1} failure vector "
                f"with {top_cat['occurrences']} occurrences — consider preventive measures."
            )
        
        # Auto-fix effectiveness
        if auto_fix_stats['total_attempts'] > 0:
            success_rate = (auto_fix_stats['successful'] / auto_fix_stats['total_attempts'] * 100)
            if success_rate > 80:
                learnings.append(
                    f"Auto-fix system performing excellently with {success_rate:.0f}% success rate."
                )
            elif success_rate > 60:
                learnings.append(
                    f"Auto-fix system showing good results at {success_rate:.0f}% — "
                    "room for strategy optimization."
                )
            else:
                learnings.append(
                    f"Auto-fix success rate at {success_rate:.0f}% — "
                    "review and enhance fix strategies."
                )
        
        # Strategy insights
        if auto_fix_stats['top_strategies']:
            best_strategy = auto_fix_stats['top_strategies'][0]
            learnings.append(
                f"Most effective strategy: '{best_strategy['strategy']}' "
                f"({best_strategy['success_rate']:.0f}% success rate)."
            )
        
        # Trend insights
        rising_issues = [f for f in top_failures if f['trend'] == 'rising']
        if rising_issues:
            learnings.append(
                f"⚠️ Rising trend detected in {', '.join([i['category'] for i in rising_issues])} "
                "— monitor closely."
            )
        
        return learnings
    
    def _generate_recommendations(self, top_failures: List[Dict], 
                                 auto_fix_stats: Dict, mttr_trends: Dict) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Failure-based recommendations
        for failure in top_failures:
            if failure['category'] == 'dependency' and failure['occurrences'] > 3:
                recommendations.append(
                    "📦 Implement dependency freeze workflow to prevent version drift issues."
                )
                break
        
        # Auto-fix recommendations
        if auto_fix_stats['total_attempts'] > 0:
            low_success_strategies = [
                s for s in auto_fix_stats['top_strategies'] 
                if s['success_rate'] < 50
            ]
            if low_success_strategies:
                recommendations.append(
                    f"🔧 Review and enhance strategies: {', '.join([s['strategy'] for s in low_success_strategies])}"
                )
        
        # MTTR recommendations
        if mttr_trends['daily_mttr']:
            recent_mttr = mttr_trends['daily_mttr'][-1]['avg_mttr'] if mttr_trends['daily_mttr'] else 0
            if recent_mttr > 5:
                recommendations.append(
                    "⏱️ MTTR increasing — investigate root causes for slower resolutions."
                )
        
        # General recommendations
        recommendations.append(
            "📊 Continue monitoring CI health metrics and failure patterns."
        )
        
        recommendations.append(
            "🧪 Add pre-commit hooks to catch issues earlier in development cycle."
        )
        
        return recommendations
    
    def _build_markdown_report(self, days: int, executive_summary: Dict, 
                              top_failures: List[Dict], auto_fix_stats: Dict,
                              mttr_trends: Dict, daily_breakdown: List[Dict],
                              key_learnings: List[str], recommendations: List[str]) -> str:
        """Build the final markdown report."""
        report_lines = []
        
        # Header
        report_date = datetime.now().strftime("%Y-%m-%d")
        report_lines.append(f"# 🧠 CI Intelligence Weekly Report – {report_date}\n")
        report_lines.append(f"*Analysis Period: Last {days} days*\n")
        
        # Executive Summary
        report_lines.append("## 📊 Executive Summary\n")
        
        es = executive_summary
        fix_rate_trend = "↑" if es['auto_fix_rate_change'] > 0 else "↓" if es['auto_fix_rate_change'] < 0 else "→"
        mttr_trend = "↓" if es['mttr_change'] < 0 else "↑" if es['mttr_change'] > 0 else "→"
        
        report_lines.append(f"- 🛠️ **Auto-fix success rate:** {es['auto_fix_rate']:.0f}% {fix_rate_trend}")
        report_lines.append(f"- 📉 **MTTR:** {es['avg_mttr']:.1f} min ({mttr_trend} {abs(es['mttr_change']):.0f}%)")
        report_lines.append(f"- 🔁 **Top recurring issue:** {es['top_recurring']['category']} – {es['top_recurring']['count']} occurrences")
        report_lines.append(f"- 📈 **Total failures analyzed:** {es['total_failures']}\n")
        
        # Top Failure Categories
        report_lines.append("## 🔥 Top 5 Failure Categories\n")
        report_lines.append("| Category | Occurrences | Auto-Fix Rate | Trend |")
        report_lines.append("|----------|-------------|----------------|--------|")
        
        trend_emojis = {'rising': '📈', 'improving': '📉', 'stable': '📊'}
        for failure in top_failures:
            trend_emoji = trend_emojis.get(failure['trend'], '📊')
            trend_label = failure['trend'].title()
            fix_status = "✅" if failure['auto_fix_rate'] > 50 else "⚠️" if failure['auto_fix_rate'] > 0 else "❌"
            
            report_lines.append(
                f"| {failure['category'].title()} | {failure['occurrences']} | "
                f"{failure['auto_fix_rate']:.0f}% {fix_status} | {trend_emoji} {trend_label} |"
            )
        
        report_lines.append("")
        
        # Key Learnings
        report_lines.append("## 🧠 Key Learnings\n")
        for learning in key_learnings:
            report_lines.append(f"- {learning}")
        report_lines.append("")
        
        # Auto-Fix Highlights
        report_lines.append("## 🚀 Auto-Fix Highlights\n")
        if auto_fix_stats['total_attempts'] > 0:
            report_lines.append(
                f"- ✅ Fixed **{auto_fix_stats['successful']}/{auto_fix_stats['total_attempts']}** "
                f"failures automatically"
            )
            report_lines.append(f"- 🔧 **{auto_fix_stats['unique_strategies']}** unique fix strategies employed")
            
            if auto_fix_stats['top_strategies']:
                report_lines.append("\n**Top Fix Strategies:**\n")
                for i, strategy in enumerate(auto_fix_stats['top_strategies'][:3], 1):
                    report_lines.append(
                        f"{i}. **{strategy['strategy']}**: {strategy['success_rate']:.0f}% success "
                        f"({strategy['successful']}/{strategy['attempts']} attempts, "
                        f"avg {strategy['avg_time']:.1f}min)"
                    )
        else:
            report_lines.append("- ℹ️ No auto-fix attempts recorded in this period")
        
        report_lines.append("")
        
        # Daily Breakdown
        if daily_breakdown:
            report_lines.append("## 📅 Daily Failure Breakdown\n")
            report_lines.append("| Date | Failures | Categories |")
            report_lines.append("|------|----------|------------|")
            for day in daily_breakdown:
                report_lines.append(f"| {day['date']} | {day['failures']} | {day['categories']} |")
            report_lines.append("")
        
        # MTTR Trends
        if mttr_trends['daily_mttr']:
            report_lines.append("## ⏱️ MTTR Trends\n")
            avg_mttr = sum(d['avg_mttr'] for d in mttr_trends['daily_mttr']) / len(mttr_trends['daily_mttr'])
            report_lines.append(f"**Average MTTR:** {avg_mttr:.2f} minutes\n")
            
            report_lines.append("| Date | Avg MTTR (min) | Fixes |")
            report_lines.append("|------|----------------|-------|")
            for trend in mttr_trends['daily_mttr']:
                report_lines.append(f"| {trend['date']} | {trend['avg_mttr']:.2f} | {trend['fixes']} |")
            report_lines.append("")
        
        # Recommendations
        report_lines.append("## 📈 Recommendations\n")
        for i, rec in enumerate(recommendations, 1):
            report_lines.append(f"{i}. {rec}")
        report_lines.append("")
        
        # Footer
        report_lines.append("---\n")
        report_lines.append(f"*Report generated by CI Intelligence Agent v2.0 on {datetime.now().isoformat()}*\n")
        report_lines.append("*For detailed analysis, query the CI failure history database*\n")
        
        return "\n".join(report_lines)
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate CI intelligence reports from historical data"
    )
    parser.add_argument(
        "--days", 
        type=int, 
        default=7, 
        help="Number of days to analyze (default: 7)"
    )
    parser.add_argument(
        "--output", 
        help="Output file path (default: stdout)"
    )
    parser.add_argument(
        "--db-path", 
        default="ci_failure_history.db",
        help="Path to history database"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format instead of markdown"
    )
    
    args = parser.parse_args()
    
    try:
        generator = CIIntelligenceReportGenerator(db_path=args.db_path)
        
        report = generator.generate_report(days=args.days)
        
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report)
            print(f"✅ Report written to {args.output}")
        else:
            print(report)
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        print("ℹ️ Run CI analysis first to populate the history database", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error generating report: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if 'generator' in locals():
            generator.close()


if __name__ == "__main__":
    main()

