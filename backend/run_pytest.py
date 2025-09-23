#!/usr/bin/env python3
"""
Pytest test runner for backend with proper configuration.
"""

import sys
import os
import subprocess

# Fix Windows console encoding
if os.name == 'nt':
    try:
        os.system('chcp 65001 > nul')
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_unit_tests():
    """Run unit tests only."""
    print("🧪 Running Unit Tests with pytest")
    print("=" * 50)

    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_models.py",
        "tests/test_config.py",
        "tests/test_api.py",
        "tests/test_api_models.py",
        "tests/test_api_endpoints.py",
        "-v",
        "--tb=short",
        "-m", "unit",
        "--disable-warnings"
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))
    return result.returncode

def run_all_tests():
    """Run all available tests."""
    print("🧪 Running All Available Tests with pytest")
    print("=" * 50)

    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_models.py",
        "tests/test_config.py",
        "tests/test_api.py",
        "tests/test_api_models.py",
        "tests/test_api_endpoints.py",
        "-v",
        "--tb=short",
        "--disable-warnings"
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))
    return result.returncode

def run_with_coverage():
    """Run tests with detailed output (coverage tool not available)."""
    print("🧪 Running Tests with Detailed Output")
    print("=" * 50)
    print("Note: Coverage tool not installed. Install with: pip install pytest-cov")

    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_models.py",
        "tests/test_config.py",
        "tests/test_api.py",
        "tests/test_api_models.py",
        "tests/test_api_endpoints.py",
        "-v",
        "--tb=long",
        "-s",
        "--disable-warnings"
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))
    return result.returncode

def run_database_tests():
    """Run database integration tests only."""
    print("🗄️ Running Database Integration Tests")
    print("=" * 50)
    print("Note: Requires a test database connection")

    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_repositories.py",
        "tests/test_database_integration.py",
        "-v",
        "--tb=short",
        "-m", "database",
        "--run-database-tests",
        "--disable-warnings"
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))
    return result.returncode

def run_full_suite():
    """Run all tests including database tests."""
    print("🚀 Running Full Test Suite (Unit + Database)")
    print("=" * 50)

    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--disable-warnings"
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))
    return result.returncode

def main():
    """Run tests based on command line arguments."""
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "unit":
            exit_code = run_unit_tests()
        elif mode == "coverage":
            exit_code = run_with_coverage()
        elif mode == "all":
            exit_code = run_all_tests()
        elif mode == "database" or mode == "db":
            exit_code = run_database_tests()
        elif mode == "full":
            exit_code = run_full_suite()
        else:
            print(f"Unknown mode: {mode}")
            print("Usage: python run_pytest.py [unit|all|coverage|database|db|full]")
            print("")
            print("Modes:")
            print("  unit     - Run unit tests only (no database)")
            print("  all      - Run all unit tests (default)")
            print("  database - Run database integration tests only")
            print("  db       - Alias for database")
            print("  full     - Run complete test suite (unit + database)")
            print("  coverage - Run with detailed output")
            exit_code = 1
    else:
        exit_code = run_all_tests()

    print("\n" + "=" * 50)
    if exit_code == 0:
        print("🎉 All tests passed!")
    else:
        print("💥 Some tests failed!")

    return exit_code

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)