import json
import pathlib
import sys

import yaml
from jsonschema import Draft202012Validator, validate

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Load schemas with context managers
with open(ROOT / "schemas" / "scenario.schema.json") as f:
    scenario_schema = json.load(f)
with open(ROOT / "schemas" / "remediation.rule.schema.json") as f:
    remediation_schema = json.load(f)
with open(ROOT / "schemas" / "drplan.schema.json") as f:
    dr_schema = json.load(f)
with open(ROOT / "schemas" / "slo.schema.json") as f:
    slo_schema = json.load(f)

SCHEMAS = {
    "scenario": scenario_schema,
    "remediation": remediation_schema,
    "dr": dr_schema,
    "slo": slo_schema,
}
FAILURES = []


def load_yaml_files(base):
    p = ROOT / base
    return sorted(p.rglob("*.y*ml")) if p.exists() else []


def vfile(kind, path):
    with open(path) as f:
        data = yaml.safe_load(f)
    try:
        validate(instance=data, schema=SCHEMAS[kind], cls=Draft202012Validator)
    except Exception as e:
        FAILURES.append(f"[SCHEMA] {kind}: {path} -> {e}")
        return
    if kind == "scenario":
        br = data.get("blastRadius") or {}
        if (br.get("maxConcurrentTargets") or 0) > 1 and "prod" in str(path):
            FAILURES.append(
                f"[SEMANTIC] {path}: prod scenarios must limit maxConcurrentTargets <= 1"
            )
        if not (data.get("validation") or {}).get("sloChecks"):
            FAILURES.append(f"[SEMANTIC] {path}: missing validation.sloChecks")
        if not data.get("schedule"):
            FAILURES.append(f"[SEMANTIC] {path}: missing schedule (cron/ci)")
    if kind == "remediation":
        g = data.get("guardrails") or {}
        if "backoff" not in g or "rateLimit" not in g:
            FAILURES.append(
                f"[SEMANTIC] {path}: guardrails.backoff and guardrails.rateLimit required"
            )
    if kind == "dr":
        meta = data.get("metadata") or {}
        if not meta.get("rtoTarget") or not meta.get("rpoTarget"):
            FAILURES.append(f"[SEMANTIC] {path}: require rtoTarget and rpoTarget")


if __name__ == "__main__":
    for p in load_yaml_files("configs/chaos-scenarios"):
        vfile("scenario", p)
    for p in load_yaml_files("configs/remediation-rules"):
        vfile("remediation", p)
    for p in load_yaml_files("configs/dr-plans"):
        vfile("dr", p)
    for p in load_yaml_files("configs/slo"):
        vfile("slo", p)
    if FAILURES:
        print("Validation failures (\n" + "\n".join(FAILURES) + "\n)")
        sys.exit(1)
    print("All configs validated ✔")
