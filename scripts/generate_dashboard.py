#!/usr/bin/env python3
"""
Builds a CI dashboard bundle:
 - Reads pytest JSON, coverage.xml, ruff JSON
 - Merges with previous history (if available)
 - Emits JSON data: latest.json, history.json, tests.json, lint.json, coverage.json, meta.json
 - Emits badges JSON for shields.io (tests, lint, coverage, duration, coverage trend)
 - Emits index.html (static, Chart.js via CDN)
"""
from __future__ import annotations
import argparse
import json
import os
import time
from datetime import datetime, timezone
from xml.etree import ElementTree as ET


def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def parse_pytest_json(pytest_json_path: str) -> dict:
    if not os.path.isfile(pytest_json_path):
        return {"passed": 0, "failed": 0, "skipped": 0, "duration": 0.0}
    data = json.loads(read_file(pytest_json_path))
    summary = data.get("summary", {})
    return {
        "passed": int(summary.get("passed", 0) or 0),
        "failed": int(summary.get("failed", 0) or 0),
        "skipped": int(summary.get("skipped", 0) or 0),
        "duration": float(summary.get("duration", 0.0) or 0.0),
    }


def parse_coverage_xml(coverage_xml_path: str) -> dict:
    if not os.path.isfile(coverage_xml_path):
        return {"coverage_percent": 0.0}
    tree = ET.parse(coverage_xml_path)
    root = tree.getroot()
    # Cobertura-style attribute line-rate (0..1)
    line_rate = root.attrib.get("line-rate", "0")
    pct = round(float(line_rate) * 100, 1)
    return {"coverage_percent": pct}


def parse_ruff_json(ruff_json_path: str) -> dict:
    if not os.path.isfile(ruff_json_path):
        return {"issues": 0}
    try:
        arr = json.loads(read_file(ruff_json_path))
        if isinstance(arr, list):
            return {"issues": len(arr)}
        return {"issues": 0}
    except Exception:
        return {"issues": 0}


def load_prev_history(prev_site_dir: str) -> list[dict]:
    path = os.path.join(prev_site_dir or "", "data", "history.json")
    if path and os.path.isfile(path):
        try:
            return json.loads(read_file(path))
        except Exception:
            return []
    return []


