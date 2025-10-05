# AgSense Stage 7 - Intelligent Agent Orchestration Platform

🧠 **AgSense Stage 7** is a Python 3.12+ monorepo built with `uv` workspaces for intelligent agent orchestration. This scaffold provides a complete development environment with CI/CD, testing, and deployment workflows.

## 🚀 Quick Start

### Prerequisites

- Python 3.10+ (recommended: 3.12)
- [uv](https://github.com/astral-sh/uv) package manager
- Git

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd agsense

# Install dependencies and set up development environment
make setup

# Verify installation
ags test
ags mcp-check
```

### First Run

```bash
# Enable MCP mode
export AGS_MCP_ENABLED=true

# Check MCP readiness
ags mcp-check

# Run agent simulation with trace
ags agent run all --trace

# Or start individual agents
make run-orchestrator
make run-ingest
make run-retrieval
```

## 📁 Project Structure

```
agsense/
├── pyproject.toml              # Root workspace configuration
├── Makefile                    # Development commands
├── .pre-commit-config.yaml     # Pre-commit hooks
├── .github/workflows/          # CI/CD pipelines
├── packages/                   # Workspace packages
│   ├── core/                   # Shared contracts and models
│   ├── cli/                    # Command-line interface
│   ├── agent-orchestrator/     # Central coordination
│   ├── agent-ingest/           # Data ingestion
│   ├── agent-retrieval/        # Data retrieval
│   ├── agent-scoring/          # Data scoring
│   ├── agent-notify/           # Notifications
│   └── agent-billing/          # Billing & payments
└── tests/                      # Test suite
    ├── unit/                   # Unit tests
    └── integration/            # Integration tests
```

## 🛠️ Development Commands

### Setup & Installation

```bash
make setup          # Complete development setup
make install        # Install production dependencies
make dev-install    # Install development dependencies
```

### Code Quality

```bash
make lint           # Run all linting (ruff, black, mypy)
make format         # Format code automatically
make test           # Run tests with coverage
make quick-test     # Quick test run (no coverage)
```

### Agent Management

```bash
make run            # Start all agents
make run-orchestrator    # Start orchestrator only
make run-ingest     # Start ingest agent only
# ... etc for other agents
```

### CLI Commands

```bash
ags dev-setup            # Set up development environment
ags test                 # Run tests via CLI
ags mcp-check            # Check MCP readiness (validates all agents)
ags agent run all        # Run all agents through orchestrator
ags agent run all --trace # Run with request flow visualization
ags health-check         # System health check
ags info                 # Show system information
```

### Build & Release

```bash
make build          # Build all packages
make publish        # Publish to registry
make clean          # Clean build artifacts
```

## 🧪 Testing

### Unit Tests

```bash
make test-unit      # Run unit tests only
pytest tests/unit/  # Direct pytest command
```

### Integration Tests

```bash
make test-integration  # Run integration tests only
pytest tests/integration/  # Direct pytest command
```

### Coverage

```bash
make test           # Includes coverage report
# Coverage reports generated in htmlcov/
```

## 🤖 Agent Architecture

### Core Contracts

All agents implement the `AgentProtocol` interface:

```python
from agsense_core.models.contracts import AgentProtocol, AgentInput, AgentOutput

class MyAgent(AgentProtocol):
    async def run(self, data: AgentInput) -> AgentOutput:
        # Agent logic here
        pass
    
    async def health_check(self) -> bool:
        # Health check logic
        pass
    
    async def validate_input(self, data: AgentInput) -> bool:
        # Input validation
        pass
```

### Orchestrator

The `AgentOrchestrator` manages all agents and routes requests:

```python
from agent_orchestrator.orchestrator import AgentOrchestrator

orchestrator = AgentOrchestrator()
await orchestrator.start()

# Route a request
response = await orchestrator.route_request(agent_input)
```

## 🔧 Configuration

### Environment Variables

```bash
# MCP Mode (required for dry run simulation)
export AGS_MCP_ENABLED=true

# Optional: Set custom Python version
export UV_PYTHON=3.12

# Optional: Enable verbose logging
export RUST_LOG=debug

# Optional: OpenTelemetry configuration
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_SERVICE_NAME=agsense
```

### Workspace Configuration

The project uses `uv` workspaces defined in `pyproject.toml`:

```toml
[tool.uv.workspace]
members = [
    "packages/core",
    "packages/cli",
    "packages/agent-orchestrator",
    # ... other packages
]
```

## 🚀 CI/CD Pipeline

### GitHub Actions

- **CI Pipeline** (`.github/workflows/ci.yml`):
  - Lint and type checking
  - Multi-version Python testing (3.10, 3.11, 3.12)
  - Security scanning
  - Build verification

- **Release Pipeline** (`.github/workflows/release.yml`):
  - Automatic releases on version tags
  - Package building and publishing
  - Changelog generation

### Pre-commit Hooks

Automatically installed with `make setup`:

- **Code formatting**: `black`, `ruff`
- **Linting**: `ruff`, `mypy`
- **Security**: `bandit`
- **Documentation**: `pydocstyle`

## 📦 Package Management

### Adding Dependencies

```bash
# Add to root workspace
uv add package-name

# Add to specific package
uv add package-name --package packages/core

# Add dev dependency
uv add --dev package-name
```

### Building Packages

```bash
make build          # Build all packages
uv build            # Build current package
```

## 🧪 Smoke Testing

Run the orchestrator smoke test:

```bash
# Via Python
python packages/agent-orchestrator/example_smoke_test.py

# Via Make
make smoke-test     # (if added to Makefile)
```

## 🔍 Troubleshooting

### Common Issues

1. **uv not found**:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Python version issues**:
   ```bash
   uv python install 3.12
   uv sync
   ```

3. **Import errors**:
   ```bash
   # Ensure you're in the project root
   cd agsense
   uv sync
   ```

4. **Test failures**:
   ```bash
   # Check Python path
   uv run python -c "import sys; print(sys.path)"
   
   # Run with verbose output
   uv run pytest tests/ -v -s
   ```

### Debug Mode

```bash
# Enable verbose logging
ags --verbose dev-setup

# Run with debug output
RUST_LOG=debug uv run ags test
```

## 📚 Documentation

### Core Documentation
- [Core Contracts](packages/core/src/core/models/contracts.py)
- [MCP Base Adapter](packages/core/src/core/adapters/mcp_base.py)
- [CLI Documentation](packages/cli/src/ags/app.py)
- [Orchestrator API](packages/agent-orchestrator/src/agent_orchestrator/orchestrator.py)

### Guides & Tutorials
- [MCP Quick Start Guide](MCP_QUICK_START.md) - Get started in 5 minutes
- [Step 2 Completion Report](STEP_2_MCP_SIMULATION_COMPLETE.md) - Full implementation details
- [Agent Development Guide](docs/agent-development.md) - How to create new agents

## 🤝 Contributing

1. **Setup development environment**:
   ```bash
   make setup
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature
   ```

3. **Make changes and test**:
   ```bash
   make lint test
   ```

4. **Commit with conventional commits**:
   ```bash
   git commit -m "feat: add new feature"
   ```

5. **Push and create PR**

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/agsense/agsense/issues)
- **Documentation**: [Project Wiki](https://github.com/agsense/agsense/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/agsense/agsense/discussions)

## 🧠 MCP Simulation (Step 2)

AgSense includes a complete **Model Context Protocol (MCP)** simulation framework for dry-run validation of agent readiness.

### Quick Start

```bash
# 1. Enable MCP mode
export AGS_MCP_ENABLED=true

# 2. Validate all agents are MCP-ready
ags mcp-check

# 3. Run end-to-end orchestrator simulation
ags agent run all --trace
```

### What Gets Validated

✅ **MCP Stub Adapters** - All agents have working MCP adapters  
✅ **Protocol Compliance** - Agents implement required methods  
✅ **Schema Validation** - Input/output contracts are enforced  
✅ **Request Routing** - Orchestrator correctly routes to agents  
✅ **Structured Logging** - All required fields present in logs  
✅ **CI Integration** - Automated validation on every PR

### Example Output

```
🔄 Request Flow Trace
├── agent-ingest (215ms)
├── agent-retrieval (163ms)
├── agent-scoring (269ms)
├── agent-notify (113ms)
└── agent-billing (321ms)

✅ All 5 agents executed successfully!
Average latency: 216ms
```

See [MCP_QUICK_START.md](MCP_QUICK_START.md) for detailed guide.

---

**🎉 Ready to build intelligent agents? Start with `make setup` and `ags dev-setup`!**