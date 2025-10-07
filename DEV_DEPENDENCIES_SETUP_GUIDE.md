# 📦 Development Dependencies Setup Guide

## 🎯 Quick Start

### Option 1: One Command Setup (Recommended)

```bash
# Activate virtual environment
source .venv/bin/activate

# Install all dev dependencies
make install-dev

# Verify installation
make check-deps
```

### Option 2: Manual Installation

```bash
# Activate virtual environment
source .venv/bin/activate

# Install from requirements file
pip install -r requirements-dev.txt

# OR use uv (faster)
uv sync
```

---

## 🚨 Problem Solved

### Before (ModuleNotFoundError)
```
❌ ModuleNotFoundError: No module named 'aiohttp'
❌ Tests failing due to missing dependencies
❌ Manual dependency hunting
```

### After (Standardized Setup)
```
✅ All dependencies listed in requirements-dev.txt
✅ One command to install everything: make install-dev
✅ Automatic dependency verification
✅ Clear setup instructions
```

---

## 📋 What Gets Installed

### Core Testing
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `pytest-xdist` - Parallel test execution
- `pytest-timeout` - Test timeouts

### Linting & Formatting
- `ruff` - Fast Python linter
- `black` - Code formatter
- `mypy` - Type checker

### Async & HTTP (Critical!)
- `aiohttp` - Async HTTP client/server ⭐
- `anyio` - Async compatibility layer
- `httpx` - Modern async HTTP client

### Configuration & Data
- `pyyaml` - YAML parsing
- `python-dotenv` - Environment variables
- `toml` - TOML parsing

### Monitoring
- `psutil` - Process monitoring

### Utilities
- `requests` - HTTP library
- `click` - CLI framework
- `rich` - Terminal formatting

---

## 🔍 Virtual Environment Management

### Check if venv is active:
```bash
# Should show your venv path
echo $VIRTUAL_ENV

# Should point to venv's python
which python3
```

### Create venv (if needed):
```bash
python3 -m venv .venv
```

### Activate venv:
```bash
# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### Deactivate venv:
```bash
deactivate
```

---

## 🛠️ Available Make Commands

### Installation
```bash
make install-dev      # Install ALL dev dependencies
make check-deps       # Verify dependencies are installed
```

### Development
```bash
make lint             # Run linting
make format           # Format code
make fix-lint         # Auto-fix lint issues
make test             # Run tests with coverage
make verify-all       # Run complete pipeline (includes dep check)
```

---

## 🧪 Verification Steps

### 1. Check Virtual Environment
```bash
python3 scripts/setup/install_dev_dependencies.py --check-only
```

Expected output:
```
📋 Environment Check:
   Python: 3.11.x
   Location: /path/to/.venv/bin/python3
   Virtual Env: ✅ Active
```

### 2. Verify Critical Dependencies
```bash
make check-deps
```

Expected output:
```
🔍 Checking dependencies...
✅ All dependencies OK
```

### 3. Test Import
```python
# Should all work without errors
import aiohttp
import pytest
import ruff
import black
import yaml
```

---

## 📦 File Structure

```
MAGSASA-CARD-ERP/
├── requirements-dev.txt              # Development dependencies
├── pyproject.toml                    # Project config (includes dev deps)
├── scripts/
│   └── setup/
│       └── install_dev_dependencies.py  # Installation script
├── .venv/                            # Virtual environment (create this)
└── Makefile                          # Convenient shortcuts
```

---

## 🔧 pyproject.toml Integration

Dependencies are also defined in `pyproject.toml` under `[tool.uv]`:

```toml
[tool.uv]
dev-dependencies = [
    "aiohttp>=3.9.0",
    "pytest>=7.4.3",
    "ruff==0.5.0",
    "black==24.4.2",
    # ... and more
]
```

This allows using:
```bash
uv sync  # Installs all dependencies including dev
```

---

## 🚀 CI/CD Integration

### GitHub Actions Example
```yaml
- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    make install-dev

- name: Verify dependencies
  run: make check-deps

- name: Run tests
  run: make test
```

### Troubleshooting in CI
If `make verify-all` fails with `ModuleNotFoundError`:

1. **Check dependency installation step exists:**
   ```yaml
   - run: make install-dev
   ```

2. **Verify Python version matches:**
   ```yaml
   - uses: actions/setup-python@v4
     with:
       python-version: '3.11'
   ```

3. **Use caching for speed:**
   ```yaml
   - uses: actions/cache@v3
     with:
       path: ~/.cache/pip
       key: ${{ runner.os }}-pip-${{ hashFiles('requirements-dev.txt') }}
   ```

---

## ⚠️ Common Issues

### Issue: "ModuleNotFoundError: No module named 'aiohttp'"
**Solution:**
```bash
source .venv/bin/activate
make install-dev
```

### Issue: "WARNING: Not running in a virtual environment"
**Solution:**
```bash
# Create and activate venv first
python3 -m venv .venv
source .venv/bin/activate
make install-dev
```

### Issue: "pip: command not found"
**Solution:**
```bash
python3 -m ensurepip --upgrade
make install-dev
```

### Issue: Dependencies installed but imports fail
**Solution:**
```bash
# Make sure you're using the venv's python
which python3  # Should show .venv/bin/python3

