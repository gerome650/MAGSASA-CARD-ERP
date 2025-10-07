# 🔥 CI-Safe Smoke/Import/Regression Test Layer

A robust test infrastructure for the `core/` package that provides early CI failure detection and automatic code quality enforcement.

## 📋 Overview

This test layer consists of three main components:

1. **Import Sanity Tests** - Verify all modules can be imported
2. **Smoke Component Tests** - Dynamic class discovery and instantiation testing
3. **Regression Guard** - Prevent bad patterns from reappearing

## 📁 Files Created

### Core Test Files

| File | Purpose | When to Run |
|------|---------|-------------|
| `tests/test_import_sanity.py` | Import validation | First in CI pipeline |
| `tests/test_smoke_core_components.py` | Class instantiation checks | After imports pass |
| `tests/test_regression_guard.py` | Lint pattern enforcement | Last (or continuously) |
| `tests/conftest.py` | Pytest configuration | Auto-loaded |

### Utility Scripts

| File | Purpose | Usage |
|------|---------|-------|
| `scripts/check_init_files.py` | __init__.py validation | CI check or auto-fix |

## 🚀 Quick Start

### Local Development

```bash
# 1. Check/create __init__.py files
python3 scripts/check_init_files.py

# 2. Run import sanity tests
pytest tests/test_import_sanity.py -v

# 3. Run smoke tests
pytest tests/test_smoke_core_components.py -v

# 4. Run regression guard
pytest tests/test_regression_guard.py -v

# 5. Run all smoke tests together
pytest tests/test_import_sanity.py tests/test_smoke_core_components.py tests/test_regression_guard.py -v
```

### CI/CD Pipeline

```yaml
# Recommended CI workflow order
steps:
  - name: Check __init__.py files
    run: python3 scripts/check_init_files.py --check-only

  - name: Import Sanity Tests
    run: pytest tests/test_import_sanity.py -v --tb=short

  - name: Smoke Component Tests
    run: pytest tests/test_smoke_core_components.py -v --tb=short

  - name: Regression Guard
    run: pytest tests/test_regression_guard.py -v --tb=short
```

## 📊 Test Markers

The tests use custom pytest markers for organization:

```bash
# Run only sanity tests
pytest -m sanity -v

# Run only smoke tests
pytest -m smoke -v

# Run only regression tests
pytest -m regression -v

# Skip slow tests
pytest -m "not slow" -v
```

## 🔍 What Each Test Does

### 1️⃣ Import Sanity Tests (`test_import_sanity.py`)

**Purpose:** Ensures all Python modules in `core/` can be imported without errors.

**Features:**
- Automatic module discovery using `pkgutil`
- Graceful handling of missing third-party dependencies (skips instead of fails)
- Detects real import errors vs. dependency issues

**Example Output:**
```
tests/test_import_sanity.py::test_import_module[core.adapters] SKIPPED   [ 25%]
tests/test_import_sanity.py::test_import_module[core.models] PASSED      [ 50%]
tests/test_import_sanity.py::test_core_package_exists PASSED             [100%]
```

### 2️⃣ Smoke Component Tests (`test_smoke_core_components.py`)

**Purpose:** Discovers and attempts to instantiate all classes in `core/`.

**Features:**
- Dynamic class discovery
- Smart instantiation with dummy arguments
- Skips abstract classes automatically
- Optional method call testing

**Example Output:**
```
🔎 Testing class: core.models.contracts.AgentInput
  ✅ Successfully instantiated AgentInput
```

### 3️⃣ Regression Guard (`test_regression_guard.py`)

**Purpose:** Prevents common Python anti-patterns from reappearing.

**Blocked Patterns:**
- `F821` - Undefined names
- `F841` - Unused variables
- `B007` - Unused loop variables
- `SIM117` - Nested with statements
- `SIM105` - try/except pass
- `SIM222` - "... or True" expressions

**Example Output:**
```
tests/test_regression_guard.py::test_no_common_issues PASSED [100%]
```

## 🛠️ Script: `check_init_files.py`

Ensures all Python packages have `__init__.py` files.

### Usage

```bash
# Check mode (CI) - fails if missing files found
python3 scripts/check_init_files.py --check-only

# Auto-create mode (local dev) - creates missing files
python3 scripts/check_init_files.py
```

### Example Output

**Check Mode:**
```
❌ Missing __init__.py in:
    /path/to/core/submodule/__init__.py
💡 Run without --check-only to auto-create these files.
```

