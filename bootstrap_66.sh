#!/usr/bin/env bash
set -euo pipefail
REPO_DIR="${REPO_DIR:-$PWD/agsense-resilience}"
DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"
FEATURE_BRANCH="${FEATURE_BRANCH:-stage-6.6-bootstrap}"
REMOTE_URL="${REMOTE_URL:-}"
PY=python3
echo "=> Bootstrapping Stage 6.6 into: $REPO_DIR"
mkdir -p "$REPO_DIR"
cd "$REPO_DIR"
if [ ! -d .git ]; then git init -b "$DEFAULT_BRANCH"; fi
current_branch="$(git rev-parse --abbrev-ref HEAD)"
if [ "$current_branch" != "$FEATURE_BRANCH" ]; then git checkout -B "$FEATURE_BRANCH"; fi
mkdir -p scripts schemas \
  configs/chaos-scenarios configs/remediation-rules configs/dr-plans configs/slo \
  platform/gatekeeper/policies/tests infra/k8s \
  .github/workflows docs/roadmap docs/adr ops/runbooks \
  platform/chaos/orchestrator platform/remediation/rule-engine platform/dr/orchestrator \
  pipelines/github tools/cli
cat > .gitignore <<'EOF'
.venv/
__pycache__/
*.pyc
.DS_Store
dist/
build/
.ops-cache/
# Chaos outputs
deploy/chaos_results_*/
EOF
cat > .yamllint <<'EOF'
extends: default
rules:
  line-length:
    max: 160
    allow-non-breakable-words: true
ignore: |
  ops/runbooks/
EOF
cat > README.md <<'EOF'
# Stage 6.6 — Continuous Chaos, Auto-Remediation, DR, and CI/CD Enforcement
**Scope**
- Continuous chaos automation (cron + CI)
- Auto-remediation engine (rules + guardrails)
- Disaster recovery (DR) simulations + runbook generation
- CI/CD enforcement (block on SLO regressions / chaos failures)
**Local usage**
make setup
make lint
make validate
make opa-test
**Docs protocol (repo-first)**
- docs/ (ADRs, roadmap)
- ops/runbooks/ (generated)
- configs/ (scenarios, SLOs, rules, DR plans)
EOF
cat > Makefile <<'EOF'
.PHONY: setup lint validate opa-test roadmap
setup:
	python3 -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -r requirements.txt
lint:
	. .venv/bin/activate && yamllint configs
validate:
	. .venv/bin/activate && python scripts/validate_configs.py
opa-test:
	opa test platform/gatekeeper/policies -v
roadmap:
	. .venv/bin/activate && python scripts/render_roadmap.py
EOF
cat > requirements.txt <<'EOF'
yamllint==1.35.1
PyYAML==6.0.2
jsonschema==4.22.0
Jinja2==3.1.4
EOF
cat > scripts/validate_configs.py <<'EOF'
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
EOF
cat > scripts/render_roadmap.py <<'EOF'
import yaml, pathlib
from jinja2 import Template
ROOT = pathlib.Path(__file__).resolve().parents[1]
rf = ROOT/'docs'/'roadmap'/'roadmap.yaml'
if not rf.exists(): raise SystemExit(0)
roadmap = yaml.safe_load(open(rf))
md = Template("# ROADMAP\n{% for i in roadmap %}## {{i.id}} — {{i.title}}\n- **Owner:** {{i.owner}}\n- **Start:** {{i.start}}\n- **Target:** {{i.target}}\n- **Status:** {{i.status}}\n- **KPIs:** {% for k in i.kpis %}`{{k}}`{% if not loop.last %}, {% endif %}{% endfor %}\n- **Links:** {% for k,v in i.links.items() %}[{{k}}]({{v}}){% if not loop.last %}, {% endif %}{% endfor %}\n{% endfor %}").render(roadmap=roadmap)
open(ROOT/'docs'/'ROADMAP.md','w').write(md)
print("Rendered docs/ROADMAP.md")
EOF
cat > schemas/scenario.schema.json <<'EOF'
{ "$schema":"https://json-schema.org/draft/2020-12/schema", "type":"object",
  "required":["apiVersion","kind","metadata","injection","validation"],
  "properties":{
    "apiVersion":{"const":"chaos.ag/1"},
    "kind":{"const":"Scenario"},
    "metadata":{"type":"object","required":["name"],
      "properties":{"name":{"type":"string"},"owners":{"type":"array","items":{"type":"string"}}}},
    "schedule":{"type":["object","null","string","array"]},
    "blastRadius":{"type":"object"},
    "injection":{"type":"object","required":["type"],"properties":{"type":{"type":"string"}}},
    "validation":{"type":"object","required":["sloChecks"],
      "properties":{"healthEndpoints":{"type":"array"},"sloChecks":{"type":"array","items":{"type":"object"}}}},
    "evidence":{"type":"object"}
}}
EOF
cat > schemas/remediation.rule.schema.json <<'EOF'
{ "$schema":"https://json-schema.org/draft/2020-12/schema","type":"object",
  "required":["apiVersion","kind","metadata","conditions","actions"],
  "properties":{"apiVersion":{"const":"remediation.ag/1"},"kind":{"const":"Rule"},
    "metadata":{"type":"object","required":["name"]},"conditions":{"type":"object"},
    "actions":{"type":"object"},"guardrails":{"type":"object"},"observability":{"type":"object"}}}
