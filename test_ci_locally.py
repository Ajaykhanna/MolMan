#!/usr/bin/env python3
"""
CI/CD Local Testing Script

This script simulates what the CI workflows do, allowing you to test
locally before pushing to GitHub.
"""

import subprocess
import sys


def run_command(cmd, description, continue_on_error=False):
    """Run a command and report results."""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}")
    print(f"Command: {cmd}\n")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if result.returncode != 0:
        if continue_on_error:
            print(f"⚠️  {description} had issues (continuing)")
            return False
        else:
            print(f"❌ {description} failed!")
            return False
    else:
        print(f"✅ {description} passed!")
        return True


def main():
    """Run all CI checks locally."""
    print("="*60)
    print("  MolMan CI/CD Local Testing")
    print("="*60)
    print("\nThis script runs the same checks as GitHub Actions CI/CD.\n")

    results = {}

    # 1. Package Installation Test
    results['install'] = run_command(
        "pip install -e . -q",
        "Package Installation Test"
    )

    # 2. Test Suite
    results['tests'] = run_command(
        "pytest -v --tb=short",
        "Full Test Suite (134 tests)"
    )

    # 3. Code Coverage
    results['coverage'] = run_command(
        "pytest --cov=molvis_core --cov-report=term-missing --cov-report=html",
        "Code Coverage Report"
    )

    # 4. Black Formatting Check
    results['black'] = run_command(
        "black --check --diff molvis_core tests",
        "Black Code Formatting",
        continue_on_error=True
    )

    # 5. Import Sorting Check
    results['isort'] = run_command(
        "isort --check-only --diff molvis_core tests",
        "isort Import Sorting",
        continue_on_error=True
    )

    # 6. Ruff Linting
    results['ruff'] = run_command(
        "ruff check molvis_core tests",
        "Ruff Linting",
        continue_on_error=True
    )

    # 7. Type Checking
    results['mypy'] = run_command(
        "mypy molvis_core --ignore-missing-imports --no-strict-optional",
        "mypy Type Checking",
        continue_on_error=True
    )

    # 8. Security Scanning
    results['bandit'] = run_command(
        "bandit -r molvis_core -ll",
        "Bandit Security Scan",
        continue_on_error=True
    )

    # Summary
    print("\n" + "="*60)
    print("  SUMMARY")
    print("="*60 + "\n")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for check, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {check:20s} {'PASSED' if status else 'FAILED'}")

    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} checks passed")
    print(f"{'='*60}\n")

    if passed == total:
        print("🎉 All checks passed! Ready to push.")
        return 0
    elif results['install'] and results['tests']:
        print("⚠️  Core functionality works, but code quality checks need attention.")
        print("    You can fix these with:")
        print("      black molvis_core tests")
        print("      isort molvis_core tests")
        print("      ruff check --fix molvis_core tests")
        return 0
    else:
        print("❌ Critical issues found. Please fix before pushing.")
        return 1


if __name__ == "__main__":
    # Check if required tools are installed
    required_tools = ['pytest', 'black', 'isort', 'ruff', 'mypy', 'bandit']
    missing_tools = []

    for tool in required_tools:
        result = subprocess.run(f"which {tool}", shell=True, capture_output=True)
        if result.returncode != 0:
            missing_tools.append(tool)

    if missing_tools:
        print("⚠️  Missing tools. Install with:")
        print(f"    pip install {' '.join(missing_tools)} pytest-cov pytest-mock")
        print("\nOr install all dev dependencies:")
        print("    pip install -e '.[dev]'")
        sys.exit(1)

    sys.exit(main())
