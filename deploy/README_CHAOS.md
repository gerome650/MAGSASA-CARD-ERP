# Chaos Engineering Suite - Quick Reference

## 🚀 Quick Start

### Option 1: One-Command Execution (Recommended)

```bash
# Make script executable (first time only)
chmod +x deploy/run_chaos_tests.sh

# Run complete chaos test suite
./deploy/run_chaos_tests.sh
```

### Option 2: Manual Execution

```bash
# 1. Start your application
cd src && python main.py &

# 2. Run chaos injection
python deploy/chaos_injector.py \
  --config deploy/chaos_scenarios.yml \
  --target http://localhost:8000 \
  --output deploy/chaos_results.json

# 3. Validate resilience
python deploy/resilience_validator.py \
  --chaos-results deploy/chaos_results.json \
  --report deploy/chaos_report.md \
  --fail-on-violation

# 4. View report
cat deploy/chaos_report.md
```

## 📋 Common Commands

### Dry Run (Safe Testing)
```bash
python deploy/chaos_injector.py --dry-run
```

### Run Specific Scenario
```bash
python deploy/chaos_injector.py \
  --scenario "Medium CPU Stress"
```

### Custom Target URL
```bash
./deploy/run_chaos_tests.sh \
  --target http://staging.example.com
```

### Different Intensities
```bash
# Light scenarios only
./deploy/run_chaos_tests.sh --intensity smoke

# Standard scenarios
./deploy/run_chaos_tests.sh --intensity standard

# Heavy stress testing
./deploy/run_chaos_tests.sh --intensity stress
```

## 📊 Output Files

| File | Description |
|------|-------------|
| `chaos_results.json` | Raw chaos injection results |
| `resilience_validation.json` | SLO compliance validation |
| `chaos_report.md` | Human-readable report with recommendations |

## 🎯 Default SLO Targets

- **MTTR**: ≤ 30 seconds
- **Error Rate**: ≤ 5%
- **Availability**: ≥ 95%
- **Latency Degradation**: ≤ 500ms
- **Recovery Time**: ≤ 10 seconds

## 🔥 Failure Types

1. **CPU Exhaustion** - Stress CPU cores
2. **Memory Leak** - Memory pressure testing
3. **Network Delay** - Latency injection
4. **Packet Loss** - Network reliability
5. **Container Crash** - Recovery testing
6. **Database Down** - DB failure simulation
7. **Disk Stress** - I/O pressure

## 🚨 Troubleshooting

### Service health check fails
```bash
curl http://localhost:8000/api/health
```

### stress-ng not available
```bash
# Linux
sudo apt-get install stress-ng

# macOS
brew install stress-ng

# Or just use Python fallback (automatic)
```

### View detailed logs
```bash
python deploy/chaos_injector.py --verbose
```

## 📚 Documentation

For comprehensive documentation, see:
- **[Chaos Engineering Guide](../docs/CHAOS_ENGINEERING_GUIDE.md)** - Complete guide
- **[Stage 6.5 Report](../STAGE_6.5_COMPLETION_REPORT.md)** - Implementation details

## 🔧 Configuration

Edit `deploy/chaos_scenarios.yml` to:
- Add custom scenarios
- Adjust intensity levels
- Modify SLO targets
- Configure safety settings

## 🤖 CI/CD Integration

Chaos tests run automatically on:
- Pull requests to main/develop
- Manual workflow dispatch
- Nightly scheduled runs (2 AM)

Manual trigger:
1. Go to GitHub Actions
2. Select "Chaos Engineering Tests"
3. Click "Run workflow"
4. Choose intensity and target

## ⚡ Pro Tips

1. **Start small**: Run smoke tests first
2. **Use dry-run**: Test configurations safely
3. **Monitor actively**: Watch system during chaos
4. **Review reports**: Learn from resilience metrics
5. **Iterate**: Gradually increase intensity

## 📞 Support

- Review troubleshooting in main guide
- Check GitHub Issues
- Contact DevOps team

---

**Quick Links**:
- [Full Documentation](../docs/CHAOS_ENGINEERING_GUIDE.md)
- [Scenarios Config](chaos_scenarios.yml)
- [GitHub Workflow](../.github/workflows/chaos.yml)

