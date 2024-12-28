#!/bin/bash

# Directory of the experiments
EXPERIMENTS_DIR="$(dirname "$0")/.."

# Create logs directory if it doesn't exist
mkdir -p "${EXPERIMENTS_DIR}/logs"

# Define log files
LOG_FILE_FD="${EXPERIMENTS_DIR}/logs/experiment_logs_file_descriptors.txt"
LOG_FILE_NFS="${EXPERIMENTS_DIR}/logs/experiment_logs_nfs.txt"
LOG_FILE_RAMDISK="${EXPERIMENTS_DIR}/logs/experiment_logs_ramdisk.txt"

echo "Starting all hardware optimization experiments..."

# Run experiments and log outputs
bash "$EXPERIMENTS_DIR/file_descriptors_experiment.sh" > "$LOG_FILE_FD" 2>&1
bash "$EXPERIMENTS_DIR/nfs_experiment.sh" > "$LOG_FILE_NFS" 2>&1
bash "$EXPERIMENTS_DIR/ramdisk_experiment.sh" > "$LOG_FILE_RAMDISK" 2>&1

echo "All experiments completed. Logs are saved in the 'logs' directory."
