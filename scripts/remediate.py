#!/usr/bin/env python3
import datetime
import os
import shlex
import subprocess
import sys

NS = os.environ.get("NAMESPACE", "staging-apps")
DEPLOY = os.environ.get("DEPLOYMENT", "demo")
ACTION = os.environ.get("ACTION", "restart")  # restart|scale
SCALE_TO = os.environ.get("SCALE_TO", "2")

LOG = "/tmp/remediation.log"


def run(cmd):
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def log(line):
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    with open(LOG, "a") as f:
        f.write(f"[{ts}] {line}\n")


def main():
    log(
        f"Remediator start: ns={NS} deploy={DEPLOY} action={ACTION} scale_to={SCALE_TO}"
    )
    # Check deployment exists
    rc, out, err = run(
        f"kubectl -n {shlex.quote(NS)} get deploy {shlex.quote(DEPLOY)} -o jsonpath='{{.metadata.name}}'"
    )
    if rc != 0:
        log(f"ERROR: deployment {DEPLOY} not found in ns {NS}: {err or out}")
        print(LOG)
        sys.exit(0)  # no-op in CI if demo isn't deployed

    log(f"Deployment {DEPLOY} found in namespace {NS}")

    if ACTION == "restart":
        log(f"Action: restart deployment {DEPLOY}")
        rc, out, err = run(
            f"kubectl -n {shlex.quote(NS)} rollout restart deploy/{shlex.quote(DEPLOY)}"
        )
        if rc == 0:
            log(f"SUCCESS: restart initiated - {out}")
        else:
            log(f"ERROR: restart failed - {err or out}")

    elif ACTION == "scale":
        log(f"Action: scale deployment {DEPLOY} to {SCALE_TO}")
        rc, out, err = run(
            f"kubectl -n {shlex.quote(NS)} scale deploy/{shlex.quote(DEPLOY)} --replicas={shlex.quote(SCALE_TO)}"
        )
        if rc == 0:
            log(f"SUCCESS: scaled to {SCALE_TO} replicas - {out}")
        else:
            log(f"ERROR: scale failed - {err or out}")

    else:
        log(f"ERROR: unknown action '{ACTION}'")
        print(LOG)
        sys.exit(1)

    log("Remediator complete")
    print(LOG)


if __name__ == "__main__":
    main()
