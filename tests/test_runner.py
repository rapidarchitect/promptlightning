#!/usr/bin/env python3
"""
Test runner for Dakora with different test categories
"""
import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(test_type="all", verbose=False, fast=False):
    """Run different categories of tests"""

    # Base pytest command
    cmd = ["python", "-m", "pytest"]

    if verbose:
        cmd.append("-v")

    # Add coverage if requested
    cmd.extend(["--tb=short"])

    # Determine which tests to run
    test_files = []

    if test_type == "all":
        test_files = [
            "tests/test_init.py",
            "tests/test_playground_server.py",
            "tests/test_playground_api.py"
        ]
        if not fast:
            test_files.append("tests/test_playground_performance.py")

    elif test_type == "unit":
        test_files = [
            "tests/test_init.py",
            "tests/test_playground_server.py"
        ]

    elif test_type == "integration":
        test_files = ["tests/test_playground_api.py"]

    elif test_type == "performance":
        test_files = ["tests/test_playground_performance.py"]
        if fast:
            cmd.extend(["-m", "not slow"])  # Skip slow tests in fast mode

    elif test_type == "smoke":
        # Just run a few basic tests quickly
        cmd.extend([
            "tests/test_init.py::test_init_creates_proper_structure",
            "tests/test_playground_server.py::TestPlaygroundServer::test_create_playground_with_config",
            "tests/test_playground_api.py::TestPlaygroundHealthAPI::test_health_endpoint_returns_200"
        ])

    else:
        print(f"Unknown test type: {test_type}")
        return 1

    # Add test files to command
    cmd.extend(test_files)

    print(f"Running tests: {' '.join(cmd)}")
    print("-" * 60)

    # Run the tests
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
        return result.returncode
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Run Dakora tests")
    parser.add_argument(
        "test_type",
        nargs="?",
        default="all",
        choices=["all", "unit", "integration", "performance", "smoke"],
        help="Type of tests to run"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "-f", "--fast",
        action="store_true",
        help="Skip slow tests"
    )

    args = parser.parse_args()

    print("🧪 Dakora Test Runner")
    print(f"Test type: {args.test_type}")
    if args.fast:
        print("Fast mode: skipping slow tests")
    print("")

    return run_tests(args.test_type, args.verbose, args.fast)


if __name__ == "__main__":
    sys.exit(main())