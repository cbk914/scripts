#!/bin/ash
# Upgrade OpenWRT firmware for AR750 to newest snapshot
#
# SECURITY: the original was
#     wget http://downloads.openwrt.org/.../openwrt-...-sysupgrade.bin && \
#     sysupgrade /tmp/openwrt-...-sysupgrade.bin
#
# Flashing a root filesystem over plaintext HTTP with no integrity check is the
# worst case in this repository: anyone on the network path can substitute the
# image and either brick the device or install firmware that owns it
# permanently, below the level any later update would necessarily fix.
#
# This version requires HTTPS and a pinned SHA-256, and refuses to flash
# anything it has not verified.
#
# Copy lib/verify_download.sh alongside this script; it must sit in ./lib/.
#
# Set FIRMWARE_SHA256 to the digest of the exact image you intend to flash.
# For a snapshot build, fetch the official index over HTTPS and take the value
# from it:
#     https://downloads.openwrt.org/snapshots/targets/ar71xx/generic/sha256sums
FIRMWARE_SHA256="${FIRMWARE_SHA256:-UNPINNED}"

FIRMWARE_URL="https://downloads.openwrt.org/snapshots/targets/ar71xx/generic/openwrt-ar71xx-generic-gl-ar750-squashfs-sysupgrade.bin"
FIRMWARE_FILE="/tmp/openwrt-ar71xx-generic-gl-ar750-squashfs-sysupgrade.bin"

if [ ! -f "$(dirname "$0")/lib/verify_download.sh" ]; then
    echo "ERROR: ./lib/verify_download.sh not found next to this script." >&2
    echo "Refusing to flash an unverified firmware image." >&2
    exit 1
fi

. "$(dirname "$0")/lib/verify_download.sh"

cd /tmp || exit 1

# Downloads over HTTPS and verifies against the pinned digest. On any failure
# this returns non-zero and removes the partial file.
verify_download "$FIRMWARE_URL" "$FIRMWARE_FILE" "$FIRMWARE_SHA256" || {
    echo "ERROR: firmware image failed verification; not flashing." >&2
    exit 1
}

echo "[+] Firmware verified: $FIRMWARE_FILE"
echo "[+] Flashing..."
sysupgrade "$FIRMWARE_FILE"

# 19.07 branch
# wget https://downloads.openwrt.org/releases/19.07-SNAPSHOT/targets/ar71xx/generic/openwrt-19.07-snapshot-r11217-b21bea7b1b-ar71xx-generic-gl-ar750-squashfs-sysupgrade.bin && sysupgrade /tmp/openwrt-19.07-snapshot-r11217-b21bea7b1b-ar71xx-generic-gl-ar750-squashfs-sysupgrade.bin