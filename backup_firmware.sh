#!/bin/ash
# Simple script to backup RAM to binary file
# Execute on OpenWRT system
FILE="/tmp/backup_firmware.bin"

touch $FILE && 
cd /tmp &&
cat /dev/mtd5 > $FILE
#scp $FILE <destination>
# To restore:
# mtd -r write $FILE rootfs_data
