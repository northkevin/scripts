#!/bin/bash

# ~/scripts/bin/run_experiments.sh

# Experiment Log File
LOG_FILE=~/scripts/experiment_logs.txt

# Function to log messages
log_message() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
}

# RAM Disk Experiment
log_message "Starting RAM Disk experiment"
~/scripts/bin/ramdisk_experiment.sh
if [ $? -eq 0 ]; then
  log_message "Completed RAM Disk experiment successfully"
else
  log_message "RAM Disk experiment encountered errors"
fi

# File Descriptors Limit Experiment
log_message "Starting File Descriptors Limit experiment"
~/scripts/bin/file_descriptors_experiment.sh
if [ $? -eq 0 ]; then
  log_message "Completed File Descriptors Limit experiment successfully"
else
  log_message "File Descriptors Limit experiment encountered errors"
fi

# Network File System Experiment
log_message "Starting Network File System experiment"
~/scripts/bin/nfs_experiment.sh
if [ $? -eq 0 ]; then
  log_message "Completed Network File System experiment successfully"
else
  log_message "Network File System experiment encountered errors"
fi

echo "All experiments completed. Check $LOG_FILE for details."
