#!/usr/bin/env python3
"""
🎯 Governance Drift Dashboard Generator

Analyzes governance-history.json to generate visual dashboards and reports showing:
- Uptime trends over time
- Latency performance
- Drift event detection
- Anomaly summaries

Outputs:
- governance-drift-dashboard.md  (Markdown report)
- governance-drift-dashboard.html (HTML dashboard with embedded charts)

Usage:
    python scripts/qa/gov_drift_dashboard.py

Requirements:
    - matplotlib (for plotting)
    - governance-history.json (input file)

FUTURE ENHANCEMENTS:
- Add rolling averages for smoothed trend lines
- Add SLA comparison and compliance percentage
- Add GitHub Pages auto-publish support
- Add configurable time window filtering
- Add anomaly prediction using basic ML
"""

import base64
import json
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-GUI backend for CI compatibility
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️  matplotlib not available, charts will be skipped", file=sys.stderr)


class GovernanceDriftDashboard:
    """Generates drift dashboard from governance history."""

    HISTORY_FILE = "governance-history.json"
    OUTPUT_MD = "governance-drift-dashboard.md"
    OUTPUT_HTML = "governance-drift-dashboard.html"
    
    # Thresholds for anomaly detection
    UPTIME_WARN = 99.0
    UPTIME_FAIL = 98.0
    LATENCY_WARN = 2500
    LATENCY_FAIL = 4000
    DRIFT_WARNING_THRESHOLD = 20.0  # Drift ratio % for warning

    def __init__(self, history_file: str = None, workspace: Path = None):
        """Initialize dashboard generator."""
        self.workspace = workspace or Path.cwd()
        self.history_file = Path(history_file) if history_file else self.workspace / self.HISTORY_FILE
        self.data: List[Dict[str, Any]] = []
        self.stats: Dict[str, Any] = {}
        
    def load_history(self) -> bool:
        """Load and validate governance history file."""
        if not self.history_file.exists():
            print(f"❌ Error: History file not found: {self.history_file}", file=sys.stderr)
            print("\n💡 Tip: Run the governance-heartbeat workflow to generate history data.", file=sys.stderr)
            return False
        
        try:
            with open(self.history_file, 'r') as f:
                self.data = json.load(f)
            
            if not self.data:
                print(f"⚠️  Warning: History file is empty: {self.history_file}", file=sys.stderr)
                return False
            
            print(f"✅ Loaded {len(self.data)} heartbeat records from {self.history_file}")
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON in history file: {e}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"❌ Error loading history file: {e}", file=sys.stderr)
            return False
    
    def calculate_statistics(self):
        """Calculate summary statistics from history data."""
        total_records = len(self.data)
        healthy_count = sum(1 for record in self.data if record.get("status") == "healthy")
        drift_count = sum(1 for record in self.data if record.get("status") == "drift-detected")
        
        # Extract numeric values (filter out "unavailable")
        uptimes = [
            float(r["uptime"]) for r in self.data 
            if r.get("uptime") not in ["unavailable", None, ""]
        ]
        latencies = [
            float(r["latency"]) for r in self.data 
            if r.get("latency") not in ["unavailable", None, ""]
        ]
        error_rates = [
            float(r["error_rate"]) for r in self.data 
            if r.get("error_rate") not in ["unavailable", None, ""]
        ]
        
        # Calculate averages
        avg_uptime = sum(uptimes) / len(uptimes) if uptimes else 0
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        avg_error_rate = sum(error_rates) / len(error_rates) if error_rates else 0
        
        # Get anomalies (drift events)
        anomalies = [
            r for r in self.data 
            if r.get("status") == "drift-detected"
        ]
        last_anomalies = anomalies[-5:] if len(anomalies) >= 5 else anomalies
        
        # Calculate drift percentage
        drift_percentage = (drift_count / total_records * 100) if total_records > 0 else 0
        
        self.stats = {
            "total_records": total_records,
            "healthy_count": healthy_count,
            "drift_count": drift_count,
            "drift_percentage": drift_percentage,
            "avg_uptime": avg_uptime,
            "avg_latency": avg_latency,
            "avg_error_rate": avg_error_rate,
            "min_uptime": min(uptimes) if uptimes else 0,
            "max_uptime": max(uptimes) if uptimes else 0,
            "min_latency": min(latencies) if latencies else 0,
            "max_latency": max(latencies) if latencies else 0,
            "last_anomalies": last_anomalies,
            "uptimes": uptimes,
            "latencies": latencies,
            "error_rates": error_rates,
        }
        
        print(f"📊 Statistics calculated:")
        print(f"   Total heartbeats: {total_records}")
        print(f"   Healthy: {healthy_count} ({healthy_count/total_records*100:.1f}%)")
        print(f"   Drift detected: {drift_count} ({drift_percentage:.1f}%)")
        print(f"   Avg uptime: {avg_uptime:.2f}%")
        print(f"   Avg latency: {avg_latency:.0f}ms")
    
    def generate_plots(self) -> Dict[str, str]:
        """Generate matplotlib plots and return as base64 encoded strings."""
        if not MATPLOTLIB_AVAILABLE:
            print("⚠️  Skipping plot generation (matplotlib not available)")
            return {}
        
        plots = {}
        
        # Prepare time series data
        timestamps = []
        uptimes = []
        latencies = []
        drift_timestamps = []
        drift_values = []
        
        for record in self.data:
            try:
                ts = datetime.fromisoformat(record["timestamp"].replace("Z", "+00:00"))
                timestamps.append(ts)
                
                # Uptime
                uptime = record.get("uptime")
                if uptime not in ["unavailable", None, ""]:
                    uptimes.append(float(uptime))
                else:
                    uptimes.append(None)
                
                # Latency and drift markers
                latency = record.get("latency")
                if latency not in ["unavailable", None, ""]:
                    latencies.append(float(latency))
                    
                    # Mark drift events on latency chart
                    if record.get("status") == "drift-detected":
                        drift_timestamps.append(ts)
                        drift_values.append(float(latency))
                else:
                    latencies.append(None)
                    
            except (ValueError, KeyError) as e:
                print(f"⚠️  Skipping malformed record: {e}", file=sys.stderr)
                continue
        
        # Plot 1: Uptime over time
        if timestamps and any(u is not None for u in uptimes):
            fig, ax = plt.subplots(figsize=(12, 5))
            
            # Filter out None values
            valid_timestamps = [t for t, u in zip(timestamps, uptimes) if u is not None]
            valid_uptimes = [u for u in uptimes if u is not None]
            
            ax.plot(valid_timestamps, valid_uptimes, 'b-', linewidth=2, label='Uptime')
            ax.axhline(y=self.UPTIME_WARN, color='orange', linestyle='--', label=f'Warning ({self.UPTIME_WARN}%)')
            ax.axhline(y=self.UPTIME_FAIL, color='red', linestyle='--', label=f'Critical ({self.UPTIME_FAIL}%)')
            
            ax.set_xlabel('Time', fontsize=12)
            ax.set_ylabel('Uptime (%)', fontsize=12)
            ax.set_title('📈 Governance Uptime Trend', fontsize=14, fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            plots['uptime'] = self._fig_to_base64(fig)
            plt.close(fig)
        
        # Plot 2: Latency trend with drift markers
        if timestamps and any(lat is not None for lat in latencies):
            fig, ax = plt.subplots(figsize=(12, 5))
            
            # Filter out None values
            valid_timestamps = [t for t, lat in zip(timestamps, latencies) if lat is not None]
            valid_latencies = [lat for lat in latencies if lat is not None]
            
            ax.plot(valid_timestamps, valid_latencies, 'g-', linewidth=2, label='Latency')
            
            # Add drift markers
            if drift_timestamps and drift_values:
                ax.scatter(drift_timestamps, drift_values, color='red', s=100, zorder=5, 
                          marker='o', label='Drift Event', edgecolors='darkred', linewidths=2)
            
            ax.axhline(y=self.LATENCY_WARN, color='orange', linestyle='--', label=f'Warning ({self.LATENCY_WARN}ms)')
            ax.axhline(y=self.LATENCY_FAIL, color='red', linestyle='--', label=f'Critical ({self.LATENCY_FAIL}ms)')
            
            ax.set_xlabel('Time', fontsize=12)
            ax.set_ylabel('Latency (ms)', fontsize=12)
            ax.set_title('🐢 Governance Latency Trend (with Drift Events)', fontsize=14, fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            plots['latency'] = self._fig_to_base64(fig)
            plt.close(fig)
        
        # Plot 3: Status distribution pie chart
        fig, ax = plt.subplots(figsize=(8, 6))
        
        labels = ['Healthy', 'Drift Detected']
        sizes = [self.stats['healthy_count'], self.stats['drift_count']]
        colors = ['#4CAF50', '#FF5252']
        explode = (0, 0.1)  # Explode drift slice
        
        ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
               shadow=True, startangle=90, textprops={'fontsize': 12})
        ax.set_title('🥧 Governance Health Status Distribution', fontsize=14, fontweight='bold')
        
        plots['distribution'] = self._fig_to_base64(fig)
        plt.close(fig)
        
        print(f"✅ Generated {len(plots)} plots")
        return plots
    
    def _fig_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 string."""
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        return img_base64
    
    def generate_markdown_report(self, plots: Dict[str, str]):
        """Generate Markdown report."""
        output_path = self.workspace / self.OUTPUT_MD
        
        # Format last update time
        if self.data:
            last_timestamp = self.data[-1].get("timestamp", "Unknown")
            try:
                last_dt = datetime.fromisoformat(last_timestamp.replace("Z", "+00:00"))
                last_update = last_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            except:
                last_update = last_timestamp
        else:
            last_update = "No data"
        
        # Build markdown content
        md_content = f"""# 🎯 Governance Drift Dashboard

**Generated:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}  
**Last Heartbeat:** {last_update}  
**Data Source:** `{self.history_file.name}`

