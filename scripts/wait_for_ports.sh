#!/usr/bin/env bash
set -euo pipefail
usage(){ echo "Usage: $0 [--timeout SEC] <IP> <PORT1> [PORT2] ..." >&2; exit 2; }

TIMEOUT=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --timeout) TIMEOUT="${2:-0}"; shift 2 ;;
    -h|--help) usage ;;
    *) break ;;
  esac
done

[[ $# -ge 2 ]] || usage
IP="$1"; shift
PORTS=("$@")

echo "Waiting for ports on $IP: ${PORTS[*]} (timeout: ${TIMEOUT}s)"
START=$(date +%s)

while true; do
  ALL=1
  for P in "${PORTS[@]}"; do
    if nc -vz "$IP" "$P" >/dev/null 2>&1; then
      echo "✓ $IP:$P open"
    else
      echo "… $IP:$P closed"
      ALL=0
    fi
  done
  [[ $ALL -eq 1 ]] && break
  if [[ $TIMEOUT -gt 0 ]]; then
    NOW=$(date +%s)
    ELAPSED=$((NOW-START))
    if [[ $ELAPSED -ge $TIMEOUT ]]; then
      echo "ERROR: timeout (${TIMEOUT}s) waiting for ports ${PORTS[*]} on $IP" >&2
      exit 1
    fi
  fi
  sleep 5
done
echo "All ports open."
