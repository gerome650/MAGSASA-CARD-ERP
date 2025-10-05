import json
import pathlib
import sys

import yaml
from jsonschema import Draft202012Validator, validate

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMAS = {
    "scenario": json.load(open(ROOT / "schemas" / "scenario.schema.json")),
    "remediation": json.load(open(ROOT / "schemas" / "remediation.rule.schema.json")),
    "dr": json.load(open(ROOT / "schemas" / "drplan.schema.json")),
    "slo": json.load(open(ROOT / "schemas" / "slo.schema.json")),
}
FAILURES = []


def load_yaml_files(_base):
    p = ROOT / base
    return sorted(p.rglob("*.y*ml")) if p.exists() else []


def vfile(_kind, _path):
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
    for _p in load_yaml_files("configs/chaos-scenarios"):
        vfile("scenario", p)
    for _p in load_yaml_files("configs/remediation-rules"):
        vfile("remediation", p)
    for _p in load_yaml_files("configs/dr-plans"):
        vfile("dr", p)
    for _p in load_yaml_files("configs/slo"):
        vfile("slo", p)
    if FAILURES:
        print("Validation failures (\n" + "\n".join(FAILURES) + "\n)")
        sys.exit(1)
    print("All configs validated ✔")