---

## 📊 Summary Metrics

| Metric | Value |
|--------|-------|
| **Total Heartbeats** | {self.stats['total_records']} |
| **Healthy Runs** | {self.stats['healthy_count']} ({self.stats['healthy_count']/self.stats['total_records']*100:.1f}%) |
| **Drift Detected** | {self.stats['drift_count']} ({self.stats['drift_percentage']:.1f}%) |
| **Average Uptime** | {self.stats['avg_uptime']:.2f}% |
| **Average Latency** | {self.stats['avg_latency']:.0f} ms |
| **Average Error Rate** | {self.stats['avg_error_rate']:.2f}% |
| **Uptime Range** | {self.stats['min_uptime']:.2f}% - {self.stats['max_uptime']:.2f}% |
| **Latency Range** | {self.stats['min_latency']:.0f}ms - {self.stats['max_latency']:.0f}ms |

"""

        # Add drift warning if threshold exceeded
        if self.stats['drift_percentage'] > self.DRIFT_WARNING_THRESHOLD:
            md_content += f"""
---

## ⚠️ DRIFT WARNING

**Alert:** Drift ratio is {self.stats['drift_percentage']:.1f}%, which exceeds the {self.DRIFT_WARNING_THRESHOLD}% threshold!

**Recommended Actions:**
1. Review recent governance heartbeat logs
2. Check Render service health and performance
3. Investigate if thresholds need adjustment
4. Verify Slack notification delivery
5. Consider implementing auto-remediation

