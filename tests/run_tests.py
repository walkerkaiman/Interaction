#!/usr/bin/env python3
"""
Test runner script for the Interaction Framework.
Provides convenient commands to run different test suites.
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"\n❌ {description} failed with exit code {result.returncode}")
        return False
    else:
        print(f"\n✅ {description} completed successfully")
        return True


def install_dependencies():
    """Install test dependencies."""
    print("Installing test dependencies...")
    
    commands = [
        (["pip", "install", "-r", "requirements.txt"], "Installing Python dependencies"),
        (["playwright", "install", "chromium"], "Installing Playwright browsers"),
    ]
    
    for cmd, desc in commands:
        if not run_command(cmd, desc):
            return False
    return True


def run_unit_tests():
    """Run unit tests only."""
    cmd = ["python", "-m", "pytest", "tests/test_module_system.py", "-v", "-m", "not slow"]
    return run_command(cmd, "Unit Tests")


def run_api_tests():
    """Run API tests."""
    cmd = ["python", "-m", "pytest", "tests/test_api_endpoints.py", "-v"]
    return run_command(cmd, "API Tests")


def run_frontend_tests():
    """Run frontend UI tests."""
    cmd = ["python", "-m", "pytest", "tests/test_frontend_ui.py", "-v", "--headed"]
    return run_command(cmd, "Frontend UI Tests")


def run_performance_tests():
    """Run performance tests."""
    cmd = ["python", "-m", "pytest", "tests/test_performance.py", "-v", "-m", "not slow"]
    return run_command(cmd, "Performance Tests")


def run_integration_tests():
    """Run integration tests."""
    cmd = ["python", "-m", "pytest", "tests/test_integration.py", "-v"]
    return run_command(cmd, "Integration Tests")


def run_all_tests():
    """Run all tests."""
    cmd = ["python", "-m", "pytest", "tests/", "-v", "--maxfail=5"]
    return run_command(cmd, "All Tests")


def run_quick_tests():
    """Run quick regression tests (unit + API)."""
    cmd = ["python", "-m", "pytest", "tests/test_module_system.py", "tests/test_api_endpoints.py", "-v", "-m", "not slow"]
    return run_command(cmd, "Quick Regression Tests")


def run_ci_tests():
    """Run tests suitable for CI/CD (headless, no slow tests)."""
    cmd = ["python", "-m", "pytest", "tests/", "-v", "--maxfail=3", "-m", "not slow", "--headless"]
    return run_command(cmd, "CI/CD Tests")


def main():
    parser = argparse.ArgumentParser(
        description="Test runner for Interaction Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test Suites:
  unit        - Run unit tests (fast)
  api         - Run API endpoint tests
  frontend    - Run frontend UI tests (requires display)
  performance - Run performance tests
  integration - Run integration tests
  all         - Run all tests
  quick       - Run quick regression tests (unit + api)
  ci          - Run CI-suitable tests (headless, no slow tests)
  install     - Install test dependencies

Examples:
  python run_tests.py quick         # Quick regression tests
  python run_tests.py api           # Just API tests
  python run_tests.py all           # Full test suite
  python run_tests.py install       # Install dependencies
        """
    )
    
    parser.add_argument(
        "suite",
        choices=["unit", "api", "frontend", "performance", "integration", "all", "quick", "ci", "install"],
        help="Test suite to run"
    )
    
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install dependencies before running tests"
    )
    
    args = parser.parse_args()
    
    # Change to project root directory
    project_root = Path(__file__).parent.parent
    import os
    os.chdir(project_root)
    
    success = True
    
    # Install dependencies if requested
    if args.install_deps or args.suite == "install":
        success = install_dependencies()
        if args.suite == "install":
            return 0 if success else 1
        if not success:
            return 1
    
    # Run the requested test suite
    test_runners = {
        "unit": run_unit_tests,
        "api": run_api_tests,
        "frontend": run_frontend_tests,
        "performance": run_performance_tests,
        "integration": run_integration_tests,
        "all": run_all_tests,
        "quick": run_quick_tests,
        "ci": run_ci_tests,
    }
    
    runner = test_runners.get(args.suite)
    if runner:
        success = runner()
    else:
        print(f"Unknown test suite: {args.suite}")
        return 1
    
    if success:
        print(f"\n🎉 {args.suite.title()} tests completed successfully!")
        return 0
    else:
        print(f"\n💥 {args.suite.title()} tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())