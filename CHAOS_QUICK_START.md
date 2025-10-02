# 🚀 Chaos Engineering - Quick Start

Get started with chaos testing in 5 minutes!

## Prerequisites Check

```bash
# 1. Verify Python 3.11+
python3 --version

# 2. Install dependencies
pip install -r requirements.txt

# 3. Make scripts executable
chmod +x deploy/chaos_injector.py
chmod +x deploy/resilience_validator.py
chmod +x deploy/run_chaos_tests.sh
```

## Option A: Automated (Recommended) ⚡

```bash
# Start your application first
cd src && python main.py &

# Wait for service to be ready (check health)
curl http://localhost:8000/api/health

# Run complete chaos test suite
cd ..
./deploy/run_chaos_tests.sh
```

That's it! The script will:
1. ✅ Check service health
2. 🔥 Run chaos injection
3. 📊 Validate resilience
4. 📄 Generate report

## Option B: Manual Control 🎮

### Step 1: Start Application
```bash
cd src
python main.py &
cd ..
```

### Step 2: Run Chaos Injection
```bash
python deploy/chaos_injector.py \
  --config deploy/chaos_scenarios.yml \
  --target http://localhost:8000 \
  --output deploy/chaos_results.json
```

### Step 3: Validate Resilience
```bash
python deploy/resilience_validator.py \
  --target http://localhost:8000 \
  --chaos-results deploy/chaos_results.json \
  --report deploy/chaos_report.md \
  --fail-on-violation
```

### Step 4: View Report
```bash
cat deploy/chaos_report.md
```

## Safety First: Dry Run 🛡️

Test without actual chaos:

```bash
python deploy/chaos_injector.py \
  --config deploy/chaos_scenarios.yml \
  --target http://localhost:8000 \
  --dry-run
```

## Different Intensities 🎚️

```bash
# Light (smoke test) - ~5 minutes
./deploy/run_chaos_tests.sh --intensity smoke

# Standard (recommended) - ~15 minutes
./deploy/run_chaos_tests.sh --intensity standard

# Heavy (stress test) - ~25 minutes
./deploy/run_chaos_tests.sh --intensity stress
```

## View Results 📊

```bash
# View generated report
cat deploy/chaos_report.md

# View JSON results
cat deploy/chaos_results.json | python -m json.tool

# View validation results
cat deploy/resilience_validation.json | python -m json.tool
```

## Troubleshooting 🔧

### Service health check fails
```bash
# Check if service is running
curl http://localhost:8000/api/health

# Check logs
tail -f src/logs/*.log
```

### Permission errors
```bash
# Make scripts executable
chmod +x deploy/*.py deploy/*.sh
```

### Missing dependencies
```bash
# Install requirements
pip install -r requirements.txt

# Optional: Install stress-ng
sudo apt-get install stress-ng  # Linux
brew install stress-ng          # macOS
```

## Understanding Output 📈

### Exit Codes
- `0` = All tests passed ✅
- `1` = SLO violations or errors ❌

### Key Metrics
- **MTTR**: Time to recover (target: ≤30s)
- **Error Rate**: Failed requests % (target: ≤5%)
- **Availability**: Uptime % (target: ≥95%)
- **Latency Degradation**: Slowdown (target: ≤500ms)

## What's Next? 🎯

1. **Review Report**: Check `deploy/chaos_report.md`
2. **Fix Issues**: Address any SLO violations
3. **Iterate**: Run again after fixes
4. **Automate**: Let CI/CD run tests automatically

## Need Help? 📚

- **Quick Reference**: `deploy/README_CHAOS.md`
- **Full Guide**: `docs/CHAOS_ENGINEERING_GUIDE.md`
- **Completion Report**: `STAGE_6.5_COMPLETION_REPORT.md`

## CI/CD Integration 🤖

Tests run automatically on:
- Pull requests
- Nightly at 2 AM
- Manual trigger via GitHub Actions

Manual trigger:
1. Go to GitHub Actions
2. Select "Chaos Engineering Tests"
3. Click "Run workflow"
4. Choose intensity level

---

**🎉 You're ready to test system resilience!**

Start with: `./deploy/run_chaos_tests.sh`

