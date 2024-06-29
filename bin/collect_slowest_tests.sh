#!/bin/bash
# ~/scripts/bin/collect_slowest_tests.sh

# Number of runs
RUNS=100
LOG_DIR=~/scripts/slowest_tests_logs
LOG_FILE=~/scripts/slowest_tests_db.log

# Create log directory if not exists
mkdir -p $LOG_DIR

# Clear log file if it exists
> $LOG_FILE

for ((i=1; i<=RUNS; i++)); do
  echo "Running test iteration $i..."
  mix test --slowest 10 > $LOG_DIR/run_$i.log 2>&1

  # Extract and log the slowest 10 tests
  grep -A 10 "Top 10 slowest" $LOG_DIR/run_$i.log | tail -n 10 >> $LOG_FILE
  echo "Logged results for iteration $i."
done

echo "Completed $RUNS test runs. Results logged in $LOG_FILE."