---

"""

        # Add anomalies table
        md_content += """
## 🚨 Last 5 Anomalies

"""
        if self.stats['last_anomalies']:
            md_content += "| Timestamp | Message |\n"
            md_content += "|-----------|----------|\n"
            
            for anomaly in self.stats['last_anomalies']:
                timestamp = anomaly.get("timestamp", "Unknown")
                message = anomaly.get("message", "No message")
                md_content += f"| `{timestamp}` | {message} |\n"
        else:
            md_content += "✅ No anomalies detected! All heartbeats are healthy.\n"
        
        # Add chart references (if available)
        if plots:
            md_content += """
---

## 📈 Trend Visualizations

"""
            if 'uptime' in plots:
                md_content += "### Uptime Trend\n"
                md_content += "![Uptime Trend](governance-drift-uptime.png)\n\n"
            
            if 'latency' in plots:
                md_content += "### Latency Trend (with Drift Events)\n"
                md_content += "![Latency Trend](governance-drift-latency.png)\n\n"
            
            if 'distribution' in plots:
                md_content += "### Status Distribution\n"
                md_content += "![Status Distribution](governance-drift-distribution.png)\n\n"
            
            md_content += "_Note: For interactive charts, view the HTML dashboard (`governance-drift-dashboard.html`)_\n"
        
        # Add footer
        md_content += """
