#!/bin/bash

# Number of times to run the test suite
NUM_RUNS=$1

if [ -z "$NUM_RUNS" ]; then
  echo "Usage: $0 <number_of_runs>"
  exit 1
fi

# Array to store individual run times
declare -a run_times

echo "Running mix test $NUM_RUNS times..."

# Function to calculate average
calculate_average() {
  sum=0
  count=$1
  for time in "${run_times[@]}"; do
    sum=$(echo "$sum + $time" | bc)
  done
  average=$(echo "scale=2; $sum / $count" | bc)
  echo $average
}

# Run the tests the specified number of times
for ((i=1; i<=NUM_RUNS; i++)); do
  echo "Run #$i..."
  start_time=$(date +%s.%N)
  mix test > /dev/null 2>&1
  end_time=$(date +%s.%N)
  elapsed_time=$(echo "$end_time - $start_time" | bc)
  run_times+=($elapsed_time)
  echo "Run #$i took $elapsed_time seconds"
done

# Calculate and print the average time
average_time=$(calculate_average $NUM_RUNS)
echo "Average time over $NUM_RUNS runs: $average_time seconds"
