#!/bin/bash
# ~/scripts/bin/file_descriptors_experiment.sh

# Increase File Descriptors Limit
echo "Increasing file descriptors limit..."
ORIGINAL_LIMIT=$(ulimit -n)
NEW_LIMIT=4096
ulimit -n $NEW_LIMIT

# Run Tests
echo "Running tests with increased file descriptors limit..."
START_TIME=$(date +%s)
mix test
END_TIME=$(date +%s)

# Measure Time Taken
DURATION=$((END_TIME - START_TIME))
echo "Time taken for tests with increased file descriptors limit: $DURATION seconds"

# Revert File Descriptors Limit
echo "Reverting file descriptors limit..."
ulimit -n $ORIGINAL_LIMIT

echo "File descriptors limit experiment completed."
