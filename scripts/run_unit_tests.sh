#!/bin/bash
# Run unit tests only

echo "Running unit tests..."

# Run pytest with unit marker
python -m pytest \
    --cov=src \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --cov-report=xml:coverage.xml \
    --cov-fail-under=75 \
    -v \
    --tb=short \
    -m unit \
    tests/

# Exit with pytest exit code
exit $?