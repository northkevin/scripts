#!/bin/bash
# ~/scripts/bin/ramdisk_experiment.sh


# Create RAM Disk
RAMDISK_SIZE=8388608 # Adjust the size as needed
RAMDISK_NAME="RAMDisk"
MOUNT_POINT="/Volumes/$RAMDISK_NAME"

echo "Creating RAM Disk..."
diskutil erasevolume HFS+ "$RAMDISK_NAME" `hdiutil attach -nomount ram://$RAMDISK_SIZE`

# Check if RAM Disk was created
if [ $? -ne 0 ]; then
  echo "Failed to create RAM Disk"
  exit 1
fi

# Run Tests in RAM Disk
echo "Running tests in RAM Disk..."
pushd $MOUNT_POINT
START_TIME=$(date +%s)
mix test
END_TIME=$(date +%s)
popd

# Measure Time Taken
DURATION=$((END_TIME - START_TIME))
echo "Time taken for tests in RAM Disk: $DURATION seconds"

# Detach RAM Disk
echo "Detaching RAM Disk..."
diskutil eject $MOUNT_POINT

echo "RAM Disk experiment completed."
