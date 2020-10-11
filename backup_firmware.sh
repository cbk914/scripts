#!/bin/ash
# Simple script to backup RAM <> binary file
# Execute on OpenWRT system
FILE="/tmp/backup_firmware.bin"

touch $FILE && 
cd /tmp &&
# u-boot
# cat /dev/mtd0 > /tmp/backup_u-boot.bin
# Art
# cat /dev/mtd4 > /tmp/backup_art.bin
# Firmware + settings
cat /dev/mtd5 > $FILE
#scp $FILE <destination>
# To restore:
# mtd -r write $FILE rootfs_data
