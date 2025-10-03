import sys, json, pathlib
from jsonschema import validate, Draft202012Validator
import yaml
ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMAS = {
    'scenario': json.load(open(ROOT/ 'schemas' / 'scenario.schema.json')),
    'remediation': json.load(open(ROOT/ 'schemas' / 'remediation.rule.schema.json')),
    'dr': json.load(open(ROOT/ 'schemas' / 'drplan.schema.json')),
    'slo': json.load(open(ROOT/ 'schemas' / 'slo.schema.json')),
}
FAILURES = []
def load_yaml_files(base):
    p = ROOT / base
    return sorted([f for f in p.rglob('*.y*ml')]) if p.exists() else []
def vfile(kind, path):
    data = yaml.safe_load(open(path))
    try:
        validate(instance=data, schema=SCHEMAS[kind], cls=Draft202012Validator)
    except Exception as e:
        FAILURES.append(f"[SCHEMA] {kind}: {path} -> {e}")
        return
    if kind == 'scenario':
        br = (data.get('blastRadius') or {})
        if (br.get('maxConcurrentTargets') or 0) > 1 and 'prod' in str(path):
            FAILURES.append(f"[SEMANTIC] {path}: prod scenarios must limit maxConcurrentTargets <= 1")
        if not (data.get('validation') or {}).get('sloChecks'):
            FAILURES.append(f"[SEMANTIC] {path}: missing validation.sloChecks")
        if not data.get('schedule'):
            FAILURES.append(f"[SEMANTIC] {path}: missing schedule (cron/ci)")
    if kind == 'remediation':
        g = data.get('guardrails') or {}
        if 'backoff' not in g or 'rateLimit' not in g:
            FAILURES.append(f"[SEMANTIC] {path}: guardrails.backoff and guardrails.rateLimit required")
    if kind == 'dr':
        meta = data.get('metadata') or {}
        if not meta.get('rtoTarget') or not meta.get('rpoTarget'):
            FAILURES.append(f"[SEMANTIC] {path}: require rtoTarget and rpoTarget")
if __name__ == '__main__':
    for p in load_yaml_files('configs/chaos-scenarios'): vfile('scenario', p)
    for p in load_yaml_files('configs/remediation-rules'): vfile('remediation', p)
    for p in load_yaml_files('configs/dr-plans'): vfile('dr', p)
    for p in load_yaml_files('configs/slo'): vfile('slo', p)
    if FAILURES:
        print("Validation failures (\n" + "\n".join(FAILURES) + "\n)")
        sys.exit(1)
    print("All configs validated ✔")
