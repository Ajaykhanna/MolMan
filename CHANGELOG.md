# Changelog

All notable changes to MolMan will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-26 🎉 Production Ready

### Major Milestone: Production-Ready Release

MolMan v1.0.0 represents a complete transformation from a basic visualization tool to a production-ready molecular manipulation platform with enterprise-grade quality assurance, testing, and automation.

### Added

#### Phase 1: Testing Infrastructure
- ✅ **134 comprehensive tests** covering all core functionality
- ✅ **81% code coverage** with HTML and terminal reports
- ✅ **pytest configuration** with custom markers (unit, integration, performance, slow)
- ✅ **Test fixtures** in conftest.py for reusable test data
- ✅ **Coverage reporting** with exclusions and precision settings
- ✅ **Multi-version support**: Python 3.9, 3.10, 3.11, 3.12

**Test Modules:**
- `tests/test_geometry.py` - 23 tests for geometric operations
- `tests/test_io.py` - 27 tests for file I/O operations
- `tests/test_logic.py` - 13 tests for bond detection
- `tests/test_molecule.py` - 20 tests for molecule class
- `tests/test_config.py` - 18 tests for configuration management
- `tests/test_project.py` - 21 tests for project persistence
- `tests/conftest.py` - Shared fixtures (water, benzene, methane molecules)

#### Phase 2: Logging & Error Handling
- ✅ **Structured logging system** with rotating file handlers (10MB, 5 backups)
- ✅ **14 custom exception types** organized by category
- ✅ **Log files** in `~/.molman/logs/` (molman.log, molman_errors.log)
- ✅ **Debug mode** with verbose output and stack traces
- ✅ **Log context decorator** for automatic logging
- ✅ **Integration** across all core modules

**Exception Categories:**
- File I/O: `FileNotFoundError`, `EmptyFileError`, `FileFormatError`, `FileParseError`
- Validation: `InvalidCoordinatesError`, `AtomCountMismatchError`, `DimensionMismatchError`
- Molecular: `InvalidMoleculeError`, `InvalidRotationError`, `InvalidTransformationError`
- Configuration: `ConfigurationError`, `InvalidConfigError`, `MissingConfigError`
- Base: `MolManError` (parent of all exceptions)

**Logging Features:**
- Rotating file handlers with size-based rotation
- Separate error log for quick issue identification
- Console and file logging with independent control
- Debug mode with stack trace capture
- Context manager for automatic logging

#### Phase 3: Configuration Management & State Persistence
- ✅ **Configuration system** with `~/.molman/config.json`
- ✅ **Project format** (.molman) for saving/loading work
- ✅ **Recent files tracking** (last 10 projects with deduplication)
- ✅ **Auto-save functionality** with configurable intervals
- ✅ **Backup creation** with timestamps
- ✅ **Export to XYZ** from projects
- ✅ **Dot-notation access** for configuration (`config.get("preferences.auto_save.enabled")`)
- ✅ **Deep dictionary merging** for configuration defaults

**New Modules:**
- `molvis_core/config.py` (389 lines) - Configuration management
- `molvis_core/project.py` (465 lines) - Project serialization
- `tests/test_config.py` (310 lines) - Configuration tests
- `tests/test_project.py` (386 lines) - Project tests

**Configuration Features:**
- User preferences persistence
- Auto-save with configurable intervals
- Recent files with max count and filtering
- Import/export configuration
- Reset to defaults
- Merge with defaults for upgrades

**Project Features:**
- JSON-based .molman format
- Full molecule serialization (coords, transformations, bonds)
- Metadata support
- Backup creation
- Auto-save path generation
- XYZ export

#### Phase 10: CI/CD Pipeline
- ✅ **4 GitHub Actions workflows** for automation
- ✅ **Matrix testing** across Python 3.9-3.12
- ✅ **Code coverage tracking** with Codecov integration
- ✅ **Security scanning** with 5 tools
- ✅ **Performance monitoring** with pytest-benchmark
- ✅ **Pre-commit hooks** for local development
- ✅ **Automated artifact uploads** (coverage, security reports, benchmarks)

**Workflows:**
1. **CI - Tests and Coverage** (`.github/workflows/ci.yml`)
   - Multi-version Python testing
   - Coverage reporting with Codecov
   - HTML coverage artifacts
   - Test summaries

2. **Code Quality** (`.github/workflows/code-quality.yml`)
   - Ruff linting
   - Black formatting check
   - isort import sorting
   - mypy type checking
   - Radon complexity analysis

3. **Security Scanning** (`.github/workflows/security.yml`)
   - Bandit security scanner
   - Safety dependency scanner
   - CodeQL advanced analysis
   - Dependency review (PRs)
   - Weekly scheduled scans

4. **Performance Testing** (`.github/workflows/performance.yml`)
   - pytest-benchmark integration
   - Memory profiling
   - Regression detection (150% threshold)
   - Baseline storage

**Developer Tools:**
- Pre-commit hooks configuration (`.pre-commit-config.yaml`)
- Central tool configuration (`pyproject.toml`)
- Local CI testing script (`test_ci_locally.py`)
- Comprehensive documentation

**Security Tools:**
- Bandit (Python security linting)
- Safety (dependency vulnerability scanning)
- CodeQL (semantic code analysis)
- Dependency Review (PR dependency scanning)
- Pre-commit security hooks

### Changed

#### Core Improvements
- **All modules** now use structured logging instead of print statements
- **All modules** use custom exceptions instead of generic errors
- **Test files** updated to expect custom exceptions
- **Configuration** is now persistent across sessions
- **Projects** can be saved and loaded with full state

#### API Enhancements
- `Molecule` class now logs initialization and transformations
- `Project` class added for managing multiple molecules
- `ConfigManager` class added for user preferences
- File I/O functions now log operations and handle errors gracefully

