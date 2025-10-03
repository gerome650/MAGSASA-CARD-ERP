#!/usr/bin/env bash
set -euo pipefail

# Goal: if no kube contexts exist, set up Minikube (Docker driver) on macOS.
# Then, hand off to the existing interactive runner (run_chaos_interactive.sh).

# Ensure Homebrew env so brew/kubectl/minikube are on PATH (harmless if already set)
eval "$(/opt/homebrew/bin/brew shellenv)" 2>/dev/null || true

# 1) kubectl present?
if ! command -v kubectl >/dev/null 2>&1; then
  echo "ERROR: kubectl not found. Install with: brew install kubectl" >&2
  exit 1
fi

echo "==> kubectl client:"
kubectl version --client || true

# 2) Do we have any contexts already?
if ! kubectl config get-contexts -o name 2>/dev/null | grep -q .; then
  echo "==> No kube contexts found. Bootstrapping a local Minikube cluster (Docker driver)."

  # Docker Desktop is the simplest driver on macOS/arm64
  if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: Docker Desktop is required for the 'docker' driver."
    echo "Install from https://www.docker.com/products/docker-desktop/, enable it, then re-run this script."
    exit 1
  fi

  # Install minikube if missing
  if ! command -v minikube >/dev/null 2>&1; then
    echo "==> Installing minikube via Homebrew..."
    brew install minikube
  fi

  echo "==> Starting minikube (this may take a few minutes)..."
  minikube start --driver=docker
fi

# 3) Show/confirm context
CUR_CTX="$(kubectl config current-context 2>/dev/null || true)"
echo "==> Current kubectl context: ${CUR_CTX:-<none>} (use 'kubectl config get-contexts' to see all)"

# 4) Hand off to the interactive chaos runner
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
RUNNER="$ROOT/run_chaos_interactive.sh"
if [[ ! -f "$RUNNER" ]]; then
  echo "ERROR: $RUNNER not found. Ensure the file exists and re-run."
  exit 1
fi

echo
echo "Next step: run the interactive chaos script. Example:"
echo "  bash run_chaos_interactive.sh"
echo
echo "Tip: When prompted for context, enter 'minikube' (or leave blank to keep current)."