def badge_json(label: str, message: str, color: str = "blue") -> dict:
    return {
        "schemaVersion": 1,
        "label": label,
        "message": message,
        "color": color,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pytest-json", required=True)
    ap.add_argument("--coverage-xml", required=True)
    ap.add_argument("--ruff-json", required=True)
    ap.add_argument("--prev-site", default="")  # _site/ci-dashboard
    ap.add_argument("--out", required=True)  # ci-dashboard
    ap.add_argument("--repo", required=True)
    ap.add_argument("--run-url", required=True)
    ap.add_argument("--commit", required=True)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--actor", required=True)
    ap.add_argument("--duration-seconds", required=True)
    ap.add_argument("--duration-pretty", required=True)
    args = ap.parse_args()

    ts = datetime.now(timezone.utc).isoformat()
    pytest_summary = parse_pytest_json(args.pytest_json)
    cov = parse_coverage_xml(args.coverage_xml)
    ruff = parse_ruff_json(args.ruff_json)
    duration_seconds = int(args.duration_seconds)
    duration_pretty = args.duration_pretty

    total = pytest_summary["passed"] + pytest_summary["failed"]
    pass_rate = round((pytest_summary["passed"] / total * 100.0), 1) if total else 0.0

    # Load previous to compute trend
    history = load_prev_history(args.prev_site)
    prev_cov = history[-1]["coverage_percent"] if history else None
    cov_delta = round(cov["coverage_percent"] - (prev_cov or 0.0), 1)
    cov_delta_str = (
        f"{cov['coverage_percent']}% ({'+' if cov_delta>=0 else ''}{cov_delta}%)"
    )

    # latest.json
    latest = {
        "timestamp": ts,
        "repo": args.repo,
        "branch": args.branch,
        "commit": args.commit,
        "actor": args.actor,
        "run_url": args.run_url,
        "tests": pytest_summary,
        "lint": ruff,
        "coverage_percent": cov["coverage_percent"],
        "coverage_delta": cov_delta,
        "pass_rate": pass_rate,
        "ci_duration_seconds": duration_seconds,
        "ci_duration_pretty": duration_pretty,
    }

    out_dir = args.out
    data_dir = os.path.join(out_dir, "data")
    badges_dir = os.path.join(out_dir, "badges")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(badges_dir, exist_ok=True)

    # Write data files
    write_json(os.path.join(data_dir, "latest.json"), latest)
    write_json(os.path.join(data_dir, "tests.json"), pytest_summary)
    write_json(os.path.join(data_dir, "lint.json"), ruff)
    write_json(os.path.join(data_dir, "coverage.json"), cov)
    write_json(
        os.path.join(data_dir, "meta.json"),
        {
            "timestamp": ts,
            "repo": args.repo,
            "branch": args.branch,
            "commit": args.commit,
            "actor": args.actor,
            "run_url": args.run_url,
            "ci_duration_seconds": duration_seconds,
            "ci_duration_pretty": duration_pretty,
        },
    )

    # Update history.json (append one record per run; keep last 200)
    history.append(
        {
            "timestamp": ts,
            "coverage_percent": cov["coverage_percent"],
            "pass_rate": pass_rate,
            "ci_duration_seconds": duration_seconds,
            "lint_issues": ruff["issues"],
            "tests_total": total,
            "tests_passed": pytest_summary["passed"],
            "tests_failed": pytest_summary["failed"],
            "commit": args.commit,
            "branch": args.branch,
        }
    )
    history = history[-200:]
    write_json(os.path.join(data_dir, "history.json"), history)

    # Badges (Shields endpoint JSON)
    # tests
    tests_color = "green" if pytest_summary["failed"] == 0 else "red"
    write_json(
        os.path.join(badges_dir, "test-results-badge.json"),
        badge_json("Tests", f"{pytest_summary['passed']}/{total} passed", tests_color),
    )
    # lint
    lint_color = "green" if ruff["issues"] == 0 else "yellow"
    write_json(
        os.path.join(badges_dir, "lint-status-badge.json"),
        badge_json("Lint", f"{ruff['issues']} issues", lint_color),
    )
    # coverage
    cov_color = (
        "brightgreen"
        if cov["coverage_percent"] >= 90
        else ("yellow" if cov["coverage_percent"] >= 75 else "red")
    )
    write_json(
        os.path.join(badges_dir, "coverage-badge.json"),
        badge_json("Coverage", f"{cov['coverage_percent']}%", cov_color),
    )
    # duration
    write_json(
        os.path.join(badges_dir, "ci-duration-badge.json"),
        badge_json("CI Duration", duration_pretty, "blue"),
    )
    # coverage trend
    trend_color = cov_color
    write_json(
        os.path.join(badges_dir, "coverage-trend-badge.json"),
        badge_json("Coverage Trend", cov_delta_str, trend_color),
    )

    # Emit index.html (simple template injection)
    html_path = os.path.join(out_dir, "index.html")
    html = INDEX_HTML.strip().replace("__REPO_PATH__", args.repo)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    print("✅ Dashboard generated at:", out_dir)


# Minimal, responsive dashboard with Chart.js via CDN
INDEX_HTML = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CI Dashboard — __REPO_PATH__</title>
  <link rel="preconnect" href="https://cdn.jsdelivr.net">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root { --bg:#0b1020; --card:#131a2b; --text:#e6ebff; --muted:#99a3c2; --ok:#56d364; --warn:#ffd33d; --bad:#ff6a69; --brand:#6ea8fe; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji"; background:var(--bg); color:var(--text); }
    header { padding:24px 20px; border-bottom:1px solid #1e2740; display:flex; gap:16px; align-items:center; flex-wrap:wrap; }
    header .title { font-size:20px; font-weight:700; }
    header .sub { color:var(--muted); font-size:14px; }
    .wrap { padding:20px; display:grid; grid-template-columns: repeat(12, 1fr); gap:16px; }
    .card { background:var(--card); border:1px solid #222b49; border-radius:14px; padding:16px; }
    .kpi { grid-column: span 3; }
    .kpi h3 { margin:0 0 8px; font-size:13px; color:var(--muted); text-transform:uppercase; letter-spacing:.06em; }
    .kpi .val { font-size:22px; font-weight:700; }
    .row { grid-column: span 12; display:grid; grid-template-columns: repeat(12, 1fr); gap:16px; }
    .col-6 { grid-column: span 6; }
    .muted { color:var(--muted); }
    a.btn { background:#1a284e; border:1px solid #294d9b; color:#cfe0ff; text-decoration:none; padding:8px 10px; border-radius:9px; font-size:13px; }
    .badge { font-size:12px; padding:3px 6px; border-radius:8px; border:1px solid #2b375d; background:#11182b; color:var(--muted); }
    footer { padding:16px 20px; color:var(--muted); border-top:1px solid #1e2740; }
    @media (max-width: 900px){ .kpi { grid-column: span 6; } .col-6 { grid-column: span 12; } }
  </style>
</head>
<body>
  <header>
    <div class="title">CI Dashboard — __REPO_PATH__</div>
    <div class="sub">Live metrics from GitHub Actions · Updated each run</div>
    <div style="flex:1"></div>
    <a class="btn" href="../">Repo Pages</a>
    <a class="btn" href="https://github.com/__REPO_PATH__/actions">Actions</a>
  </header>
  <div class="wrap">
    <!-- KPIs -->
    <div class="card kpi"><h3>Coverage</h3><div class="val" id="kpiCoverage">—</div><div class="muted" id="kpiCoverageDelta">—</div></div>
    <div class="card kpi"><h3>Pass Rate</h3><div class="val" id="kpiPassRate">—</div><div class="muted" id="kpiTests">—</div></div>
    <div class="card kpi"><h3>Lint Issues</h3><div class="val" id="kpiLint">—</div><div class="muted">Ruff total</div></div>
    <div class="card kpi"><h3>CI Duration</h3><div class="val" id="kpiDuration">—</div><div class="muted" id="kpiCommit">—</div></div>

    <!-- Charts -->
    <div class="row">
      <div class="card col-6">
        <h3 class="muted">Coverage Trend</h3>
        <canvas id="coverageChart" height="140"></canvas>
      </div>
      <div class="card col-6">
        <h3 class="muted">Pass Rate Trend</h3>
        <canvas id="passChart" height="140"></canvas>
      </div>
    </div>
    <div class="row">
      <div class="card col-6">
        <h3 class="muted">CI Duration Trend (s)</h3>
        <canvas id="durChart" height="140"></canvas>
      </div>
      <div class="card col-6">
        <h3 class="muted">Lint Issues Trend</h3>
        <canvas id="lintChart" height="140"></canvas>
      </div>
    </div>

    <!-- Meta -->
    <div class="row">
      <div class="card col-6" id="metaCard">
        <h3 class="muted">Latest Run</h3>
        <div id="meta"></div>
      </div>
      <div class="card col-6">
        <h3 class="muted">Badges</h3>
        <div style="display:flex; gap:8px; flex-wrap:wrap;">
          <img class="badge" src="https://img.shields.io/endpoint?url=https://gerome650.github.io/MAGSASA-CARD-ERP/ci-dashboard/badges/coverage-badge.json" alt="coverage">
          <img class="badge" src="https://img.shields.io/endpoint?url=https://gerome650.github.io/MAGSASA-CARD-ERP/ci-dashboard/badges/coverage-trend-badge.json" alt="coverage trend">
          <img class="badge" src="https://img.shields.io/endpoint?url=https://gerome650.github.io/MAGSASA-CARD-ERP/ci-dashboard/badges/test-results-badge.json" alt="tests">
          <img class="badge" src="https://img.shields.io/endpoint?url=https://gerome650.github.io/MAGSASA-CARD-ERP/ci-dashboard/badges/lint-status-badge.json" alt="lint">
          <img class="badge" src="https://img.shields.io/endpoint?url=https://gerome650.github.io/MAGSASA-CARD-ERP/ci-dashboard/badges/ci-duration-badge.json" alt="duration">
        </div>
      </div>
    </div>
  </div>
  <footer>
    <span>Built from GitHub Actions. Data JSON under <code>/ci-dashboard/data</code>. Badges under <code>/ci-dashboard/badges</code>.</span>
  </footer>
  <script>
    async function fetchJSON(p){ const r=await fetch(p,{cache:'no-store'}); return r.json(); }
    function fmtDate(d){ const t=new Date(d); return t.toLocaleString(); }
    (async()=>{
      const latest = await fetchJSON('./data/latest.json');
      const history = await fetchJSON('./data/history.json');

      // KPIs
      document.getElementById('kpiCoverage').textContent = latest.coverage_percent.toFixed(1) + '%';
      const delta = latest.coverage_delta;
      document.getElementById('kpiCoverageDelta').textContent = (delta>=0?'+':'') + delta.toFixed(1) + '% vs prev';
      document.getElementById('kpiPassRate').textContent = latest.pass_rate.toFixed(1) + '%';
      document.getElementById('kpiTests').textContent = `${latest.tests.passed}/${latest.tests.passed+latest.tests.failed} passed`;
      document.getElementById('kpiLint').textContent = latest.lint.issues;
      document.getElementById('kpiDuration').textContent = latest.ci_duration_pretty;
      document.getElementById('kpiCommit').textContent = latest.commit.substring(0,7) + ' · ' + latest.branch;

      // Meta
      document.getElementById('meta').innerHTML = `
        <div class="muted">Timestamp: ${fmtDate(latest.timestamp)}</div>
        <div>Run: <a class="btn" href="${latest.run_url}">Open on GitHub</a></div>
        <div class="muted">Actor: ${latest.actor}</div>
      `;

      // Charts
      const labels = history.map(h => (new Date(h.timestamp)).toLocaleDateString());
      const cov = history.map(h => h.coverage_percent);
      const pass = history.map(h => h.pass_rate);
      const dur = history.map(h => h.ci_duration_seconds);
      const lint = history.map(h => h.lint_issues);

      const common = {borderWidth:2, tension:.3, pointRadius:0};

      new Chart(document.getElementById('coverageChart'), {
        type:'line',
        data:{ labels, datasets:[{label:'Coverage %', data: cov, ...common}] },
        options:{ plugins:{legend:{display:false}}, scales:{x:{ticks:{color:'#9fb0ff'}},y:{ticks:{color:'#9fb0ff'}}} }
      });
      new Chart(document.getElementById('passChart'), {
        type:'line',
        data:{ labels, datasets:[{label:'Pass Rate %', data: pass, ...common}] },
        options:{ plugins:{legend:{display:false}}, scales:{x:{ticks:{color:'#9fb0ff'}},y:{ticks:{color:'#9fb0ff'}}} }
      });
      new Chart(document.getElementById('durChart'), {
        type:'line',
        data:{ labels, datasets:[{label:'Duration (s)', data: dur, ...common}] },
        options:{ plugins:{legend:{display:false}}, scales:{x:{ticks:{color:'#9fb0ff'}},y:{ticks:{color:'#9fb0ff'}}} }
      });
      new Chart(document.getElementById('lintChart'), {
        type:'line',
        data:{ labels, datasets:[{label:'Lint Issues', data: lint, ...common}] },
        options:{ plugins:{legend:{display:false}}, scales:{x:{ticks:{color:'#9fb0ff'}},y:{ticks:{color:'#9fb0ff'}}} }
      });
    })();
  </script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