# If not, deactivate and reactivate
deactivate
source .venv/bin/activate
```

---

## 📚 Additional Resources

- **pytest documentation**: https://docs.pytest.org/
- **ruff documentation**: https://docs.astral.sh/ruff/
- **aiohttp documentation**: https://docs.aiohttp.org/
- **uv documentation**: https://github.com/astral-sh/uv

---

## 🎉 Success Checklist

- [ ] Virtual environment created (`.venv/` exists)
- [ ] Virtual environment activated (`$VIRTUAL_ENV` is set)
- [ ] Dev dependencies installed (`make install-dev` completed)
- [ ] Dependencies verified (`make check-deps` passes)
- [ ] Can import aiohttp (`python -c "import aiohttp"` works)
- [ ] Tests run (`make test` works)
- [ ] Linting works (`make lint` works)

Once all checked, you're ready to develop! 🚀

---

## 🧪 Development Mode for Coverage (Optional)

During early development, you may want to work on features without being blocked by coverage requirements. The governance system supports a **development mode** that relaxes coverage enforcement locally while maintaining strict enforcement in CI/CD pipelines.

### How It Works

1. **Local Development**: Coverage below minimum will **warn** but **not fail**
2. **CI/CD Pipelines**: Coverage below minimum will **always fail** (strict enforcement)
3. **Explicit Opt-in**: You must use `--allow-dev` flag to enable relaxed mode

### Enable Development Mode

**Step 1: Update `merge_policy.yml`**

```yaml
coverage:
  enabled: true
  minimum: 85
  dev_mode: true  # 👈 Enable development mode
```

**Step 2: Run governance checks with dev mode**

```bash
# Run governance checks in development mode
make governance-dev

# Or use the script directly
python scripts/hooks/enforce_coverage.py --allow-dev
```

### Example Output

**In Development Mode (with --allow-dev):**
```
🔧 Enforcement Mode: DEVELOPMENT MODE (relaxed enforcement)

⚠️  DEV MODE: Coverage 75.0% is below minimum threshold 85% (would fail in CI/strict mode)
   Minimum: 85%, Target: 95%
   💡 Tip: Run with --strict to test CI enforcement locally
```

**In CI or Strict Mode:**
```
🔧 Enforcement Mode: CI MODE (strict enforcement)
🏗️  CI Environment Detected: Full enforcement active

❌ FAIL: Coverage 75.0% is below minimum threshold 85%
   Required: >=85%, Target: 95%
```

### Testing CI Enforcement Locally

You can test how your code will behave in CI by using the `--strict` flag:

```bash
# Test strict enforcement locally
python scripts/hooks/enforce_coverage.py --strict
```

### ⚠️ Important Warnings

- **Not a workaround**: Dev mode should be used during **active development**, not as a permanent solution for poor test coverage
- **CI always enforces**: Your code will still fail in CI/CD pipelines if coverage is below minimum
- **Explicit opt-in**: Dev mode requires both `dev_mode: true` in policy AND `--allow-dev` flag
- **Use responsibly**: Clean up and improve coverage before creating pull requests

### When to Use Dev Mode

✅ **Good use cases:**
- Prototyping new features
- Early development phases
- Exploratory coding
- Refactoring existing code incrementally

❌ **Bad use cases:**
- Avoiding writing tests permanently
- Merging untested code to main
- Bypassing quality standards
- Production-ready features

### Make Targets

```bash
# Standard governance (strict)
make governance-report

# Development mode governance (relaxed)
make governance-report-dev

# Run specific coverage check in dev mode
make governance-dev
```

---

## 💡 Pro Tips

1. **Use direnv** for automatic venv activation:
   ```bash
   # .envrc
   source .venv/bin/activate
   ```

2. **Alias for quick setup:**
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   alias venv='source .venv/bin/activate'
   ```

3. **Check before commit:**
   ```bash
   # Always run before pushing
   make verify-all
   ```

4. **Keep dependencies updated:**
   ```bash
   pip list --outdated
   pip install -U <package>
   ```

---

**Questions?** Check the main README or open an issue on GitHub.

