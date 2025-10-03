#!/usr/bin/env bash
set -euo pipefail

# Bootstraps a local Kubernetes (k3s) using Colima, then hands off to run_chaos_interactive.sh

# Ensure Homebrew env so 'brew' and installed binaries are on PATH
eval "$(/opt/homebrew/bin/brew shellenv)" 2>/dev/null || true

# kubectl check (you already installed it, but be explicit)
if ! command -v kubectl >/dev/null 2>&1; then
  echo "ERROR: kubectl not found. Install with: brew install kubectl" >&2
  exit 1
fi

# Install colima if missing
if ! command -v colima >/dev/null 2>&1; then
  echo "==> Installing Colima..."
  brew install colima
fi

# Start Colima with Kubernetes (k3s). Re-run is safe; it becomes a no-op.
echo "==> Starting Colima with Kubernetes (k3s) ..."
colima start --kubernetes --cpu 2 --memory 4 --disk 20 || true

echo "==> Current kube contexts:"
kubectl config get-contexts -o name || true

# Verify that 'colima' context exists (k3s via Colima)
if ! kubectl config get-contexts -o name 2>/dev/null | grep -q '^colima$'; then
  echo "ERROR: 'colima' context not found. Run: colima start --kubernetes, then re-run this script."
  exit 1
fi

echo "==> Using context: colima"
kubectl config use-context colima

# Hand off to the interactive chaos runner
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
RUNNER="$ROOT/run_chaos_interactive.sh"
if [[ ! -f "$RUNNER" ]]; then
  echo "ERROR: $RUNNER not found. Ensure Stage 6.6 scripts are present."
  exit 1
fi

echo
echo "Next: run the interactive chaos helper (enter namespace when prompted)."
echo "  bash run_chaos_interactive.sh"
