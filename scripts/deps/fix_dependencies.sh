#!/usr/bin/env bash
set -euo pipefail

echo "🛠️  Attempting dependency fixes (best-effort)…"

have_cmd() { command -v "$1" >/dev/null 2>&1; }

# 1) Poetry lock refresh (keeps versions unless needed)
if have_cmd poetry; then
  echo "• Running: poetry lock --no-update"
  poetry lock --no-update || echo "  (lock refresh failed, continuing)"
fi

# 2) Pin floating versions in pyproject.toml where feasible (simple heuristics)
if [ -f pyproject.toml ]; then
  echo "• Pinning broad wildcards in pyproject.toml (heuristic)"
  # Example heuristic: change ">=x.y,<x.z" to "^x.y" left untouched; but pin "*" to "~= current"
  # We only handle the most dangerous "*" to a conservative floor if a version exists in lock.
  if [ -f poetry.lock ]; then
    # Extract pinned versions from lock for direct deps and replace "*" specs
    python - "$@" <<'PY'
import re, sys, pathlib, tomllib
lock = pathlib.Path("poetry.lock").read_text()
py = pathlib.Path("pyproject.toml").read_text()
versions = {}
pkg = None
for line in lock.splitlines():
    if line.startswith("[[package]]"):
        pkg=None
    m = re.match(r'^name = "([^"]+)"$', line.strip())
    if m: pkg = m.group(1)
    m2 = re.match(r'^version = "([^"]+)"$', line.strip())
    if m2 and pkg:
        versions[pkg]=m2.group(1)
out = py
def pin_star(block):
    name = block[0]
    vers = versions.get(name)
    if not vers: return None
    # prefer ~=major.minor
    parts = vers.split(".")
    if len(parts)>=2:
        return f"~={parts[0]}.{parts[1]}"
    return vers
def repl(match):
    name = match.group("name")
    pinned = pin_star([name])
    if pinned:
        return f'{match.group("pre")}"{pinned}"'
    return match.group(0)
out = re.sub(r'(?P<pre>^\s*[^#\s]+?\s*=\s*)"(?:\*|any)"\s*$', repl, out, flags=re.M)
pathlib.Path("pyproject.toml").write_text(out)
print("Pinned '*' where lock info available.")
PY
  fi
fi

# 3) Sync Dockerfile base image tag to required Python version if present
if [ -f Dockerfile ]; then
  PY_REQ="${PYTHON_REQUIRED_VERSION:-}"
  if [ -n "$PY_REQ" ]; then
    echo "• Syncing Dockerfile base python image to ${PY_REQ%%.*}.${PY_REQ#*.%%}"
    # Replace lines like: FROM python:3.11-slim OR python:3.11.9-slim
    sed -E -i.bak 's|^(FROM\s+python:)[0-9]+\.[0-9]+(\.[0-9]+)?(-[a-z0-9.-]+)?|\1'"$PY_REQ"'|i' Dockerfile || true
    rm -f Dockerfile.bak || true
  fi
fi

echo "✅ fix-dependencies completed (best-effort). Review changes and run tests."

