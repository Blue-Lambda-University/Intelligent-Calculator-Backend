#!/bin/bash
set -e

echo "=================================="
echo " Jenkins Pipeline Test Started"
echo "=================================="

echo "Running on host: $(hostname)"

echo "Current directory: $(pwd)"
echo "Current user: $(whoami)"
echo "Build number: ${BUILD_NUMBER:-N/A}"
echo "Step 1: Checking environment..."
echo "Environment check passed!"

echo "Step 2: Simulating build..."
sleep 2
echo "Build completed successfully!"

echo "Step 3: Simulating tests..."
sleep 2
echo "All tests passed!"

echo "=================================="
echo " Jenkins Pipeline Test SUCCESS!"
echo "=================================="

exit 0