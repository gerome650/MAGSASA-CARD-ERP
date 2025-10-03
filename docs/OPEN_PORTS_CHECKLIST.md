# Open ports for remote k3s runner

1) Cloud firewall:
   - Allow TCP **22** (SSH) and **6443** (Kubernetes API) from your public IP (`curl ifconfig.me`).
2) VM firewall:
   - UFW: `sudo ufw allow 22/tcp && sudo ufw allow 6443/tcp && sudo ufw status`
   - firewalld: add ports 22 and 6443, then reload.
3) Verify from your laptop:
   - `bash scripts/wait_for_ports.sh <IP> 22 6443`
4) Proceed:
   - `bash scripts/fix_kube_and_apply.sh`

