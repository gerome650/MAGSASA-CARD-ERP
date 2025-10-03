#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 2 ]]; then
  echo "Usage: bash scripts/ssh_probe.sh <PUBLIC_IP> </path/to/private_key>" >&2
  exit 2
fi
IP="$1"; KEY="$2"
[[ -f "$KEY" ]] || { echo "ERROR: key not found: $KEY"; exit 2; }
chmod 600 "$KEY" || true

echo "==> Checking port 22 on $IP ..."
if ! nc -vz "$IP" 22 2>/dev/null; then
  echo "ERROR: Port 22 not reachable. Open it in cloud firewall & VM firewall (ufw)." >&2
  exit 1
fi

USERS=(ubuntu ec2-user root admin centos opc debian)
OK_USER=""
for U in "${USERS[@]}"; do
  echo ">>> testing $U@$IP"
  if ssh -i "$KEY" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=6 -o BatchMode=yes "$U@$IP" 'echo OK' 2>/dev/null | grep -q '^OK$'; then
    OK_USER="$U"; break
  fi
done

if [[ -z "$OK_USER" ]]; then
  echo "ERROR: SSH failed for users: ${USERS[*]}."
  echo "Tips: verify IP/key; add your *.pub to ~/.ssh/authorized_keys on the VM; or try the provider's console."
  exit 1
fi

echo "✅ Success with user: $OK_USER"
echo "Next: bash scripts/bootstrap_k3s_remote.sh \"$OK_USER@$IP\" \"$KEY\""