EOF
cat > schemas/drplan.schema.json <<'EOF'
{ "$schema":"https://json-schema.org/draft/2020-12/schema","type":"object",
  "required":["apiVersion","kind","metadata","steps"],
  "properties":{"apiVersion":{"const":"dr.ag/1"},"kind":{"const":"DRPlan"},
    "metadata":{"type":"object","required":["name","rtoTarget","rpoTarget"]},
    "steps":{"type":"array","items":{"type":"object","required":["name","action"]}}}}
EOF
cat > schemas/slo.schema.json <<'EOF'
{ "$schema":"https://json-schema.org/draft/2020-12/schema","type":"object",
  "required":["service","objective","target","window"],
  "properties":{"service":{"type":"string"},"objective":{"type":"string"},
    "target":{"type":["number","string"]},"window":{"type":"string"},"baseline":{"type":"object"}}}
EOF
cat > configs/chaos-scenarios/pod-kill-api.scenario.yaml <<'EOF'
apiVersion: chaos.ag/1
kind: Scenario
metadata:
  name: pod-kill-api
  owners: [platform-resilience]
schedule:
  when: ["cron: 0 3 * * *", "ci:on-pr", "ci:post-deploy"]
blastRadius:
  namespaceAllowlist: ["stg-api", "prod-api"]
  maxConcurrentTargets: 1
  dryRun: false
injection:
  type: k8s.podKill
  selector:
    labels: { app: api-gateway }
  disruption:
    killPercentage: 30
validation:
  healthEndpoints:
    - url: https://api.example.com/health
      method: GET
      timeout: 5s
  sloChecks:
    - sloRef: latency-p99-api
      maxRegression: 5%
    - sloRef: error-rate-api
      absoluteMax: 0.5%
evidence:
  store: s3://resilience-artifacts/${{ env }}/${{ run.id }}/
  redact: ["token", "password"]
EOF
cat > configs/remediation-rules/api-restart.rule.yaml <<'EOF'
apiVersion: remediation.ag/1
kind: Rule
metadata:
  name: api-auto-restart
  owners: [sre]
conditions:
  any:
    - metric: "http_error_rate{service='api-gateway'}"
      for: 2m
      op: ">"
      value: 0.02
    - alert: "KubePodCrashLooping"
      for: 3m
actions:
  sequence:
    - type: k8s.rolloutRestart
      target: deploy/api-gateway
      waitReady: 5m
      maxUnavailable: 1
    - type: verify.slo
      references: [error-rate-api]
guardrails:
  changeFreeze:
    windows: ["Fri 18:00..Mon 08:00 TZ=America/Los_Angeles"]
    allowIf: ["severity >= P1", "on-call-approved"]
  backoff:
    initial: 30s
    max: 10m
    factor: 2.0
  rateLimit:
    actionsPerHour: 3
observability:
  annotate: [pagerduty, grafana]
  emitEvent: true
EOF
cat > configs/dr-plans/region-failover.dr.yaml <<'EOF'
apiVersion: dr.ag/1
kind: DRPlan
metadata:
  name: region-failover-usw2->use1
  rtoTarget: 30m
  rpoTarget: 5m
  owners: [platform-resilience, db-team]
steps:
  - name: freeze-deployments
    action: cicd.freeze
  - name: promote-read-replica
    action: db.failover
    params: { cluster: "orders", toRegion: "use1" }
  - name: switch-traffic
    action: traffic.shift
    params: { weightFrom: "usw2", weightTo: "use1", rampMins: 10 }
  - name: verify
    action: verify.healthAndSLO
    params: { endpointsRef: "critical" }
evidence:
  report:
    format: md
    publish:
      - git: "ops/runbooks/region-failover-usw2-use1.md"
      - s3:  "s3://resilience-artifacts/dr/${{ run.ts }}/"
EOF
cat > configs/slo/latency-p99-api.slo.yaml <<'EOF'
service: api-gateway
objective: p99_latency_ms
target: 450
window: 7d
baseline:
  source: "prom: histogram_quantile(0.99, rate(http_request_duration_ms_bucket{service='api-gateway'}[5m]))"
  keepHistory: 90d
EOF
cat > .github/workflows/resilience-gate.yml <<'EOF'
name: Resilience Gate
on:
  pull_request:
    types: [opened, synchronize, reopened]
