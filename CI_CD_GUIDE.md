# CI/CD Pipeline Guide

## Overview

MolMan uses a comprehensive CI/CD pipeline with GitHub Actions to ensure code quality, security, and reliability. This guide explains the automated workflows and how to work with them.

## 🔄 Automated Workflows

### 1. **CI - Tests and Coverage** (`.github/workflows/ci.yml`)

**Triggers:**
- Push to `main`, `master`, `develop`, or `claude/**` branches
- Pull requests to `main`, `master`, `develop`
- Manual workflow dispatch

**What it does:**
- ✅ Runs full test suite on Python 3.9, 3.10, 3.11, 3.12
- ✅ Generates code coverage reports (XML, HTML, terminal)
- ✅ Uploads coverage to Codecov (Python 3.11 only)
- ✅ Uploads HTML coverage report as artifact (30-day retention)
- ✅ Creates test summary in GitHub Actions

**Matrix testing:**
```yaml
python-version: ["3.9", "3.10", "3.11", "3.12"]
```

**Coverage goals:**
- Current: ~81% (134 tests passing)
- Target: >85% for production readiness

### 2. **Code Quality** (`.github/workflows/code-quality.yml`)

**Triggers:**
- Push to main branches
- Pull requests
- Manual dispatch

**Components:**

#### Lint and Format Check
- **Ruff**: Fast Python linter (replaces flake8, pylint)
- **Black**: Code formatter (line length: 100)
- **isort**: Import sorting

#### Type Checking
- **mypy**: Static type checking
- Runs on `molvis_core` with relaxed settings

#### Code Complexity
- **Radon**: Cyclomatic complexity analysis
- **Maintainability Index**: Code health metrics

**Note:** All quality checks use `continue-on-error: true` to avoid blocking PRs, but issues are reported in the summary.

### 3. **Security Scanning** (`.github/workflows/security.yml`)

**Triggers:**
- Push to main branches
- Pull requests
- Weekly schedule (Mondays at 00:00 UTC)
- Manual dispatch

**Security Tools:**

#### Bandit
- Scans for common security issues in Python code
- Generates JSON report (uploaded as artifact)
- Checks: SQL injection, hardcoded passwords, unsafe functions

#### Safety
- Checks dependencies for known vulnerabilities
- Scans against CVE database
- Reports vulnerable packages

#### Dependency Review
- PR-only check
- Reviews new dependencies for security issues
- Fails on moderate+ severity vulnerabilities

#### CodeQL
- GitHub's advanced security scanning
- Queries: `security-and-quality`
- Results appear in Security tab

### 4. **Performance Testing** (`.github/workflows/performance.yml`)

**Triggers:**
- Push to `main`, `master`, `develop`
- Pull requests
- Manual dispatch

**Benchmarks:**

#### pytest-benchmark
- Runs tests marked with `@pytest.mark.performance`
- Generates JSON benchmark results
- Stores baseline for comparison
- Alerts on 150%+ regression

#### Memory Profiling
- Tracks memory usage during operations
- Uses `tracemalloc` for profiling
- Reports peak memory usage

**Usage:**
```python
@pytest.mark.performance
def test_large_molecule_loading():
    # Your performance test here
    pass
```

## 🔧 Local Development Setup

### Install Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

### Pre-commit Hooks Included

1. **File checks**: trailing whitespace, EOF fixes, YAML/JSON validation
2. **Black**: Auto-format code (line length: 100)
3. **isort**: Sort imports
4. **Ruff**: Lint and auto-fix issues
5. **mypy**: Type checking
6. **Bandit**: Security scanning
7. **Interrogate**: Docstring coverage (50% minimum)
8. **Safety**: Dependency vulnerability check

### Manual Tool Usage

```bash
# Format code
black molvis_core tests

# Sort imports
isort molvis_core tests

# Lint with Ruff
ruff check molvis_core tests

# Fix linting issues automatically
ruff check --fix molvis_core tests

# Type check
mypy molvis_core --ignore-missing-imports

# Security scan
bandit -r molvis_core

# Check dependencies
safety check

# Run tests with coverage
pytest --cov=molvis_core --cov-report=html

# Complexity analysis
radon cc molvis_core -a -s
radon mi molvis_core -s
```

## 📊 CI/CD Dashboard

### Viewing Workflow Results

1. **Actions Tab**: `https://github.com/Ajaykhanna/MolMan/actions`
2. **Pull Request Checks**: Visible at bottom of each PR
3. **Branch Protection**: Can require checks to pass before merge

### Artifacts

Workflows upload artifacts that persist for 30 days:

