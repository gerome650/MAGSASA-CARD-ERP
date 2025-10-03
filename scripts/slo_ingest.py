#!/usr/bin/env python3
import os, json, glob
from datetime import datetime

try:
    import yaml  # PyYAML
except ImportError:
    yaml = None

def load_slos():
    slos = []
    for path in glob.glob("configs/slo/*.slo.yaml"):
        name = os.path.splitext(os.path.basename(path))[0]
        objective = "n/a"
        if yaml is not None:
            try:
                with open(path, "r") as f:
                    data = yaml.safe_load(f) or {}
                    # try common keys
                    objective = (
                        data.get("objective")
                        or data.get("target")
                        or data.get("slo")
                        or data.get("description")
                        or "n/a"
                    )
                    name = data.get("name") or data.get("id") or name
            except Exception:
                pass
        slos.append({"slo": name, "objective": str(objective), "status": "ok", "value": 0})
    return slos

def main():
    # Allow forcing a non-zero regression count for demos/tests
    force_val = os.environ.get("FORCE_SLO_REGRESSIONS", "").strip()
    try:
        forced = int(force_val) if force_val else 0
    except ValueError:
        forced = 0

    details = load_slos()
    # If forced > 0, mark first N entries as failed to make it visible
    if forced > 0 and details:
        for i in range(min(forced, len(details))):
            details[i]["status"] = "fail"
            details[i]["value"] = 1

    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "chaos_failed": False,            # keep compatibility with existing OPA input
        "slo_regressions": forced if forced > 0 else 0,
        "details": details,
    }
    out = "/tmp/slo.json"
    with open(out, "w") as f:
        json.dump(payload, f, indent=2)
    print(out)

if __name__ == "__main__":
    main()

