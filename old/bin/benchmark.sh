#!/bin/bash

# Function to display usage
usage() {
  echo "Usage: $0 -n <number_of_runs> -c \"<command_to_benchmark>\""
  exit 1
}

# Parse command-line arguments
while getopts "n:c:" opt; do
  case ${opt} in
    n )
      NUM_RUNS=$OPTARG
      ;;
    c )
      COMMAND=$OPTARG
      ;;
    \? )
      usage
      ;;
  esac
done

# Check if required arguments are provided
if [ -z "$NUM_RUNS" ] || [ -z "$COMMAND" ]; then
  usage
fi

# Array to store individual run times
declare -a run_times

echo "Running '$COMMAND' $NUM_RUNS times..."

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

# Run the command the specified number of times
for ((i=1; i<=NUM_RUNS; i++)); do
  echo "Run #$i..."
  start_time=$(date +%s.%N)
  eval $COMMAND > /dev/null 2>&1
  end_time=$(date +%s.%N)
  elapsed_time=$(echo "$end_time - $start_time" | bc)
  run_times+=($elapsed_time)
  echo "Run #$i took $elapsed_time seconds"
done

# Calculate and print the average time
average_time=$(calculate_average $NUM_RUNS)
echo "Average time over $NUM_RUNS runs: $average_time seconds"
