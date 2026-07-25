#!/bin/bash
# Run all tests with coverage reporting

echo "Running all tests..."

# Run pytest with coverage
python -m pytest \
    --cov=src \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --cov-report=xml:coverage.xml \
    --cov-fail-under=75 \
    -v \
    --tb=short \
    tests/

# Exit with pytest exit code
exit $?