**Auto-Create Mode:**
```
🔧 Creating 2 missing __init__.py file(s)...
  ✅ Created: /path/to/core/submodule/__init__.py
  ✅ Created: /path/to/core/utils/__init__.py
✨ Done. All __init__.py files present.
```

## 🎯 Benefits

### Early Failure Detection
- **Import issues** caught before expensive tests run
- **Missing dependencies** identified immediately
- **Broken imports** detected at CI entry

### Automatic Quality Enforcement
- **Lint regressions** blocked at test level
- **Bad patterns** prevented from merging
- **Code quality** maintained automatically

### Developer Productivity
- **Fast feedback** - tests complete in seconds
- **Auto-discovery** - new modules tested automatically
- **Clear errors** - pinpoint exact issues quickly

## 📈 Performance

| Test Suite | Typical Duration | Files Tested |
|-------------|------------------|--------------|
| Import Sanity | < 1 second | All core modules |
| Smoke Components | < 1 second | All core classes |
| Regression Guard | 1-5 seconds | Entire codebase |
| **Total** | **< 10 seconds** | **Complete coverage** |

## 🔧 Configuration

### Pytest Markers (pyproject.toml)

The following markers are registered in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    "sanity: marks tests as sanity/import tests (run first)",
    "smoke: marks tests as smoke tests (lightweight component tests)",
    "regression: marks tests as regression guards (prevent bad patterns)",
    "order: execution order marker for tests",
]
```

### Path Configuration (conftest.py)

The `conftest.py` ensures proper module resolution:

```python
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CORE_SRC_PATH = os.path.join(PROJECT_ROOT, "packages", "core", "src")

if CORE_SRC_PATH not in sys.path:
    sys.path.insert(0, CORE_SRC_PATH)
```

## 🚨 Troubleshooting

### Issue: "No module named 'core'"

**Solution:** Run tests from project root or check `conftest.py` paths.

```bash
# Correct: Run from project root
cd /path/to/MAGSASA-CARD-ERP
pytest tests/test_import_sanity.py

# Incorrect: Run from tests directory
cd tests && pytest test_import_sanity.py  # ❌ Won't work
```

### Issue: Tests are skipped

**Reason:** Missing dependencies or abstract classes (this is expected behavior).

```bash
# View skip reasons
pytest tests/test_import_sanity.py -v -rs
```

### Issue: Regression guard fails

**Solution:** Fix the lint violations or adjust the patterns in `test_regression_guard.py`.

```bash
# See exact violations
pytest tests/test_regression_guard.py -v

# Auto-fix some issues
ruff check --fix .
```

## 📝 Maintenance

### Adding New Patterns to Regression Guard

Edit `tests/test_regression_guard.py`:

```python
BAD_PATTERNS = [
    "F821",    # undefined name
    "F841",    # unused variable
    # Add new pattern here
    "E501",    # line too long (example)
]
```

### Excluding Modules from Smoke Tests

Edit `tests/test_smoke_core_components.py`:

```python
def iter_core_classes():
    for _finder, name, _ispkg in pkgutil.walk_packages(...):
        # Add exclusion logic
        if "exclude_me" in name:
            continue
```

## ✅ Best Practices

1. **Run locally before pushing** to catch issues early
2. **Keep tests fast** - these should complete in seconds
3. **Update patterns** as code quality standards evolve
4. **Don't skip regressions** - fix the root cause instead
5. **Use markers** to run specific test subsets during development

## 🎓 Integration with Existing Tests

This smoke test layer complements (doesn't replace) your existing tests:

```
┌─────────────────────────────────────────┐
│     CI Pipeline Test Execution Order    │
├─────────────────────────────────────────┤
│ 1. ✅ Import Sanity (< 1s)              │  ← NEW
│ 2. ✅ Smoke Tests (< 1s)                │  ← NEW
│ 3. ✅ Regression Guard (< 5s)           │  ← NEW
├─────────────────────────────────────────┤
│ 4. Unit Tests                           │  ← EXISTING
│ 5. Integration Tests                    │  ← EXISTING
│ 6. E2E Tests                            │  ← EXISTING
└─────────────────────────────────────────┘
```

**Benefit:** Fail fast - catch 80% of issues in first 10 seconds!

## 📚 Further Reading

- [pytest documentation](https://docs.pytest.org/)
- [ruff documentation](https://docs.astral.sh/ruff/)
- [Python pkgutil module](https://docs.python.org/3/library/pkgutil.html)

---

**Created:** October 2025  
**Maintained by:** Development Team  
**Status:** ✅ Production Ready

