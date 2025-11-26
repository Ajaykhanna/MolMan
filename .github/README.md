# GitHub Actions Workflows

This directory contains automated CI/CD workflows for MolMan.

## Workflows

### 🧪 ci.yml - CI: Tests and Coverage
**Runs on**: Push to main/develop/claude/**, Pull Requests

**Purpose**: Comprehensive testing across multiple Python versions

**Features**:
- Matrix testing: Python 3.9, 3.10, 3.11, 3.12
- Full pytest suite execution (134 tests)
- Code coverage reporting (Codecov + HTML artifacts)
- Dependency caching for faster builds
- Test summaries in GitHub Actions UI

**Artifacts**: Coverage HTML report (30-day retention)

---

### 🎨 code-quality.yml - Code Quality
**Runs on**: Push to main/develop/claude/**, Pull Requests

**Purpose**: Enforce code quality standards

**Checks**:
1. **Lint and Format**
   - Ruff (fast linter)
   - Black (code formatter)
   - isort (import sorting)

2. **Type Checking**
   - mypy (static type analysis)

3. **Complexity Analysis**
   - Radon (cyclomatic complexity)
   - Maintainability index

**Note**: Uses `continue-on-error` to report issues without blocking PRs

---

### 🔒 security.yml - Security Scanning
**Runs on**: Push, Pull Requests, Weekly schedule (Mon 00:00 UTC)

**Purpose**: Detect security vulnerabilities

**Scanners**:
1. **Bandit**: Python code security scanner
2. **Safety**: Dependency vulnerability checker
3. **Dependency Review**: PR-only dependency security
4. **CodeQL**: GitHub's advanced security analysis

**Artifacts**: Bandit JSON reports (30-day retention)

**Schedule**: Automated weekly scans on Mondays

---

### ⚡ performance.yml - Performance Testing
**Runs on**: Push to main/develop, Pull Requests

**Purpose**: Detect performance regressions

**Tests**:
1. **Benchmarks**: pytest-benchmark for performance tests
2. **Memory Profiling**: tracemalloc for memory usage analysis

**Features**:
- Baseline storage for comparison
- 150% regression alerting
- Benchmark artifacts

**Usage**: Mark tests with `@pytest.mark.performance`

---

## Quick Reference

### Trigger All Workflows
```bash
git push origin your-branch
```

### Manual Workflow Dispatch
All workflows support manual triggering via GitHub UI:
`Actions → Select Workflow → Run workflow`

### View Results
- **Actions Tab**: https://github.com/Ajaykhanna/MolMan/actions
- **Pull Requests**: Check section at bottom of PR
- **Branch Protection**: Configure in repository settings

### Download Artifacts
```bash
# Via GitHub CLI
gh run download <run-id>

# Via GitHub UI
Actions → Workflow Run → Artifacts section
```

## Configuration Files

- **pyproject.toml**: Central tool configuration (Black, Ruff, mypy, Bandit, pytest)
- **.pre-commit-config.yaml**: Pre-commit hooks for local development

See `CI_CD_GUIDE.md` for detailed documentation.

## Troubleshooting

### Workflow Fails
1. Check workflow logs in Actions tab
2. Run tests locally: `pytest -v`
3. Run code quality checks: `pre-commit run --all-files`

### Coverage Upload Fails
- Codecov token may be missing (optional for public repos)
- HTML artifact still generated

### Security Scan Warnings
- Review Bandit report artifacts
- Check Safety output for vulnerable dependencies
- Address CodeQL findings in Security tab

## Maintenance

### Update Dependencies
```bash
# Update pre-commit hooks
pre-commit autoupdate

# Update GitHub Actions
# Manually update version numbers in workflow files
```

### Add New Workflow
1. Create `.github/workflows/your-workflow.yml`
2. Define triggers and jobs
3. Test with manual dispatch
4. Update this README

---

**Last Updated**: Phase 10 Implementation (2025-11-26)
