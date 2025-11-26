# Testing CI/CD Pipeline

## What Was Fixed

The CI was failing due to two issues in `pyproject.toml`:

### 1. ❌ License Format Deprecation
```toml
# OLD (deprecated)
license = {text = "MIT"}

# NEW (fixed)
license = "MIT"
```

### 2. ❌ Multiple Packages Error
```
error: Multiple top-level packages discovered in a flat-layout:
['molvis_core', 'molvis_tkinter', 'molvis_plotting', 'molvis_streamlit'].
```

**Fix:** Added explicit package configuration:
```toml
[tool.setuptools]
packages = ["molvis_core", "molvis_plotting", "molvis_streamlit", "molvis_tkinter"]
```

---

## ✅ How to Test CI/CD Changes

### Method 1: Automated Local Testing (Recommended)

Run the CI simulation script:

```bash
# Make it executable
chmod +x test_ci_locally.py

# Run all CI checks
python test_ci_locally.py
```

**This script runs:**
- ✅ Package installation (`pip install -e .`)
- ✅ Full test suite (134 tests)
- ✅ Code coverage report
- ✅ Black formatting check
- ✅ isort import sorting
- ✅ Ruff linting
- ✅ mypy type checking
- ✅ Bandit security scan

**Output:**
```
Results: 8/8 checks passed
🎉 All checks passed! Ready to push.
```

---

### Method 2: Manual Step-by-Step Testing

#### 1. Test Package Installation
```bash
# Clean install
pip install -e .

# Should see:
# Successfully installed molman-0.3.0
```

#### 2. Run Tests
```bash
# Quick test
pytest -v

# With coverage
pytest --cov=molvis_core --cov-report=term-missing
```

**Expected output:**
```
============================== 134 passed in X.XXs ==============================
```

#### 3. Code Quality Checks

```bash
# Format check (doesn't modify files)
black --check molvis_core tests

# Auto-fix formatting
black molvis_core tests

# Check imports
isort --check-only molvis_core tests

# Fix imports
isort molvis_core tests

# Lint with Ruff
ruff check molvis_core tests

# Auto-fix linting issues
ruff check --fix molvis_core tests

# Type check
mypy molvis_core --ignore-missing-imports

# Security scan
bandit -r molvis_core
```

#### 4. Pre-commit Hooks (Best Practice)

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run all hooks manually
pre-commit run --all-files
```

This runs all quality checks automatically before each commit!

---

### Method 3: Check GitHub Actions (After Push)

1. **Push your changes:**
   ```bash
   git push origin your-branch
   ```

2. **View CI Results:**
   - Go to: https://github.com/Ajaykhanna/MolMan/actions
   - Click on your latest commit
   - Watch the workflows run in real-time

3. **Check Each Workflow:**

   **CI - Tests and Coverage** (Most Important)
   - ✅ Must pass before merging
   - Tests on Python 3.9, 3.10, 3.11, 3.12
   - Uploads coverage report

   **Code Quality**
   - Linting and formatting checks
   - Type checking
   - Complexity analysis
   - Uses `continue-on-error`, so won't block

   **Security Scanning**
   - Bandit, Safety, CodeQL
   - Dependency review (on PRs)
   - Reports issues but doesn't block

   **Performance Testing**
   - Benchmarks (if marked with `@pytest.mark.performance`)
   - Memory profiling

---

## 🐛 Troubleshooting

### Issue: "pip install -e ." fails locally

**Symptom:**
```
ERROR: Failed to build 'file:///...' when getting requirements
```

**Fix:**
```bash
# Update pip and setuptools
pip install --upgrade pip setuptools wheel

# Try again
pip install -e .
```

---

### Issue: Tests pass locally but fail in CI

**Common causes:**

1. **Python version differences**
   ```bash
   # CI tests on 3.9, 3.10, 3.11, 3.12
   # Check your version
   python --version

   # Test with specific version (if you have pyenv)
   pyenv local 3.9.18
   pytest -v
   ```

2. **Missing dependencies**
   ```bash
   # CI does fresh install
   # Simulate by creating new venv
   python -m venv test_env
   source test_env/bin/activate
   pip install -e .
   pip install pytest pytest-cov pytest-mock
   pytest -v
   ```

3. **File path issues**
   - CI uses Linux (forward slashes)
   - Make sure paths use `Path()` from pathlib

---

### Issue: Code quality checks fail

**Black formatting:**
```bash
# See what needs fixing
black --check --diff molvis_core tests

