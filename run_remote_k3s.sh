#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage:
  bash run_remote_k3s.sh [--ip <PUBLIC_IP>] [--key </path/to/private_key>] [--user <ubuntu|ec2-user|root|auto>]

Examples:
  bash run_remote_k3s.sh --ip 203.0.113.10 --key ~/.ssh/id_ed25519 --user ubuntu
  bash run_remote_k3s.sh   # will prompt for any missing values

You can also pre-set IP/KEY/USER via env vars:
  IP=203.0.113.10 KEY=~/.ssh/id_ed25519 USER=ubuntu bash run_remote_k3s.sh
USAGE
}

IP="${IP:-}"
KEY="${KEY:-}"
USER="${USER:-auto}"

# Parse flags
while [[ $# -gt 0 ]]; do
  case "$1" in
    --ip)   IP="${2:-}"; shift 2 ;;
    --key)  KEY="${2:-}"; shift 2 ;;
    --user) USER="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1"; usage; exit 2 ;;
  esac
done

# Interactive prompts for anything missing
if [[ -z "${IP}" ]]; then
  read -r -p "Enter VM public IP: " IP
fi
if [[ -z "${KEY}" ]]; then
  DEF_KEY="$HOME/.ssh/id_ed25519"
  read -r -p "Path to SSH private key [$DEF_KEY]: " KEY
  KEY="${KEY:-$DEF_KEY}"
fi
case "$KEY" in "~"/*) KEY="${KEY/#\~/$HOME}";; esac
if [[ -z "${USER}" ]]; then
  USER="auto"
fi

# Basic checks
[[ -n "$IP" ]] || { echo "ERROR: IP is required"; exit 2; }
[[ -f "$KEY" ]] || { echo "ERROR: SSH key not found at: $KEY"; exit 2; }
chmod 600 "$KEY" || true

ssh_ok () {
  local u="$1"
  ssh -i "$KEY" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=8 "$u@$IP" 'echo ok' 2>/dev/null | grep -q '^ok$'
}

# Resolve USER (auto-detect if requested)
if [[ "$USER" == "auto" ]]; then
  for candidate in ubuntu ec2-user root; do
    if ssh_ok "$candidate"; then USER="$candidate"; break; fi
  done
  [[ "$USER" != "auto" ]] || { echo "ERROR: SSH test failed for ubuntu/ec2-user/root on $IP with $KEY"; exit 1; }
else
  ssh_ok "$USER" || { echo "ERROR: SSH test failed for $USER@$IP (check KEY/USER/IP)"; exit 1; }
fi

echo "==> Using $USER@$IP with key $KEY"
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Bootstrap remote k3s + wire kubeconfig
bash scripts/bootstrap_k3s_remote.sh "$USER@$IP" "$KEY"

echo "==> Verifying kube context and node"
kubectl config current-context || true
kubectl get nodes -o wide || true

echo
echo "==> Launching the interactive chaos helper"
echo "    (Press Enter at the context prompt to keep current; enter your namespace or 'default')"
bash run_chaos_interactive.sh
