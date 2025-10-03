#!/usr/bin/env bash
set -euo pipefail

# Interactive helper: applies RBAC + CronJob and runs a smoke-test Job.

# Ensure Homebrew env (so kubectl is on PATH on macOS/Homebrew)
eval "$(/opt/homebrew/bin/brew shellenv)" 2>/dev/null || true

if ! command -v kubectl >/dev/null 2>&1; then
  echo "ERROR: kubectl not found. Install with: brew install kubectl" >&2
  exit 1
fi

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
RBAC="$ROOT/infra/k8s/chaos-runner-rbac.yaml"
CRON="$ROOT/infra/k8s/cron-chaos.yaml"

[[ -f "$RBAC" ]] || { echo "ERROR: missing $RBAC"; exit 1; }
[[ -f "$CRON" ]] || { echo "ERROR: missing $CRON"; exit 1; }

echo "==> kubectl client:"
kubectl version --client || true
CUR_CTX="$(kubectl config current-context 2>/dev/null || true)"

echo
echo "Available kube contexts:"
kubectl config get-contexts -o name 2>/dev/null || true
echo
read -r -p "Context to use [${CUR_CTX:-leave blank to keep current}]: " CTX
if [[ -n "${CTX:-}" ]]; then
  echo "==> Switching context to: $CTX"
  kubectl config use-context "$CTX"
fi

echo
read -r -p "Namespace to use (e.g., staging-apps) [default]: " NS
NS="${NS:-default}"
echo "==> Namespace: $NS"
kubectl get ns "$NS" >/dev/null 2>&1 || kubectl create ns "$NS"

echo "==> Applying RBAC: $RBAC"
kubectl -n "$NS" apply -f "$RBAC"

echo "==> Applying CronJob: $CRON"
kubectl -n "$NS" apply -f "$CRON"

echo "==> Verifying resources"
kubectl -n "$NS" get sa/chaos-runner -o wide || true
kubectl -n "$NS" get role/chaos-runner -o wide || true
kubectl -n "$NS" get rolebinding/chaos-runner -o wide || true
kubectl -n "$NS" get cronjob/chaos-nightly -o wide

echo "==> Triggering one-off Job from CronJob"
RUN_ID="$(date +%s)"
JOB_NAME="chaos-manual-$RUN_ID"
kubectl -n "$NS" create job --from=cronjob/chaos-nightly "$JOB_NAME"

echo "==> Waiting for Job completion (timeout 15m)"
if ! kubectl -n "$NS" wait --for=condition=complete "job/$JOB_NAME" --timeout=900s; then
  echo "WARN: Job did not complete within timeout; showing state..."
fi

echo "==> Streaming logs"
if ! kubectl -n "$NS" logs -l "job-name=$JOB_NAME" -f --tail=200; then
  echo "Logs not available yet; listing pods:"
  kubectl -n "$NS" get pods -l "job-name=$JOB_NAME" -o wide
fi

echo "==> Done"