# Auto-fix
black molvis_core tests
```

**Import sorting:**
```bash
# See what needs fixing
isort --check-only --diff molvis_core tests

# Auto-fix
isort molvis_core tests
```

**Ruff linting:**
```bash
# See issues
ruff check molvis_core tests

# Auto-fix what's possible
ruff check --fix molvis_core tests
```

---

### Issue: Security scan warnings

**Bandit warnings:**
```bash
# Run locally to see details
bandit -r molvis_core -f screen

# If false positive, add to pyproject.toml:
[tool.bandit]
skips = ["B101"]  # Skip specific check
```

**Safety warnings (vulnerable dependencies):**
```bash
# Check dependencies
pip freeze > requirements-check.txt
safety check --file requirements-check.txt

# Update vulnerable package
pip install --upgrade package-name
```

---

## 📊 Monitoring CI/CD Health

### GitHub Actions Dashboard

**View all workflows:**
```
https://github.com/Ajaykhanna/MolMan/actions
```

**Filter by workflow:**
- Click "CI - Tests and Coverage"
- See success rate over time
- Download artifacts (coverage reports, benchmark results)

### Coverage Reports

**After CI runs:**
1. Go to Actions → Latest run
2. Scroll to "Artifacts"
3. Download "coverage-report"
4. Open `htmlcov/index.html` in browser

**Current coverage:** ~81% (134 tests)

---

## 🚀 Best Practices

### Before Pushing

1. **Run local tests:**
   ```bash
   python test_ci_locally.py
   ```

2. **Or at minimum:**
   ```bash
   pytest -v
   black molvis_core tests
   isort molvis_core tests
   ```

3. **Use pre-commit hooks:**
   ```bash
   pre-commit run --all-files
   ```

### When Creating PR

1. **Check that CI passes** on your branch first
2. **Review the "Files changed" tab** for accidental commits
3. **Wait for all checks** before requesting review
4. **Address any security warnings** from CodeQL/Bandit

### Regular Maintenance

1. **Weekly:** Check security scan results
2. **Monthly:** Update pre-commit hooks (`pre-commit autoupdate`)
3. **Monitor coverage:** Should stay above 80%

---

## 📁 Where to Find CI Outputs

### Locally

```bash
# Coverage HTML report
open htmlcov/index.html

# Test output
pytest -v --tb=short > test_results.txt

# Bandit report
bandit -r molvis_core -f json -o bandit-report.json
```

### GitHub Actions

**Artifacts** (30-day retention):
- Coverage HTML report
- Bandit security report (JSON)
- Benchmark results (JSON)

**Logs:**
- Click on any workflow run
- Click on failed step to see logs
- Use search to find specific errors

**Security Tab:**
- CodeQL findings appear here
- Dependency vulnerabilities
- Security advisories

---

## 🎯 Success Criteria

### CI Must Pass ✅

- All 134 tests passing
- No build/installation errors
- Coverage report generated

### Code Quality (Recommended) ⚠️

- Black formatting consistent
- Imports sorted with isort
- No critical Ruff violations
- Type hints validated by mypy

### Security (Monitored) 🔒

- No high-severity Bandit issues
- No vulnerable dependencies
- CodeQL clean or issues addressed

---

## 🔧 Quick Fixes Reference

```bash
# Fix everything automatically
black molvis_core tests
isort molvis_core tests
ruff check --fix molvis_core tests

# Run tests
pytest -v

# Check coverage
pytest --cov=molvis_core

# Run security scan
bandit -r molvis_core

# Simulate full CI locally
python test_ci_locally.py

# Or use pre-commit
pre-commit run --all-files
```

---

## 📞 Getting Help

### CI Failing?

1. **Check the logs:** Actions → Click on failed workflow → Click on failed step
2. **Run locally:** `python test_ci_locally.py`
3. **Compare environments:** Check Python version, dependencies

### Still Stuck?

1. Check `CI_CD_GUIDE.md` for detailed documentation
2. Review workflow files in `.github/workflows/`
3. Look for similar issues in Actions history

---

**Last Updated:** Phase 10 CI/CD Implementation (2025-11-26)
