#!/usr/bin/env python3
"""Test runner for Mock Data Connector"""

import sys
import os
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
# Add base connector to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../feature_1_1_base_connector/src'))


def run_tests():
    """Run all tests and generate coverage report"""
    
    # Test arguments
    args = [
        'tests/',
        '-v',  # Verbose
        '--color=yes',  # Colored output
        '--tb=short',  # Short traceback format
        '--cov=src',  # Coverage for src directory
        '--cov-report=html',  # HTML coverage report
        '--cov-report=term-missing',  # Terminal report with missing lines
        '--cov-fail-under=90',  # Fail if coverage is below 90%
    ]
    
    # Run pytest
    exit_code = pytest.main(args)
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
        print("📊 Coverage report generated in htmlcov/index.html")
    else:
        print("\n❌ Tests failed!")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(run_tests())