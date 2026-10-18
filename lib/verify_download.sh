#!/bin/sh
################################################################
# Fail-closed download helper shared by the installer scripts.
#
# Source it, do not execute it:
#     . "$(dirname "$0")/lib/verify_download.sh"
#
# The installers in this repository fetch an archive, an installer script or a
# firmware image and then execute it, normally as root. verify_download()
# refuses to proceed unless the URL is HTTPS *and* the caller has pinned the
# artifact's SHA-256, so a network attacker, a compromised mirror or a typo in
# a URL cannot turn into code execution.
#
# The expected digest is passed in rather than hardcoded so each caller can
# source it from a variable near the top of its own script. Until someone
# pins the real digest, pass the literal UNPINNED and the call fails closed.
#
# Requires: sha256sum (coreutils or busybox), and curl or wget.
################################################################

UNPINNED="UNPINNED"

# verify_download <url> <output-path> <expected-sha256>
#
# Returns 0 on a verified download, non-zero otherwise. On any failure the
# partial file is removed so a later step cannot pick it up.
verify_download() {
    _vd_url="$1"
    _vd_out="$2"
    _vd_want="$3"

    if [ -z "$_vd_url" ] || [ -z "$_vd_out" ]; then
        echo "verify_download: usage: verify_download <url> <outfile> <sha256>" >&2
        return 2
    fi

    # Refuse plaintext outright. Integrity checking is only meaningful if the
    # digest came from a source independent of the transfer.
    case "$_vd_url" in
        https://*) ;;
        *)
            echo "verify_download: refusing non-HTTPS URL: $_vd_url" >&2
            return 2
            ;;
    esac

    # Fail closed on an unpinned digest rather than trusting the download.
    if [ -z "$_vd_want" ] || [ "$_vd_want" = "$UNPINNED" ]; then
        echo "verify_download: refusing $_vd_url: no pinned SHA-256." >&2
        echo "  Pin the artifact's real digest before running this script." >&2
        return 2
    fi

    if [ ! -x "$(command -v sha256sum 2>/dev/null)" ]; then
        echo "verify_download: sha256sum not found; cannot verify $_vd_url" >&2
        return 2
    fi

    if command -v curl >/dev/null 2>&1; then
        curl -fsSL --proto '=https' --tlsv1.2 -o "$_vd_out" "$_vd_url" || {
            echo "verify_download: download failed: $_vd_url" >&2
            rm -f "$_vd_out"
            return 1
        }
    elif command -v wget >/dev/null 2>&1; then
        wget -q -O "$_vd_out" "$_vd_url" || {
            echo "verify_download: download failed: $_vd_url" >&2
            rm -f "$_vd_out"
            return 1
        }
    else
        echo "verify_download: neither curl nor wget available" >&2
        return 2
    fi

    if ! printf '%s  %s\n' "$_vd_want" "$_vd_out" | sha256sum -c - >/dev/null 2>&1; then
        echo "verify_download: CHECKSUM MISMATCH for $_vd_out" >&2
        echo "  expected: $_vd_want" >&2
        echo "  actual:   $(sha256sum "$_vd_out" 2>/dev/null | cut -d' ' -f1)" >&2
        rm -f "$_vd_out"
        return 1
    fi

    return 0
}