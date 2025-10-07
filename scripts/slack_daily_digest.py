#!/usr/bin/env python3
"""
Slack Daily Digest for GitHub Actions
- Summarizes last 24h CI runs
- Shows 7-day trend (sparkline + emoji bars)
- Includes Syntax/Lint/Coverage badge links (GitHub Pages)
- Highlights Top 3 slowest workflows
- Posts Block Kit message to Slack Incoming Webhook
"""

from __future__ import annotations

import json
import math
import os
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import mean

# ---------- Config & Env ----------
REPO = os.getenv("GITHUB_REPOSITORY", "").strip()  # e.g. owner/repo
OWNER, REPO_NAME = (REPO.split("/", 1) + [""])[:2]
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "").strip()

# Resolve Pages base URL (fallback)
DEFAULT_PAGES = f"https://{OWNER}.github.io/{REPO_NAME}" if OWNER and REPO_NAME else ""
PAGES_BASE_URL = os.getenv("PAGES_BASE_URL", DEFAULT_PAGES).rstrip("/")

ACTIONS_URL = f"https://github.com/{REPO}/actions" if REPO else "https://github.com"

# Windows for data
NOW = datetime.now(timezone.utc)
DAY_24_AGO = NOW - timedelta(hours=24)
DAY_7_AGO = NOW - timedelta(days=7)
DAY_14_AGO = NOW - timedelta(days=14)  # for week-over-week deltas, if desired

# ---------- Utilities ----------


