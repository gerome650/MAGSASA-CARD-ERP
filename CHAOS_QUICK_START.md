# Chaos Engineering Quick Start Guide

**5-minute setup guide for MAGSASA-CARD-ERP Chaos Engineering Suite**

## 🚀 Quick Setup

### 1. Prerequisites (30 seconds)

```bash
# Install Python dependencies
pip install aiohttp pyyaml requests psutil

# Optional: Install system tools for advanced scenarios
sudo apt-get install stress-ng  # For CPU/memory stress
sudo apt-get install iproute2   # For network chaos (tc command)
```

### 2. Validate Installation (30 seconds)

```bash
# Run validation script
python validate_chaos_suite.py

# Expected output: ✅ All critical checks passed!
```

### 3. Make Scripts Executable (15 seconds)

```bash
chmod +x deploy/*.py deploy/*.sh
```

### 4. Start Your Application (60 seconds)

```bash
# Start the MAGSASA-CARD-ERP application
cd src
python main.py

# In another terminal, verify it's running
curl http://localhost:8000/api/health
```

### 5. Run First Chaos Test (3 minutes)

```bash
# Dry run (safe simulation)
./deploy/run_chaos_tests.sh --dry-run

# Real test (light intensity)
./deploy/run_chaos_tests.sh --intensity smoke
```

## 📊 Understanding Results

### Success Indicators
- ✅ All chaos scenarios completed
- ✅ SLO validation passed
- ✅ Recovery time < 30 seconds
- ✅ Error rate < 5%
- ✅ Availability > 95%

### Failure Indicators
- ❌ SLO violations detected
- ❌ Recovery time > 30 seconds
- ❌ High error rates
- ❌ Service unavailable

### Reports Generated
- `deploy/chaos_report.md` - Human-readable summary
- `deploy/chaos_results.json` - Machine-readable data
- `deploy/resilience_validation.json` - SLO validation results

## 🔧 Common Commands

### Basic Testing
```bash
# Quick smoke test
./deploy/run_chaos_tests.sh --intensity smoke

# Standard test suite
./deploy/run_chaos_tests.sh --intensity standard

# Heavy stress test
./deploy/run_chaos_tests.sh --intensity stress
```

### Individual Components
```bash
# Chaos injection only
python deploy/chaos_injector.py --dry-run

# SLO validation only
python deploy/resilience_validator.py --fail-on-violation

# Export metrics
python deploy/chaos_metrics_exporter.py --output metrics.prom
```

### Custom Scenarios
```bash
# Run specific scenario
python deploy/chaos_injector.py --scenario "Heavy Network Delay"

# Custom target URL
./deploy/run_chaos_tests.sh --target http://staging.example.com
```

## 🎯 SLO Targets

| Metric | Target | Description |
|--------|--------|-------------|
| MTTR | ≤ 30s | Mean Time To Recovery |
| Error Rate | ≤ 5% | Failed requests during chaos |
| Availability | ≥ 95% | System uptime during chaos |
| Latency Degradation | ≤ 500ms | Performance impact |
| Recovery Time | ≤ 10s | Time to return to normal |

## 🚨 Troubleshooting

### Service Not Starting
```bash
# Check if port 8000 is in use
lsof -i :8000

# Check application logs
cat app.log
```

### Permission Errors
```bash
# Fix script permissions
chmod +x deploy/*.py deploy/*.sh
```

### Missing Dependencies
```bash
# Install missing packages
pip install aiohttp pyyaml requests psutil

# Check installation
python -c "import aiohttp, yaml, requests, psutil; print('✅ All dependencies installed')"
```

### Validation Failures
```bash
# Run validation to identify issues
python validate_chaos_suite.py

# Fix any missing files or configuration issues
```

## 📈 Next Steps

### 1. Integrate with CI/CD
Add to your GitHub Actions workflow:
```yaml
- name: Chaos Engineering Tests
  run: ./deploy/run_chaos_tests.sh --intensity smoke
```

### 2. Set Up Monitoring
Export metrics to Prometheus:
```bash
python deploy/chaos_metrics_exporter.py --push \
  --pushgateway-url http://prometheus:9091
```

### 3. Customize Scenarios
Edit `deploy/chaos_scenarios.yml` to add your own scenarios:
```yaml
scenarios:
  - name: "Custom Test"
    type: "cpu_exhaust"
    intensity: "medium"
    duration: 60
```

### 4. Team Training
- Share this guide with your team
- Run chaos tests regularly
- Monitor trends over time
- Improve based on results

## 🆘 Getting Help

### Documentation
- `docs/CHAOS_ENGINEERING_GUIDE.md` - Comprehensive guide
- `STAGE_6.5_README.md` - Project overview
- `deploy/README_CHAOS.md` - Command reference

### Validation
- `python validate_chaos_suite.py` - Check installation
- `./deploy/run_chaos_tests.sh --dry-run` - Safe testing

### Support
- Check logs in `deploy/` directory
- Review generated reports
- Run validation script for diagnostics

---

**🎉 You're ready to start chaos engineering!**

Run your first test: `./deploy/run_chaos_tests.sh --intensity smoke`