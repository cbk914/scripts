#!/usr/bin/env python3
"""Verify a downloaded artifact against a pinned digest.

Several installers in this repository fetch a tarball, firmware image or
installer over the network and then execute it, often as root. Downloading
over plaintext HTTP with no integrity check means whoever is on the path can
substitute the artifact and get code execution. Fetching over TLS with no
integrity check leaves a compromised or mistaken mirror equally trusted.

This helper closes that gap in one place. It is dependency-free so it can be
used from a minimal box, and it is importable so the behaviour is unit
testable:

    python3 verify_checksum.py ./afl-latest.tgz --sha256 <hex>
    python3 verify_checksum.py ./firmware.bin --expect-env FIRMWARE_SHA256

Exit codes: 0 match, 1 mismatch or unreadable file, 2 usage or unpinned digest.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import os
import sys
from pathlib import Path

CHUNK_SIZE = 1 << 20

EXIT_OK = 0
EXIT_MISMATCH = 1
EXIT_USAGE = 2

# Placeholder that means "nobody has pinned this yet". It is treated as
# unpinned rather than as a real digest so the scripts fail closed instead of
# silently trusting whatever arrived.
UNPINNED = "UNPINNED"


class ChecksumError(Exception):
    """Raised when a digest cannot be used or a file cannot be read."""


def normalize_digest(expected):
    """Return a lowercase hex digest, or raise ChecksumError.

    Accepts values copied straight out of `sha256sum` output, so a leading
    algorithm tag, surrounding whitespace and a trailing filename marker are
    all tolerated.
    """
    if expected is None:
        raise ChecksumError("no digest supplied")

    candidate = str(expected).strip().lower()
    if not candidate:
        raise ChecksumError("empty digest")

    # Drop a leading "sha256:" or "sha256-" style tag.
    if ":" in candidate:
        candidate = candidate.split(":", 1)[1]
    if candidate.startswith("sha256-"):
        candidate = candidate[len("sha256-"):]

    # A pasted `sha256sum` line may still carry the filename after two spaces.
    candidate = candidate.split()[0] if candidate.split() else ""

    if candidate in ("", UNPINNED):
        raise ChecksumError(
            "digest is unpinned; fetch a trusted copy of the artifact and pin "
            "its real SHA-256 before installing anything"
        )

    if len(candidate) != 64:
        raise ChecksumError(
            f"expected a 64-character SHA-256 hex digest, got {len(candidate)}: {candidate!r}"
        )

    try:
        int(candidate, 16)
    except ValueError:
        raise ChecksumError(f"digest is not valid hex: {candidate!r}") from None

    return candidate


def sha256_file(path, chunk_size=CHUNK_SIZE):
    """Return the lowercase SHA-256 hex digest of the file at `path`."""
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(chunk_size), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ChecksumError(f"cannot read {path}: {exc}") from exc
    return digest.hexdigest()


def verify_checksum(path, expected):
    """Return True if `path` hashes to `expected`, else False.

    Raises ChecksumError for an unusable digest or unreadable file so the
    caller is forced to distinguish "wrong" from "cannot tell".
    """
    wanted = normalize_digest(expected)
    actual = sha256_file(path)
    # Constant-time compare; digests are public, but there is no reason to
    # leak a comparison-early exit path.
    return hmac.compare_digest(actual, wanted)


def verify_from_env(path, variable, environ=None):
    """Verify `path` against the digest held in environment `variable`."""
    env = os.environ if environ is None else environ
    if variable not in env:
        raise ChecksumError(
            f"{variable} is not set; refusing to use an unverified download"
        )
    return verify_checksum(path, env[variable])


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Verify a file against a pinned SHA-256 digest."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--sha256", help="expected SHA-256 hex digest")
    group.add_argument(
        "--expect-env",
        metavar="VARNAME",
        help="read the expected digest from this environment variable",
    )
    parser.add_argument("file", help="path to the downloaded file")
    args = parser.parse_args(argv)

    try:
        if args.sha256:
            ok = verify_checksum(args.file, args.sha256)
        else:
            ok = verify_from_env(args.file, args.expect_env)
    except ChecksumError as exc:
        print(f"verify_checksum: {exc}", file=sys.stderr)
        return EXIT_USAGE

    if ok:
        print(f"OK: {args.file} matches the pinned SHA-256")
        return EXIT_OK

    try:
        actual = sha256_file(args.file)
    except ChecksumError:
        actual = "<unreadable>"
    print(
        f"verify_checksum: CHECKSUM MISMATCH for {args.file}\n"
        f"  expected: {normalize_digest(args.sha256) if args.sha256 else os.environ.get(args.expect_env, '?')}\n"
        f"  actual:   {actual}\n"
        f"Refusing to use this file.",
        file=sys.stderr,
    )
    return EXIT_MISMATCH


if __name__ == "__main__":
    sys.exit(main())