#### Development Workflow
- Black formatting enforced (line-length: 100)
- isort import sorting with Black profile
- Ruff linting with comprehensive rule set
- mypy type checking (relaxed for gradual adoption)
- Pre-commit hooks run automatically

### Documentation

#### New Documentation
- **README.md** - Completely rewritten for v1.0 (640+ lines)
  - Production-ready focus
  - Comprehensive feature list
  - Installation instructions
  - Quick start guides
  - Architecture overview
  - Testing guide
  - Configuration guide
  - Development guide
  - CI/CD overview

- **CI_CD_GUIDE.md** (430 lines)
  - Complete CI/CD documentation
  - Workflow explanations
  - Local development setup
  - Tool usage examples
  - Troubleshooting guide

- **TESTING_CI_CD.md** (430 lines)
  - Local CI testing guide
  - Troubleshooting common issues
  - Best practices
  - Quick fixes reference

- **TESTING_PHASE3.md** (704 lines)
  - Configuration testing guide
  - Project persistence testing
  - Python REPL examples
  - Manual testing instructions

- **CHANGELOG.md** - This file

#### Updated Documentation
- **planned_upgrades.md** - Updated with Phase 1-3, 10 completion status
- **.github/README.md** - Quick reference for workflows

### Fixed

#### CI/CD Fixes
- Fixed `pyproject.toml` license format (deprecated warning)
- Added explicit package discovery to prevent multi-package error
- Updated Python version classifiers

#### Test Fixes
- Updated all tests to use custom exceptions
- Fixed test isolation issues in configuration tests
- Fixed deep copy issues in ConfigManager

### Infrastructure

#### Project Structure
```
MolMan/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── code-quality.yml
│   │   ├── security.yml
│   │   └── performance.yml
│   └── README.md
├── molvis_core/
│   ├── config.py          # NEW
│   ├── project.py         # NEW
│   ├── logging_config.py  # NEW
│   ├── exceptions.py      # NEW
│   ├── geometry.py        # ENHANCED
│   ├── io.py             # ENHANCED
│   ├── logic.py          # ENHANCED
│   └── molecule.py       # ENHANCED
├── tests/
│   ├── conftest.py       # NEW
│   ├── test_config.py    # NEW
│   ├── test_project.py   # NEW
│   ├── test_geometry.py  # UPDATED
│   ├── test_io.py        # UPDATED
│   ├── test_logic.py     # UPDATED
│   └── test_molecule.py  # UPDATED
├── .pre-commit-config.yaml   # NEW
├── pyproject.toml           # NEW
├── CI_CD_GUIDE.md          # NEW
├── TESTING_CI_CD.md        # NEW
├── TESTING_PHASE3.md       # NEW
├── CHANGELOG.md            # NEW
├── test_ci_locally.py      # NEW
├── demo_phase3.py          # NEW
├── quick_test_phase3.py    # NEW
└── README.md               # COMPLETELY REWRITTEN
```

#### Metrics
- **Lines of Code**: ~5,000+ (production code)
- **Test Coverage**: 81% (134 tests)
- **Python Versions**: 3.9, 3.10, 3.11, 3.12
- **Dependencies**: Minimal (NumPy, Matplotlib)
- **CI/CD Workflows**: 4 automated pipelines
- **Security Tools**: 5 scanning tools
- **Documentation**: 2,000+ lines

### Performance

- Added performance benchmarking infrastructure
- Memory profiling capabilities
- Regression detection (150% threshold)
- Baseline storage for comparison

### Security

- 5 automated security scanning tools
- Weekly scheduled vulnerability scans
- Dependency vulnerability tracking
- Pre-commit security hooks
- CodeQL semantic analysis

---

## [0.x] - Beta Versions

### Features
- Basic molecular visualization
- XYZ file support
- Tkinter GUI interface
- Streamlit web interface
- Translation and rotation controls
- Bond visualization
- Multi-molecule support

### Known Limitations
- No persistent configuration
- Limited error handling
- No automated testing
- Manual quality checks
- No CI/CD pipeline

---

## Version Comparison

| Feature | v0.x (Beta) | v1.0.0 (Production) |
|---------|-------------|---------------------|
| **Tests** | None | 134 tests (81% coverage) |
| **CI/CD** | Manual | 4 automated workflows |
| **Error Handling** | Basic | 14 custom exceptions |
| **Logging** | Print statements | Structured logging with rotation |
| **Configuration** | Hardcoded | Persistent user preferences |
| **Projects** | Individual XYZ files | .molman project format |
| **Documentation** | Basic README | 2,000+ lines of docs |
| **Security** | None | 5 scanning tools |
| **Code Quality** | Manual | Automated (Black, Ruff, mypy) |
| **Python Support** | 3.x | 3.9, 3.10, 3.11, 3.12 |

---

## Migration Guide (v0.x to v1.0)

### For Users

1. **Install v1.0:**
   ```bash
   git pull origin main
   pip install -e .
   ```

2. **Configuration:**
   - First run creates `~/.molman/config.json`
   - Customize preferences as needed

3. **Projects:**
   - Old XYZ files still work
   - Save as .molman for new features

### For Developers

1. **Update environment:**
   ```bash
   pip install -e '.[dev]'
   pre-commit install
   ```

2. **Run tests:**
   ```bash
   pytest -v
   ```

3. **Code quality:**
   ```bash
   python test_ci_locally.py
   ```

---

## Acknowledgments

This release represents a complete transformation of MolMan into a production-ready tool. Special thanks to:

- The open-source community for excellent tools
- Computational chemistry community for feedback
- All contributors and testers

---

[1.0.0]: https://github.com/Ajaykhanna/MolMan/releases/tag/v1.0.0
