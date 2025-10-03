#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

have_ctx() { kubectl config current-context >/dev/null 2>&1; }

if ! have_ctx; then
  echo "No kubectl context found. Let's set one up."
  read -r -p "Enter VM public IP: " IP
  read -r -p "Path to SSH private key [~/.ssh/id_ed25519]: " KEY
  [[ -z "$KEY" ]] && KEY="$HOME/.ssh/id_ed25519"
  case "$KEY" in "~"/*) KEY="${KEY/#\~/$HOME}";; esac
  bash scripts/run_remote_k3s_one_shot.sh "$IP" "$KEY"
fi

# Verify cluster
kubectl config current-context
kubectl get nodes -o wide

# Namespace + apply
NS="staging-apps"
kubectl get ns "$NS" >/dev/null 2>&1 || kubectl create ns "$NS"
kubectl -n "$NS" apply -f infra/k8s/chaos-runner-rbac.yaml
kubectl -n "$NS" apply -f infra/k8s/cron-chaos.yaml
kubectl -n "$NS" get sa,role,rolebinding,cronjob chaos-nightly -o wide

# One-off run & logs
RUN="chaos-manual-$(date +%s)"
kubectl -n "$NS" create job --from=cronjob/chaos-nightly "$RUN"
kubectl -n "$NS" logs -l job-name="$RUN" -f --tail=200