def _gh_api(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {GITHUB_TOKEN}" if GITHUB_TOKEN else "",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "slack-daily-digest",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def github_list_workflow_runs(since: datetime) -> list[dict]:
    """Return workflow runs updated since `since` (UTC). Paginates up to ~1000 items."""
    if not REPO:
        return []
    runs = []
    page = 1
    per_page = 100
    since_iso = since.isoformat().replace("+00:00", "Z")
    while True:
        url = (
            f"https://api.github.com/repos/{REPO}/actions/runs"
            f"?per_page={per_page}&page={page}&created=>={since_iso}"
        )
        data = _gh_api(url)
        page_runs = data.get("workflow_runs", []) or data.get("runs", [])
        if not page_runs:
            break
        runs.extend(page_runs)
        if len(page_runs) < per_page or len(runs) > 1000:
            break
        page += 1
    return runs


def minutes_between(a: str, b: str) -> float:
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    try:
        start = datetime.strptime(a, fmt).replace(tzinfo=timezone.utc)
        end = datetime.strptime(b, fmt).replace(tzinfo=timezone.utc)
        return max(0.0, (end - start).total_seconds() / 60.0)
    except Exception:
        return 0.0


def fmt_minutes(m: float) -> str:
    if m < 1.0:
        return f"{int(m*60)}s"
    return f"{m:.1f} min"


def sparkline(values: list[float]) -> str:
    blocks = "▁▂▃▄▅▆▇█"
    if not values:
        return ""
    vmin, vmax = min(values), max(values)
    if math.isclose(vmin, vmax):
        return blocks[0] * len(values)
    result = []
    for v in values:
        idx = int((v - vmin) / (vmax - vmin) * (len(blocks) - 1))
        result.append(blocks[max(0, min(idx, len(blocks) - 1))])
    return "".join(result)


def weekday_emoji_bar(successes: int, failures: int) -> str:
    if failures == 0 and successes == 0:
        return "—"
    if failures == 0:
        return "✅" * min(successes, 6)
    if successes == 0:
        return "❌" * min(failures, 6)
    # mix
    n = successes + failures
    ok = max(1, round(successes / n * 6))
    bad = max(0, 6 - ok)
    return "✅" * ok + "❌" * bad


def pct(n: float) -> str:
    return f"{n:.1f}%"


def safe_ratio(num: float, den: float) -> float:
    return 0.0 if den == 0 else 100.0 * num / den


# ---------- Data aggregation ----------


def aggregate_runs(runs: list[dict]):
    last24 = []
    last7 = []
    by_day = defaultdict(list)  # day (YYYY-MM-DD) -> [pass=1/0]
    durations_24 = []
    workflow_times_24 = defaultdict(list)  # name -> [minutes]

    for r in runs:
        created = r.get("created_at") or r.get("run_started_at")
        updated = r.get("updated_at") or r.get("run_started_at") or created
        status = (
            r.get("conclusion") or ""
        ).lower()  # success / failure / cancelled / neutral / skipped
        name = r.get("name") or r.get("display_title") or "Unnamed Workflow"

        # time range buckets
        try:
            created_dt = datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
        except Exception:
            continue

        is24 = created_dt >= DAY_24_AGO
        is7 = created_dt >= DAY_7_AGO

        if is7:
            last7.append(r)
            day_key = created_dt.strftime("%Y-%m-%d")
            by_day[day_key].append(1 if status == "success" else 0)

        if is24:
            last24.append(r)
            dur = minutes_between(r.get("run_started_at") or created, updated)
            durations_24.append(dur)
            workflow_times_24[name].append(dur)

    # 24h summary
    total_24 = len(last24)
    succ_24 = sum(1 for r in last24 if (r.get("conclusion") or "").lower() == "success")
    fail_24 = sum(1 for r in last24 if (r.get("conclusion") or "").lower() == "failure")
    pass_rate_24 = safe_ratio(succ_24, total_24)
    avg_duration_24 = mean(durations_24) if durations_24 else 0.0

    # 7-day trend
    # fill last 7 calendar days (today-6 … today)
    days = [(NOW - timedelta(days=i)).date().isoformat() for i in range(6, -1, -1)]
    day_pass_pct = []
    day_emoji = []
    for d in days:
        vals = by_day.get(d, [])
        s = sum(vals)
        f = len(vals) - s
        pr = safe_ratio(s, len(vals)) if vals else 0.0
        day_pass_pct.append(pr)
        day_emoji.append(weekday_emoji_bar(s, f))

    # slowest workflows (24h)
    slow = []
    total_minutes = sum(sum(v) for v in workflow_times_24.values())
    for wf, mins in workflow_times_24.items():
        avg_m = mean(mins) if mins else 0.0
        share = safe_ratio(sum(mins), total_minutes) if total_minutes else 0.0
        slow.append((wf, avg_m, share))
    slow.sort(key=lambda x: x[1], reverse=True)
    top3 = slow[:3]

    return {
        "24h": {
            "total": total_24,
            "successes": succ_24,
            "failures": fail_24,
            "pass_rate": pass_rate_24,
            "avg_duration_min": avg_duration_24,
        },
        "7d": {
            "days": days,
            "pass_pcts": day_pass_pct,
            "sparkline": sparkline(day_pass_pct),
            "emoji_bars": day_emoji,
        },
        "slowest_24h": top3,
    }


# ---------- Slack message ----------


def slack_blocks(summary: dict) -> dict:
    badges_md = []
    if PAGES_BASE_URL:
        badges_md = [
            f"[Syntax ✅]({PAGES_BASE_URL}/ci-dashboard/syntax-guard.json)",
            f"[Lint 🧹]({PAGES_BASE_URL}/ci-dashboard/lint.json)",
            f"[Coverage 📊]({PAGES_BASE_URL}/ci-dashboard/coverage.json)",
        ]

    s24 = summary["24h"]
    s7 = summary["7d"]
    slow = summary["slowest_24h"]

    day_lines = []
    for d, emojis, pr in zip(
        s7["days"], s7["emoji_bars"], s7["pass_pcts"], strict=False
    ):
        # show weekday (Mon/Tue/…) + quick emojis
        dt = datetime.fromisoformat(d)
        weekday = dt.strftime("%a")
        line = f"*{weekday}*: {emojis}  ({pct(pr)})"
        day_lines.append(line)

    slow_lines = []
    for name, avg_m, share in slow:
        slow_lines.append(f"• *{name}* — {fmt_minutes(avg_m)}  (~{pct(share)})")

    return {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📬 CI Daily Digest — Last 24 Hours",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Total runs:*\n{s24['total']}"},
                    {
                        "type": "mrkdwn",
                        "text": f"*Pass rate:*\n{pct(s24['pass_rate'])}",
                    },
                    {"type": "mrkdwn", "text": f"*✅ Successes:*\n{s24['successes']}"},
                    {"type": "mrkdwn", "text": f"*❌ Failures:*\n{s24['failures']}"},
                    {
                        "type": "mrkdwn",
                        "text": f"*Avg duration:*\n{fmt_minutes(s24['avg_duration_min'])}",
                    },
                ],
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*🏅 Quality Gates*\n"
                    + (
                        " · ".join(badges_md)
                        if badges_md
                        else "_(Badges pending GitHub Pages)_"
                    ),
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*📈 7-Day Pass-Rate Trend*\n`spark:` {s7['sparkline']}\n\n"
                    + "\n".join(day_lines),
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*🐢 Top 3 Slowest Workflows (24h)*\n"
                    + (
                        "\n".join(slow_lines) if slow_lines else "_No data in last 24h_"
                    ),
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🔎 View Actions"},
                        "url": f"{ACTIONS_URL}",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📊 View Dashboard"},
                        "url": (
                            f"{PAGES_BASE_URL}/ci-dashboard/"
                            if PAGES_BASE_URL
                            else ACTIONS_URL
                        ),
                    },
                ],
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"_Repo:_ `{REPO}`  ·  _Generated:_ {NOW.astimezone().strftime('%Y-%m-%d %H:%M %Z')}",
                    }
                ],
            },
        ]
    }


# ---------- Main ----------


def main() -> int:
    if not REPO:
        print("ERROR: GITHUB_REPOSITORY not set.")
        return 2
    if not SLACK_WEBHOOK_URL:
        print(
            "SLACK_WEBHOOK_URL not set — skipping Slack post (exit 0 to avoid failing CI)."
        )
        return 0

    try:
        runs = github_list_workflow_runs(DAY_7_AGO)
        summary = aggregate_runs(runs)
        payload = slack_blocks(summary)
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            SLACK_WEBHOOK_URL, data=data, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            print(f"Slack response: {resp.status}")
        return 0
    except urllib.error.HTTPError as e:
        print(f"HTTPError posting to Slack: {e} - {e.read().decode('utf-8', 'ignore')}")
        return 1
    except Exception as e:
        print(f"ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