jobs:
  gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Install deps
        run: |
          python -m pip install -U pip
          pip install -r requirements.txt
          if ! command -v opa >/dev/null 2>&1; then
            curl -L -o opa https://openpolicyagent.org/downloads/latest/opa_linux_amd64
            chmod +x ./opa && sudo mv ./opa /usr/local/bin/opa
          fi
      - name: Lint YAML
        run: yamllint configs
      - name: Validate configs
        run: python scripts/validate_configs.py
      - name: Policy tests
        run: opa test platform/gatekeeper/policies -v
      - name: Upload artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: resilience-artifacts
          path: |
            configs
            platform/gatekeeper/policies
EOF
cat > .github/workflows/docs-gate.yml <<'EOF'
name: Docs Gate
on: pull_request
jobs:
  docs_gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Enforce doc coupling
        run: |
          BASE=origin/${{ github.base_ref }}
          CHANGED=$(git diff --name-only $BASE...HEAD || true)
          if echo "$CHANGED" | egrep -q '^(platform/|configs/|infra/|pipelines/)'; then
            echo "$CHANGED" | egrep -q '^(docs/|ops/runbooks/)' || {
              echo "Docs required: code/config changed but no docs/runbooks updated."; exit 1; }
          fi
EOF
cat > platform/gatekeeper/policies/resilience.rego <<'EOF'
package resilience
default deny := false
deny[msg] { input.chaos_failed == true; msg := "Chaos failures detected" }
deny[msg] { input.slo_regressions > 0; msg := sprintf("%v SLO regression(s) detected", [input.slo_regressions]) }
EOF
cat > platform/gatekeeper/policies/tests/resilience_test.rego <<'EOF'
package resilience
import data.resilience.deny
test_deny_on_chaos_failure { input := {"chaos_failed": true, "slo_regressions": 0}; some msg; deny[msg] with input as input }
test_deny_on_slo_regressions { input := {"chaos_failed": false, "slo_regressions": 2}; some msg; deny[msg] with input as input }
test_allow_when_clean { input := {"chaos_failed": false, "slo_regressions": 0}; not deny[_] with input as input }
EOF
cat > infra/k8s/cron-chaos.yaml <<'EOF'
apiVersion: batch/v1
kind: CronJob
metadata: { name: chaos-nightly }
spec:
  schedule: "0 3 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: chaos-runner
          containers:
            - name: runner
              image: ghcr.io/agsense/resilience-runner:6.6
              args: ["run", "--registry", "/configs/chaos-scenarios", "--env", "staging"]
          restartPolicy: OnFailure
EOF
cat > docs/roadmap/roadmap.yaml <<'EOF'
- id: 6.6
  title: Continuous Chaos & Enforcement
  owner: platform-resilience
  start: 2025-10-03
  target: 2025-10-24
  status: in-progress
  kpis:
    - nightly_chaos_pass_rate >= 95%
    - MTTR_P2_down_by >= 40%
  links:
    configs: "configs/"
    runbooks: "ops/runbooks/"
EOF
cat > docs/adr/ADR-2025-10-03-repo-first-docs.md <<'EOF'
# ADR: Repo-First Documentation Protocol
**Context.** Notion integration is pending; artifacts/policies must be auditable and versioned.
**Decision.** The repo (configs/, docs/, ops/runbooks/) is the source of truth; CI gates enforce doc coupling.
**Consequences.** Faster iteration; consistent reviews; later optional one-way Notion sync.
EOF
touch ops/runbooks/.keep
echo "=> Setting up Python venv & installing deps"
$PY -m venv .venv; source .venv/bin/activate; pip install -U pip; pip install -r requirements.txt
if ! command -v opa >/dev/null 2>&1; then
  OS="$(uname -s)"; ARCH="$(uname -m)"; BIN="opa_linux_amd64"
  [ "$OS" = "Darwin" ] && BIN="opa_darwin_${ARCH}"
  curl -L -o opa "https://openpolicyagent.org/downloads/latest/${BIN}"; chmod +x ./opa; sudo mv ./opa /usr/local/bin/opa || mv ./opa /usr/local/bin/opa 2>/dev/null || true
fi
echo "=> Running lint/validate/tests"
make lint
$PY scripts/validate_configs.py
opa test platform/gatekeeper/policies -v
echo "=> Committing bootstrap"
git add -A
git commit -m "Stage 6.6: bootstrap scaffolding (schemas, gates, docs protocol)" || true
if [ -n "$REMOTE_URL" ]; then
  if ! git remote | grep -q '^origin$'; then git remote add origin "$REMOTE_URL"; fi
  git push -u origin "$FEATURE_BRANCH" || true
fi
echo "✅ Stage 6.6 bootstrap complete in $REPO_DIR"

