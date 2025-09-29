#!/usr/bin/env python3
"""
Quick test validation script to check that our test suite works
"""
import subprocess
import sys


def run_command(cmd, description):
    """Run a command and report results"""
    print(f"🧪 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED")
            print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False


def main():
    """Run validation tests"""
    print("🎯 Dakora Test Validation")
    print("=" * 50)

    tests = [
        (
            "export PATH=\"$HOME/.local/bin:$PATH\" && uv run python -m pytest tests/test_init.py -v --tb=no -q",
            "CLI init tests"
        ),
        (
            "export PATH=\"$HOME/.local/bin:$PATH\" && uv run python -m pytest tests/test_playground_server.py::TestPlaygroundServer::test_create_playground_with_config -v --tb=no -q",
            "Playground server creation test"
        ),
        (
            "export PATH=\"$HOME/.local/bin:$PATH\" && uv run python -m pytest tests/test_playground_server.py::TestPlaygroundServerWithTestClient::test_health_endpoint -v --tb=no -q",
            "Playground health endpoint test"
        ),
        (
            "export PATH=\"$HOME/.local/bin:$PATH\" && uv run python -m pytest tests/test_playground_server.py::TestPlaygroundServerWithTestClient::test_template_render_endpoint -v --tb=no -q",
            "Playground template render test"
        ),
    ]

    passed = 0
    total = len(tests)

    for cmd, description in tests:
        if run_command(cmd, description):
            passed += 1

    print()
    print("=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All validation tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())