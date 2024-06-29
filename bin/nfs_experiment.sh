#!/bin/bash
# ~/scripts/bin/nfs_experiment.sh

# Log File
LOG_FILE=~/scripts/experiment_logs_nfs.txt

# Mount Network File System
NFS_SERVER="your_nfs_server"
NFS_PATH="/path/on/nfs"
MOUNT_POINT="/mnt/nfs_test"

echo "Mounting Network File System..."
sudo mount -t nfs $NFS_SERVER:$NFS_PATH $MOUNT_POINT

# Check if NFS was mounted
if [ $? -ne 0 ]; then
  echo "Failed to mount NFS" | tee -a $LOG_FILE
  exit 1
fi

# Run Tests in NFS
echo "Running tests in NFS..."
pushd $MOUNT_POINT
START_TIME=$(date +%s)
mix test > $LOG_FILE 2>&1
END_TIME=$(date +%s)
popd

# Measure Time Taken
DURATION=$((END_TIME - START_TIME))
echo "Time taken for tests in NFS: $DURATION seconds" >> $LOG_FILE

# Unmount Network File System
echo "Unmounting Network File System..."
sudo umount $MOUNT_POINT

echo "NFS experiment completed."
