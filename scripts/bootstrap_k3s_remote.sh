#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash scripts/bootstrap_k3s_remote.sh <USER>@<HOST> </path/to/ssh_key>
# Example:
#   bash scripts/bootstrap_k3s_remote.sh ubuntu@203.0.113.10 ~/.ssh/id_ed25519

REMOTE="${1:-}"
SSH_KEY="${2:-}"

if [[ -z "$REMOTE" || -z "$SSH_KEY" ]]; then
  echo "Usage: $0 <USER>@<HOST> </path/to/ssh_key>" >&2
  exit 2
fi

if ! command -v ssh >/dev/null 2>&1 || ! command -v scp >/dev/null 2>&1; then
  echo "ERROR: ssh/scp required on your laptop." >&2
  exit 1
fi

HOST="${REMOTE#*@}"

echo "==> Installing k3s on $REMOTE (this uses the official install script)"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=accept-new "$REMOTE" \
  'curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server --disable traefik" sh -'

echo "==> Waiting for kubeconfig to appear..."
ssh -i "$SSH_KEY" "$REMOTE" 'while [ ! -s /etc/rancher/k3s/k3s.yaml ]; do sleep 1; done'

TMPCFG="$(mktemp)"
echo "==> Copying kubeconfig locally"
scp -i "$SSH_KEY" "$REMOTE:/etc/rancher/k3s/k3s.yaml" "$TMPCFG"

echo "==> Rewriting server address to public IP ($HOST)"
# Replace 127.0.0.1 in kubeconfig with public address
sed -i '' -e "s#https://127.0.0.1:6443#https://$HOST:6443#g" "$TMPCFG" 2>/dev/null || \
sed -i -e "s#https://127.0.0.1:6443#https://$HOST:6443#g" "$TMPCFG"

# Install locally under ~/.kube
mkdir -p "$HOME/.kube"
CTX_NAME="k3s-$HOST"
DEST="$HOME/.kube/config.$CTX_NAME"

mv "$TMPCFG" "$DEST"
chmod 600 "$DEST"

# Merge/Set context without clobbering existing config
export KUBECONFIG="$DEST:${KUBECONFIG:-$HOME/.kube/config}"
kubectl config view --merge --flatten > "$HOME/.kube/config.merged"
mv "$HOME/.kube/config.merged" "$HOME/.kube/config"

# Set a friendly context name
kubectl config rename-context "default" "$CTX_NAME" >/dev/null 2>&1 || true
kubectl config use-context "$CTX_NAME"

echo "==> Current contexts:"
kubectl config get-contexts

# Hand off to chaos interactive runner
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
RUNNER="$ROOT/run_chaos_interactive.sh"
if [[ -f "$RUNNER" ]]; then
  echo
  echo "Next step: run your interactive chaos helper on this context:"
  echo "  bash run_chaos_interactive.sh"
else
  echo "WARN: $RUNNER not found. Ensure Stage 6.6 scripts exist."
fi

echo "==> Done. Context set to: $CTX_NAME"

