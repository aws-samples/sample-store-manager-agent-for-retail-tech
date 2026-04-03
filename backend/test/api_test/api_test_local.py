#!/usr/bin/env python3
"""
API test runner for Store Daily QA System
Executes pytest with Docker integration (called from main.py)
"""

import sys
import subprocess
from pathlib import Path
import argparse


def run_tests(test_module=None, verbose=False, exclude_agent=False):
    """
    Run API tests (assumes Docker services already running)

    Args:
        test_module: Specific test module to run
        verbose: Enable verbose output
        exclude_agent: Exclude agent API tests
    """
    test_dir = Path(__file__).parent

    cmd = ["uv", "run", "python", "-m", "pytest"]

    if test_module == "agent":
        cmd.extend(["-m", "agent", "."])
    elif test_module:
        cmd.append(f"test_{test_module}.py")
    elif exclude_agent:
        cmd.extend(["-m", "not agent", "."])
    else:
        cmd.append(".")

    if verbose:
        cmd.append("-v")

    cmd.extend(["--tb=short", "--no-header", "--disable-warnings"])

    print(f"Running API tests in: {test_dir}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 40)

    try:
        result = subprocess.run(cmd, cwd=test_dir, capture_output=False)
        return result.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run Store Daily QA System API tests")
    parser.add_argument(
        "--module",
        choices=[
            "admin",
            "survey",
            "chat",
            "insights",
            "admin_errors",
            "survey_errors",
            "insights_errors",
            "agent",
        ],
        help="Run tests for specific module only",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "--exclude-agent", action="store_true", help="Exclude agent API tests"
    )

    args = parser.parse_args()

    exit_code = run_tests(args.module, args.verbose, args.exclude_agent)

    if exit_code == 0:
        print("\n✅ API tests passed!")
    else:
        print("\n❌ API tests failed!")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
