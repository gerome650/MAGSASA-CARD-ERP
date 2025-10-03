#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash scripts/run_remote_k3s_one_shot.sh <PUBLIC_IP> </path/to/private_key> [--user ubuntu|ec2-user|root]
#
# Examples:
#   bash scripts/run_remote_k3s_one_shot.sh 203.0.113.10 ~/.ssh/id_ed25519
#   bash scripts/run_remote_k3s_one_shot.sh 203.0.113.10 ~/.ssh/id_ed25519 --user ubuntu

IP="${1:-}"; KEY="${2:-}"
USER_ARG="${3:-}"

if [[ -z "$IP" || -z "$KEY" ]]; then
  echo "Usage: $0 <PUBLIC_IP> </path/to/private_key> [--user <ubuntu|ec2-user|root>]" >&2
  exit 2
fi

if [[ "$USER_ARG" == "--user" ]]; then
  USER="${4:-}"
  [[ -n "$USER" ]] || { echo "ERROR: --user requires a value"; exit 2; }
else
  USER=""
fi

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PROBE="$ROOT/scripts/ssh_probe.sh"
BOOT="$ROOT/scripts/bootstrap_k3s_remote.sh"
RUNNER="$ROOT/run_chaos_interactive.sh"

[[ -f "$PROBE" ]] || { echo "ERROR: missing $PROBE (run the earlier Cursor prompts)"; exit 1; }
[[ -f "$BOOT" ]] || { echo "ERROR: missing $BOOT (run the earlier Cursor prompts)"; exit 1; }
[[ -f "$RUNNER" ]] || { echo "ERROR: missing $RUNNER (Stage 6.6 helper)"; exit 1; }
[[ -f "$KEY" ]] || { echo "ERROR: key not found at $KEY"; exit 1; }
chmod 600 "$KEY" || true

echo "==> Probing SSH to find a working username (or using provided one)"
if [[ -n "$USER" ]]; then
  # Verify the supplied user works
  if ! ssh -i "$KEY" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=8 -o BatchMode=yes "$USER@$IP" 'echo OK' 2>/dev/null | grep -q '^OK$'; then
    echo "ERROR: SSH test failed for $USER@$IP. Check KEY/USER/IP or firewall."; exit 1
  fi
  OK_USER="$USER"
else
  # Run the probe; it prints a "✅ Success with user: <name>" line on success
  set +e
  PROBE_OUT="$("$PROBE" "$IP" "$KEY" 2>&1)"
  PROBE_RC=$?
  set -e
  echo "$PROBE_OUT"
  if [[ $PROBE_RC -ne 0 ]]; then
    echo "ERROR: ssh probe failed. See output above." >&2
    exit $PROBE_RC
  fi
  OK_USER="$(echo "$PROBE_OUT" | awk '/Success with user:/ {print $5}')"
  [[ -n "$OK_USER" ]] || { echo "ERROR: could not parse working user from probe output"; exit 1; }
fi

echo "==> Using $OK_USER@$IP with key $KEY"
bash "$BOOT" "$OK_USER@$IP" "$KEY"

echo "==> Verifying kube context & node"
kubectl config current-context || true
kubectl get nodes -o wide || true

echo
echo "==> Launching chaos interactive helper"
echo "    (Press Enter at the context prompt to keep current; enter your namespace or 'default')"
bash "$RUNNER"
