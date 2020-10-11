#!/bin/ash
# Upgrade OpenWRT firmware for AR750 to newest snapshot
cd /tmp &&
wget http://downloads.openwrt.org/snapshots/targets/ar71xx/generic/openwrt-ar71xx-generic-gl-ar750-squashfs-sysupgrade.bin &&
sysupgrade /tmp/openwrt-ar71xx-generic-gl-ar750-squashfs-sysupgrade.bin
# 19.07 branch
#wget https://downloads.openwrt.org/releases/19.07-SNAPSHOT/targets/ar71xx/generic/openwrt-19.07-snapshot-r11217-b21bea7b1b-ar71xx-generic-gl-ar750-squashfs-sysupgrade.bin && sysupgrade /tmp/openwrt-19.07-snapshot-r11217-b21bea7b1b-ar71xx-generic-gl-ar750-squashfs-sysupgrade.bin 