- **Coverage Report** (HTML): From CI workflow
- **Bandit Security Report** (JSON): From security workflow
- **Benchmark Results** (JSON): From performance workflow

**Download artifacts:**
```bash
# Via GitHub UI: Actions → Workflow Run → Artifacts section
# Or use GitHub CLI:
gh run download <run-id>
```

## 🚀 CI/CD Best Practices

### For Contributors

1. **Run pre-commit hooks** before pushing
   ```bash
   pre-commit run --all-files
   ```

2. **Run tests locally** before PR
   ```bash
   pytest -v
   ```

3. **Check coverage** for new code
   ```bash
   pytest --cov=molvis_core --cov-report=term-missing
   ```

4. **Add performance tests** for critical operations
   ```python
   @pytest.mark.performance
   def test_operation_speed():
       pass
   ```

### For Maintainers

1. **Review CI failures** before merging
2. **Check security scan results** weekly
3. **Monitor performance benchmarks** for regressions
4. **Update dependencies** regularly
5. **Keep coverage** above 80%

## 📈 Workflow Status Badges

Add to README.md:

```markdown
[![CI](https://github.com/Ajaykhanna/MolMan/workflows/CI%20-%20Tests%20and%20Coverage/badge.svg)](https://github.com/Ajaykhanna/MolMan/actions/workflows/ci.yml)
[![Code Quality](https://github.com/Ajaykhanna/MolMan/workflows/Code%20Quality/badge.svg)](https://github.com/Ajaykhanna/MolMan/actions/workflows/code-quality.yml)
[![Security](https://github.com/Ajaykhanna/MolMan/workflows/Security%20Scanning/badge.svg)](https://github.com/Ajaykhanna/MolMan/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/Ajaykhanna/MolMan/branch/main/graph/badge.svg)](https://codecov.io/gh/Ajaykhanna/MolMan)
```

## 🔐 Required Secrets

Configure in: `Settings → Secrets and variables → Actions`

### Optional but Recommended

- **CODECOV_TOKEN**: For coverage reporting to Codecov
  - Get from: https://codecov.io/
  - Not required for public repos

- **GITHUB_TOKEN**: Automatically provided by GitHub Actions
  - Used for: CodeQL, benchmark storage, artifact uploads

## ⚙️ Configuration Files

### pyproject.toml
Central configuration for all Python tools:
- Black, isort, Ruff, mypy, Bandit, pytest, coverage

### .pre-commit-config.yaml
Pre-commit hook configuration with version pinning

### pytest.ini (legacy)
Can be migrated to pyproject.toml if desired

## 🐛 Troubleshooting

### CI Fails but Tests Pass Locally

1. **Check Python version**: CI tests on multiple versions
2. **Check dependencies**: CI uses fresh install
3. **Check environment**: CI has limited resources

### Pre-commit Hooks Too Slow

```bash
# Skip slow hooks temporarily
SKIP=mypy,interrogate git commit -m "message"

# Update hook versions
pre-commit autoupdate
```

### Type Checking Errors

```bash
# Run mypy with same config as CI
mypy molvis_core --ignore-missing-imports --no-strict-optional

# Add type stubs if missing
pip install types-<package>
```

### Security Scan False Positives

Add to `pyproject.toml`:
```toml
[tool.bandit]
skips = ["B101"]  # Skip specific check
```

## 📝 Extending CI/CD

### Add New Workflow

1. Create `.github/workflows/your-workflow.yml`
2. Define trigger conditions
3. Add jobs and steps
4. Test with manual dispatch

### Add New Test Marker

1. Update `pyproject.toml`:
```toml
[tool.pytest.ini_options]
markers = [
    "your_marker: description",
]
```

2. Use in tests:
```python
@pytest.mark.your_marker
def test_something():
    pass
```

3. Run selectively:
```bash
pytest -m your_marker
```

## 🎯 Phase 10 Success Metrics

- ✅ 4 automated workflows (CI, quality, security, performance)
- ✅ Multi-version Python testing (3.9-3.12)
- ✅ Code coverage tracking with Codecov
- ✅ Pre-commit hooks for local development
- ✅ Security scanning with Bandit, Safety, CodeQL
- ✅ Performance regression detection
- ✅ Automated artifact uploads
- ✅ Comprehensive tool configuration (pyproject.toml)

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pytest Documentation](https://docs.pytest.org/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Black Documentation](https://black.readthedocs.io/)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [pre-commit Documentation](https://pre-commit.com/)

---

**Last Updated**: Phase 10 Implementation
**Status**: ✅ Production Ready
