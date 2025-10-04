# Chaos Dependency Sentinel Report

**Generated:** chaos_dependency_sentinel.py
**Scan Directories:** deploy, scripts, observability
**Requirements Files:** requirements.txt, observability/observability_requirements.txt

## Summary

- **Total Files Scanned:** 14
- **Files with Missing Dependencies:** 14
- **Total Missing Dependencies:** 6

## Missing Dependencies by File

### `deploy/chaos_injector.py`

- `PyYAML>=6.0.2`

### `deploy/load_test.py`

- `psutil>=1.0.0`
- `PyYAML>=6.0.2`

### `deploy/port_detector.py`

- `psutil>=1.0.0`

### `deploy/resilience_validator.py`

- `PyYAML>=6.0.2`

### `observability/ai_agent/cli.py`

- `PyYAML>=6.0.2`

### `observability/ai_agent/webhook_server.py`

- `fastapi>=1.0.0`
- `pydantic>=1.0.0`
- `uvicorn>=1.0.0`
- `PyYAML>=6.0.2`

### `observability/tracing/otel_tracer.py`

- `opentelemetry-api>=1.21.0`

### `scripts/analyze_ci_failure.py`

- `PyYAML>=6.0.2`

### `scripts/render_roadmap.py`

- `PyYAML>=6.0.2`

### `scripts/slo_ingest.py`

- `PyYAML>=6.0.2`

### `scripts/validate_alert_rules.py`

- `PyYAML>=6.0.2`

### `scripts/validate_chaos_local.py`

- `PyYAML>=6.0.2`

### `scripts/validate_configs.py`

- `PyYAML>=6.0.2`

### `scripts/verify_stage_readiness.py`

- `PyYAML>=6.0.2`


## Recommendations

1. Run with `--fix` to automatically add missing dependencies to requirements files
2. Run with `--install` to automatically install missing packages
3. Review auto-added dependencies and adjust versions as needed
4. Consider pinning dependencies to specific versions for reproducibility

## Auto-Fix Command

```bash
python scripts/chaos_dependency_sentinel.py --fix --install
```
