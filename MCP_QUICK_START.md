# 🚀 MCP Simulation Quick Start Guide

Get up and running with MCP (Model Context Protocol) simulation in 5 minutes.

---

## Prerequisites

- Python 3.10+ installed
- `uv` package manager ([install guide](https://github.com/astral-sh/uv))
- Git
- Terminal/shell access

---

## Step 1: Setup Environment (2 minutes)

```bash
# Clone the repository (if not already done)
cd /path/to/MAGSASA-CARD-ERP

# Install dependencies
make setup

# Verify installation
ags --version
# Output: AgSense CLI v0.1.0
```

---

## Step 2: Enable MCP Mode (30 seconds)

```bash
# Enable MCP feature flag
export AGS_MCP_ENABLED=true

# Verify it's enabled
echo $AGS_MCP_ENABLED
# Output: true
```

**💡 Tip:** Add this to your `~/.bashrc` or `~/.zshrc` to persist across sessions:
```bash
echo 'export AGS_MCP_ENABLED=true' >> ~/.zshrc
source ~/.zshrc
```

---

## Step 3: Validate Agent Readiness (1 minute)

```bash
# Run MCP readiness check
ags mcp-check
```

**Expected Output:**
```
╭───────────────────────────────────────────────╮
│ AgSense MCP Readiness Check                   │
╰───────────────────────────────────────────────╯

Environment Flag: AGS_MCP_ENABLED=✅ Enabled

┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Agent              ┃ Detected Stub ┃ Protocol Compliance ┃ Schema Validation ┃ Env Flag ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ agent-ingest       │      ✅       │         ✅          │        ✅         │    ✅    │
│ agent-retrieval    │      ✅       │         ✅          │        ✅         │    ✅    │
│ agent-scoring      │      ✅       │         ✅          │        ✅         │    ✅    │
│ agent-notify       │      ✅       │         ✅          │        ✅         │    ✅    │
│ agent-billing      │      ✅       │         ✅          │        ✅         │    ✅    │
└────────────────────┴───────────────┴─────────────────────┴───────────────────┴──────────┘

🎉 All 5 agents are fully MCP-ready!
```

✅ **All checks should show green checkmarks**

❌ **If any show red**, run:
```bash
make setup
ags mcp-check
```

---

## Step 4: Run Orchestrator Simulation (1 minute)

```bash
# Run all agents with request tracing
ags agent run all --trace
```

**Expected Output:**
```
╭──────────────────────────────────────────────╮
│ AgSense Agent Orchestrator Simulation        │
│ Running: all                                  │
╰──────────────────────────────────────────────╯

MCP Mode: ✅ Enabled

Testing 5 agent(s)...

🔄 Request Flow Trace
├── agent-ingest
│   ├── Request ID: req_a1b2c3d4
│   ├── Status: completed
│   ├── Latency: 215.43ms
│   └── Correlation ID: corr_x7y8z9w0
├── agent-retrieval
│   ├── Request ID: req_e5f6g7h8
│   ├── Status: completed
│   ├── Latency: 162.87ms
│   └── Correlation ID: corr_i9j0k1l2
...

📊 Agent Execution Results

Summary:
  • Total agents tested: 5
  • Successful: 5
  • Failed: 0
  • Average latency: 216.19ms

🎉 All agents executed successfully!
```

---

## Step 5: Inspect Logs (30 seconds)

Logs are output to stdout in JSON format with structured fields:

```bash
# Run and pipe to jq for pretty formatting
ags agent run all 2>&1 | grep "Agent request completed" | jq
```

**Example Log:**
```json
{
  "ts": "2025-10-05T14:23:45.123456Z",
  "agent": "agent-ingest",
  "request_id": "req_a1b2c3d4",
  "latency_ms": 215.43,
  "status": "ok",
  "message": "Processed by agent-ingest",
  "correlation_id": "corr_x7y8z9w0",
  "mcp_enabled": true,
  "transport": "stdio"
}
```

---

## 🎯 Common Commands

### Check System Health
```bash
ags health-check
```

### Run Individual Agent
```bash
# Run just the ingest agent
ags agent run agent-ingest --trace

# Run just the billing agent
ags agent run agent-billing --trace
```

### Run Tests
```bash
# Run all tests
ags test

# Or via make
make test
```

### View System Info
```bash
ags info
```

---

## 🔧 Troubleshooting

### Issue: `ags: command not found`

**Solution:**
```bash
# Reinstall dependencies
uv sync --dev

# Verify ags is installed
which ags
# Should output path to ags executable
```

### Issue: MCP adapters not found

**Solution:**
```bash
# Ensure you're in the project root
cd /path/to/MAGSASA-CARD-ERP

# Check packages directory exists
ls -la packages/

# Should see: agent-ingest, agent-retrieval, etc.
```

### Issue: Import errors

**Solution:**
```bash
# Clear Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Reinstall
uv sync --dev

# Verify imports
uv run python -c "from agsense_core.models.contracts import AgentInput"
```

### Issue: `AGS_MCP_ENABLED` not persisting

**Solution:**
```bash
# Add to shell config
echo 'export AGS_MCP_ENABLED=true' >> ~/.zshrc  # or ~/.bashrc
source ~/.zshrc

# Verify
echo $AGS_MCP_ENABLED
```

---

## 🎓 Next Steps

### Learn More
- Read [STEP_2_MCP_SIMULATION_COMPLETE.md](./STEP_2_MCP_SIMULATION_COMPLETE.md) for full details
- Explore [packages/core/src/core/adapters/](./packages/core/src/core/adapters/) for adapter code
- Check [packages/cli/src/ags/app.py](./packages/cli/src/ags/app.py) for CLI implementation

### Integrate with CI
```bash
# Add to your GitHub Actions workflow
- name: MCP Dry Run
  run: |
    export AGS_MCP_ENABLED=true
    ags mcp-check
    ags agent run all --trace
```

### Extend with New Agent
1. Create package: `packages/agent-<name>/`
2. Implement `AgentProtocol`
3. Add MCP stub: `adapters/mcp_stub.py`
4. Update CLI agent list
5. Run `ags mcp-check` to validate

---

## 📚 Resources

- **Main README:** [README.md](./README.md)
- **Completion Report:** [STEP_2_MCP_SIMULATION_COMPLETE.md](./STEP_2_MCP_SIMULATION_COMPLETE.md)
- **Core Contracts:** [packages/core/src/core/models/contracts.py](./packages/core/src/core/models/contracts.py)
- **MCP Base Adapter:** [packages/core/src/core/adapters/mcp_base.py](./packages/core/src/core/adapters/mcp_base.py)

---

## ✅ Validation Checklist

Run through this checklist to confirm everything is working:

- [ ] `ags --version` shows version number
- [ ] `ags mcp-check` shows all ✅ green checkmarks
- [ ] `ags agent run all --trace` completes without errors
- [ ] Logs contain `request_id`, `latency_ms`, `status` fields
- [ ] `ags health-check` passes
- [ ] Tests pass: `ags test` or `make test`

---

## 🆘 Support

If you encounter issues:

1. Check [Troubleshooting](#-troubleshooting) section above
2. Review [STEP_2_MCP_SIMULATION_COMPLETE.md](./STEP_2_MCP_SIMULATION_COMPLETE.md)
3. Run `ags info` to get system information
4. Check GitHub Issues or create a new one

---

**🎉 Congratulations!** You've successfully set up and validated the MCP simulation framework. Your agents are now MCP-ready and you can proceed to Step 3: Internal Package Publishing.

---

**Last Updated:** October 5, 2025  
**Version:** 1.0.0