---

## 🔍 Analysis Tips

### View Full History
```bash
cat governance-history.json | jq '.'
```

### Find All Drift Events
```bash
cat governance-history.json | jq '.[] | select(.status == "drift-detected")'
```

### Calculate Real-Time Drift %
```bash
TOTAL=$(cat governance-history.json | jq '. | length')
DRIFT=$(cat governance-history.json | jq '[.[] | select(.status == "drift-detected")] | length')
echo "Drift: $(echo "scale=2; ($DRIFT * 100) / $TOTAL" | bc)%"
```

---

## 📚 Related Documentation

- [GOVERNANCE_HISTORY_TRACKING.md](docs/GOVERNANCE_HISTORY_TRACKING.md) - History analysis guide
- [GOVERNANCE_HEARTBEAT_ANOMALY_DETECTION.md](GOVERNANCE_HEARTBEAT_ANOMALY_DETECTION.md) - Anomaly detection docs
- [.github/workflows/governance-heartbeat.yml](.github/workflows/governance-heartbeat.yml) - Heartbeat workflow

---

**Generated by:** `scripts/qa/gov_drift_dashboard.py`  
**Dashboard version:** 1.0.0
"""
        
        # Write markdown file
        output_path.write_text(md_content)
        print(f"✅ Markdown report generated: {output_path}")
    
    def generate_html_dashboard(self, plots: Dict[str, str]):
        """Generate HTML dashboard with embedded charts."""
        output_path = self.workspace / self.OUTPUT_HTML
        
        # Format last update time
        if self.data:
            last_timestamp = self.data[-1].get("timestamp", "Unknown")
            try:
                last_dt = datetime.fromisoformat(last_timestamp.replace("Z", "+00:00"))
                last_update = last_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            except:
                last_update = last_timestamp
        else:
            last_update = "No data"
        
        # Build HTML content
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Governance Drift Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .metric-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .metric-card h3 {{
            color: #667eea;
            font-size: 0.9em;
            text-transform: uppercase;
            margin-bottom: 10px;
        }}
        .metric-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}
        .warning-box {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 8px;
        }}
        .warning-box h3 {{
            color: #856404;
            margin-bottom: 10px;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        table th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        table td {{
            padding: 12px;
            border-bottom: 1px solid #ddd;
        }}
        table tr:hover {{
            background: #f8f9fa;
        }}
        .chart {{
            margin: 30px 0;
            text-align: center;
        }}
        .chart img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        .badge-success {{
            background: #d4edda;
            color: #155724;
        }}
        .badge-warning {{
            background: #fff3cd;
            color: #856404;
        }}
        .badge-danger {{
            background: #f8d7da;
            color: #721c24;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Governance Drift Dashboard</h1>
            <p>Real-time monitoring and analysis of governance heartbeat metrics</p>
            <p style="margin-top: 10px; font-size: 0.9em;">
                Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")} | 
                Last Heartbeat: {last_update}
            </p>
        </div>
        
        <div class="content">
"""

        # Add drift warning if needed
        if self.stats['drift_percentage'] > self.DRIFT_WARNING_THRESHOLD:
            html_content += f"""
            <div class="warning-box">
                <h3>⚠️ DRIFT WARNING</h3>
                <p><strong>Alert:</strong> Drift ratio is {self.stats['drift_percentage']:.1f}%, which exceeds the {self.DRIFT_WARNING_THRESHOLD}% threshold!</p>
                <p style="margin-top: 10px;"><strong>Action Required:</strong> Review recent governance logs and investigate anomalies.</p>
            </div>
"""

        # Add metrics grid
        html_content += f"""
            <div class="section">
                <h2>📊 Summary Metrics</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <h3>Total Heartbeats</h3>
                        <div class="value">{self.stats['total_records']}</div>
                    </div>
                    <div class="metric-card">
                        <h3>Healthy Runs</h3>
                        <div class="value">
                            {self.stats['healthy_count']}
                            <span class="badge badge-success">{self.stats['healthy_count']/self.stats['total_records']*100:.1f}%</span>
                        </div>
                    </div>
                    <div class="metric-card">
                        <h3>Drift Detected</h3>
                        <div class="value">
                            {self.stats['drift_count']}
                            <span class="badge {'badge-warning' if self.stats['drift_percentage'] <= self.DRIFT_WARNING_THRESHOLD else 'badge-danger'}">{self.stats['drift_percentage']:.1f}%</span>
                        </div>
                    </div>
                    <div class="metric-card">
                        <h3>Average Uptime</h3>
                        <div class="value">{self.stats['avg_uptime']:.2f}%</div>
                    </div>
                    <div class="metric-card">
                        <h3>Average Latency</h3>
                        <div class="value">{self.stats['avg_latency']:.0f} ms</div>
                    </div>
                    <div class="metric-card">
                        <h3>Average Error Rate</h3>
                        <div class="value">{self.stats['avg_error_rate']:.2f}%</div>
                    </div>
                </div>
            </div>
"""

        # Add charts
        if plots:
            html_content += """
            <div class="section">
                <h2>📈 Trend Visualizations</h2>
"""
            if 'uptime' in plots:
                html_content += f"""
                <div class="chart">
                    <h3>Uptime Trend</h3>
                    <img src="data:image/png;base64,{plots['uptime']}" alt="Uptime Trend">
                </div>
"""
            
            if 'latency' in plots:
                html_content += f"""
                <div class="chart">
                    <h3>Latency Trend (with Drift Events)</h3>
                    <img src="data:image/png;base64,{plots['latency']}" alt="Latency Trend">
                </div>
"""
            
            if 'distribution' in plots:
                html_content += f"""
                <div class="chart">
                    <h3>Status Distribution</h3>
                    <img src="data:image/png;base64,{plots['distribution']}" alt="Status Distribution">
                </div>
"""
            
            html_content += """
            </div>
"""

        # Add anomalies table
        html_content += """
            <div class="section">
                <h2>🚨 Last 5 Anomalies</h2>
"""
        if self.stats['last_anomalies']:
            html_content += """
                <table>
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Message</th>
                        </tr>
                    </thead>
                    <tbody>
"""
            for anomaly in self.stats['last_anomalies']:
                timestamp = anomaly.get("timestamp", "Unknown")
                message = anomaly.get("message", "No message")
                html_content += f"""
                        <tr>
                            <td><code>{timestamp}</code></td>
                            <td>{message}</td>
                        </tr>
"""
            html_content += """
                    </tbody>
                </table>
"""
        else:
            html_content += """
                <p>✅ No anomalies detected! All heartbeats are healthy.</p>
"""
        
        html_content += """
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by: <code>scripts/qa/gov_drift_dashboard.py</code> | Dashboard version: 1.0.0</p>
            <p style="margin-top: 5px;">
                📚 <a href="docs/GOVERNANCE_HISTORY_TRACKING.md" style="color: #667eea;">History Tracking Docs</a> | 
                <a href="GOVERNANCE_HEARTBEAT_ANOMALY_DETECTION.md" style="color: #667eea;">Anomaly Detection Docs</a>
            </p>
        </div>
    </div>
</body>
</html>
"""
        
        # Write HTML file
        output_path.write_text(html_content)
        print(f"✅ HTML dashboard generated: {output_path}")
    
    def run(self) -> int:
        """Execute dashboard generation pipeline."""
        print("🎯 Governance Drift Dashboard Generator")
        print("=" * 60)
        
        # Load history
        if not self.load_history():
            return 1
        
        # Calculate statistics
        self.calculate_statistics()
        
        # Generate plots
        plots = self.generate_plots()
        
        # Generate reports
        self.generate_markdown_report(plots)
        self.generate_html_dashboard(plots)
        
        print("=" * 60)
        print("✅ Dashboard generation complete!")
        print(f"\n📄 View reports:")
        print(f"   - Markdown: {self.workspace / self.OUTPUT_MD}")
        print(f"   - HTML:     {self.workspace / self.OUTPUT_HTML}")
        
        # Print drift warning if needed
        if self.stats['drift_percentage'] > self.DRIFT_WARNING_THRESHOLD:
            print(f"\n⚠️  WARNING: Drift ratio ({self.stats['drift_percentage']:.1f}%) exceeds threshold!")
        
        return 0


def main():
    """Main entry point."""
    dashboard = GovernanceDriftDashboard()
    exit_code = dashboard.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

