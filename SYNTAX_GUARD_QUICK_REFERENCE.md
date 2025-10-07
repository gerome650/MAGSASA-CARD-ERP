# 🛡️ Syntax Guard Quick Reference

## 🚀 Quick Commands

### Run Syntax Guard Locally
```bash
# Direct execution (shows detailed output)
python3 tests/regression/test_syntax_regressions.py

# Via pytest (cleaner output)
pytest tests/regression/test_syntax_regressions.py -m regression -v

# Fast fail (stop on first error)
pytest tests/regression/test_syntax_regressions.py -m regression -x

# Quiet mode (minimal output)
pytest tests/regression/test_syntax_regressions.py -m regression -q
```

### Generate Badge Manually
```bash
# Generate from pytest JSON
python scripts/generate_syntax_badge.py \
  --pytest-json pytest-report.json \
  --out ci-dashboard

# Run tests and generate badge
python scripts/generate_syntax_badge.py \
  --out ci-dashboard \
  --extended

# View badge JSON
cat ci-dashboard/syntax-guard.json
```

### View Dashboard Locally
```bash
# Generate full dashboard
python scripts/generate_dashboard.py \
  --pytest-json pytest-report.json \
  --coverage-xml coverage.xml \
  --ruff-json lint-report.json \
  --syntax-guard-json ci-dashboard/syntax-guard.json \
  --prev-site "_site/ci-dashboard" \
  --out "ci-dashboard" \
  --repo "your-org/your-repo" \
  --run-url "https://github.com/your-org/your-repo/actions/runs/123" \
  --commit "abc123" \
  --branch "main" \
  --actor "username" \
  --duration-seconds "120" \
  --duration-pretty "2m 0s"

# Open dashboard in browser
open ci-dashboard/index.html
```

---

## 📊 Monitored Files

The syntax guard watches these 6 files:
1. `implement_farmer_role.py`
2. `observability/alerts/webhook_server.py`
3. `observability/alerts/notifier.py`
4. `observability/alerts/anomaly_strategies.py`
5. `test_data_integrity.py`
6. `test_business_logic.py`

---

## 🔍 What Gets Checked

For each file, 5 checks are performed:

| Check | Tool | What It Catches |
|-------|------|----------------|
| **1. Syntax Compilation** | `py_compile` | Basic Python syntax errors |
| **2. AST Parse** | `ast.parse` | Invalid syntax tree structure |
| **3. Ruff Lint** | `ruff` | Undefined names (F821), syntax errors (E999), multiple statements (E701) |
| **4. Black Format** | `black` | Code formatting issues |
| **5. Dynamic Import** | `importlib` | Import-time errors, undefined variables |

---

## 🎯 Common Issues & Fixes

### IndentationError
```python
# ❌ Bad
def foo():
bar()  # Wrong indentation

# ✅ Good
def foo():
    bar()  # Correct indentation
```

### SyntaxError: non-default argument follows default argument
```python
# ❌ Bad
def foo(a=1, b):
    pass

# ✅ Good
def foo(b, a=1):
    pass
```

### SyntaxError: invalid syntax (double if)
```python
# ❌ Bad
if x and if y:
    pass

# ✅ Good
if x and y:
    pass
```

### Undefined name (F821)
```python
# ❌ Bad
result = undefined_variable

# ✅ Good
result = defined_variable
```

---

## 📈 CI Workflow Integration

The syntax guard runs in CI automatically:

```
Checkout Code
     ↓
Setup Python
     ↓
Install Dependencies
     ↓
Ruff Lint
     ↓
🛡️ SYNTAX GUARD ← Runs here (before tests!)
     ↓
Run Tests + Coverage
     ↓
Generate Syntax Badge
     ↓
Generate Dashboard
     ↓
Publish to GitHub Pages
     ↓
Slack Notification
```

---

## 🔗 Badge URLs

### Live Badge
```
https://gerome650.github.io/MAGSASA-CARD-ERP/ci-dashboard/syntax-guard.json
```

### Shields.io Badge
```markdown
![Syntax Guard](https://img.shields.io/endpoint?url=https://gerome650.github.io/MAGSASA-CARD-ERP/ci-dashboard/syntax-guard.json)
```

### Dashboard URL
```
https://gerome650.github.io/MAGSASA-CARD-ERP/ci-dashboard/
```

---

## 🛠️ Adding New Files to Monitor

Edit `tests/regression/test_syntax_regressions.py`:

```python
WATCHED_FILES = [
    "implement_farmer_role.py",
    "observability/alerts/webhook_server.py",
    "observability/alerts/notifier.py",
    "observability/alerts/anomaly_strategies.py",
    "test_data_integrity.py",
    "test_business_logic.py",
    "your/new/file.py",  # ← Add here
]
```

Then commit and push - CI will automatically start monitoring the new file.

---

## 🐛 Troubleshooting

### "File not found" error
**Cause:** File in `WATCHED_FILES` doesn't exist  
**Fix:** Update `WATCHED_FILES` to remove or correct the path

### "Ruff not found" warning
**Cause:** Ruff not installed  
**Fix:** `pip install ruff`

### "Black not found" warning
**Cause:** Black not installed  
**Fix:** `pip install black`

### Test passes locally but fails in CI
**Cause:** Different Python version or dependencies  
**Fix:** Match CI Python version (3.11) and run `pip install -r requirements.txt`

---

## 📊 Understanding Badge Colors

| Color | Status | Meaning |
|-------|--------|---------|
| 🟢 Bright Green | PASS ✅ | All files passed all checks |
| 🔴 Red | FAIL ❌ | One or more files have syntax errors |
| ⚪ Light Grey | N/A | No tests run or badge not generated |

---

## 💡 Pro Tips

### Fast Feedback Loop
```bash
# Watch mode - re-run on file change (requires pytest-watch)
ptw tests/regression/test_syntax_regressions.py -m regression
```

### Check Specific File
```bash
# Edit test file to focus on one file
pytest tests/regression/test_syntax_regressions.py::test_syntax_regression_guard[implement_farmer_role.py] -v
```

### Debug Mode
```bash
# Show full traceback
python3 tests/regression/test_syntax_regressions.py --tb=long
```

### Pre-commit Hook
Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
python3 tests/regression/test_syntax_regressions.py
if [ $? -ne 0 ]; then
    echo "❌ Syntax regression detected! Fix errors before committing."
    exit 1
fi
```

---

## 📞 Support

**Documentation:** See `SYNTAX_GUARD_IMPLEMENTATION_COMPLETE.md`  
**Test Suite:** `tests/regression/test_syntax_regressions.py`  
**Badge Generator:** `scripts/generate_syntax_badge.py`  
**Dashboard Generator:** `scripts/generate_dashboard.py`  
**CI Workflow:** `.github/workflows/ci-pro-dashboard.yml`

---

## ✅ Checklist: Is Syntax Guard Working?

- [ ] Tests run without errors: `python3 tests/regression/test_syntax_regressions.py`
- [ ] Badge generates: `python scripts/generate_syntax_badge.py --out ci-dashboard`
- [ ] Badge JSON exists: `cat ci-dashboard/syntax-guard.json`
- [ ] Dashboard shows syntax guard KPI
- [ ] CI workflow includes syntax guard step
- [ ] GitHub Pages displays syntax guard status
- [ ] Badge URL is accessible

---

**Last Updated:** 2025-10-05  
**Version:** 1.0.0  
**Status:** ✅ Production Ready

