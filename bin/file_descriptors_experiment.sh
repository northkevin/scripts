#!/bin/bash
# ~/scripts/bin/file_descriptors_experiment.sh

# Log File
LOG_FILE=~/scripts/experiment_logs_file_descriptors.txt

# Increase File Descriptors Limit
echo "Increasing file descriptors limit..."
ORIGINAL_LIMIT=$(ulimit -n)
NEW_LIMIT=4096
ulimit -n $NEW_LIMIT

# Run Tests
echo "Running tests with increased file descriptors limit..."
START_TIME=$(date +%s)
mix test > $LOG_FILE 2>&1
END_TIME=$(date +%s)

# Measure Time Taken
DURATION=$((END_TIME - START_TIME))
echo "Time taken for tests with increased file descriptors limit: $DURATION seconds" >> $LOG_FILE

# Revert File Descriptors Limit
echo "Reverting file descriptors limit..."
ulimit -n $ORIGINAL_LIMIT

echo "File descriptors limit experiment completed."
