#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash apply_chaos.sh <STAGING_NS> [KUBE_CONTEXT]
# Examples:
#   bash apply_chaos.sh staging-apps
#   bash apply_chaos.sh staging-apps my-staging-context

NS="${1:-default}"
CTX="${2:-}"

echo "==> Namespace: $NS"
if [[ -n "${CTX}" ]]; then
  echo "==> Switching kubectl context to: ${CTX}"
  kubectl config use-context "${CTX}"
fi

# Ensure Homebrew env is loaded (so kubectl is on PATH on macOS/Homebrew)
eval "$(/opt/homebrew/bin/brew shellenv)" 2>/dev/null || true

if ! command -v kubectl >/dev/null 2>&1; then
  echo "ERROR: kubectl not found. Install with: brew install kubectl" >&2
  exit 1
fi

echo "==> kubectl client:"
kubectl version --client || true

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
echo "==> Repo root: $ROOT"

RBAC="$ROOT/infra/k8s/chaos-runner-rbac.yaml"
CRON="$ROOT/infra/k8s/cron-chaos.yaml"

[[ -f "$RBAC" ]] || { echo "ERROR: missing $RBAC"; exit 1; }
[[ -f "$CRON" ]] || { echo "ERROR: missing $CRON"; exit 1; }

# Ensure namespace exists (no-op if it already does)
kubectl get ns "$NS" >/dev/null 2>&1 || kubectl create ns "$NS"

echo "==> Applying RBAC"
kubectl -n "$NS" apply -f "$RBAC"

echo "==> Applying CronJob"
kubectl -n "$NS" apply -f "$CRON"

echo "==> Verifying resources"
kubectl -n "$NS" get sa/chaos-runner -o wide || true
kubectl -n "$NS" get role/chaos-runner -o wide || true
kubectl -n "$NS" get rolebinding/chaos-runner -o wide || true
kubectl -n "$NS" get cronjob/chaos-nightly -o wide

# Trigger an immediate run from the CronJob
RUN_ID="$(date +%s)"
JOB_NAME="chaos-manual-$RUN_ID"
echo "==> Creating Job: $JOB_NAME (from CronJob chaos-nightly)"
kubectl -n "$NS" create job --from=cronjob/chaos-nightly "$JOB_NAME"

echo "==> Waiting for Job to complete (timeout 15m)"
if ! kubectl -n "$NS" wait --for=condition=complete "job/$JOB_NAME" --timeout=900s; then
  echo "WARN: Job did not complete within timeout; proceeding to show logs/state..."
fi

echo "==> Streaming logs (all pods for this Job)"
if ! kubectl -n "$NS" logs -l "job-name=$JOB_NAME" -f --tail=200; then
  echo "Logs not available yet; listing pods:"
  kubectl -n "$NS" get pods -l "job-name=$JOB_NAME" -o wide
fi

echo "==> Done"
