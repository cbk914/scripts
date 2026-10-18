"""Tests for verify_checksum.py, the download integrity helper.

Every installer in this repository that fetches an artifact and executes it did
so with no integrity check at all, and two of them did it over plaintext HTTP.
verify_checksum() is the single place that decides whether a download is
trustworthy, so it needs to fail closed on the ambiguous cases rather than
guessing.
"""

import hashlib
import importlib.util
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "verify_checksum", REPO_ROOT / "verify_checksum.py"
)
verify_checksum = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify_checksum)

PAYLOAD = b"pretend this is an AFL release tarball\n"


@pytest.fixture
def artifact(tmp_path):
    path = tmp_path / "artifact.bin"
    path.write_bytes(PAYLOAD)
    return path


def digest_of(path):
    return hashlib.sha256(PAYLOAD).hexdigest()


# --------------------------------------------------------------------------
# Happy path
# --------------------------------------------------------------------------

def test_sha256_file_matches_hashlib(artifact):
    assert verify_checksum.sha256_file(artifact) == digest_of(artifact)


def test_verify_accepts_correct_digest(artifact):
    assert verify_checksum.verify_checksum(artifact, digest_of(artifact)) is True


def test_verify_rejects_wrong_digest(artifact):
    wrong = "0" * 64
    assert verify_checksum.verify_checksum(artifact, wrong) is False


def test_verify_detects_single_bit_change(artifact):
    good = digest_of(artifact)
    flipped = ("0" if good[0] != "0" else "1") + good[1:]
    assert verify_checksum.verify_checksum(artifact, flipped) is False


def test_chunked_read_matches_single_shot(tmp_path):
    """A file spanning several chunks must hash identically."""
    big = tmp_path / "big.bin"
    data = os.urandom(3 * (1 << 20))  # 3 MiB, crosses the 1 MiB chunk size
    big.write_bytes(data)

    assert verify_checksum.sha256_file(big) == hashlib.sha256(data).hexdigest()


# --------------------------------------------------------------------------
# Fail-closed behaviour on ambiguous digests
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "junk", [None, "", "   ", "UNPINNED", "unpinned", "not-a-digest", "z" * 64, "abc"]
)
def test_unusable_digests_raise(artifact, junk):
    with pytest.raises(verify_checksum.ChecksumError):
        verify_checksum.verify_checksum(artifact, junk)


def test_unpinned_is_never_treated_as_a_pass(artifact):
    """The UNPINNED placeholder must raise, never quietly return False."""
    with pytest.raises(verify_checksum.ChecksumError):
        verify_checksum.verify_checksum(artifact, "UNPINNED")


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("  " + "a" * 64 + "  ", "a" * 64),
        ("sha256:" + "a" * 64, "a" * 64),
        ("sha256-" + "a" * 64, "a" * 64),
        ("SHA256:" + "A" * 64, "a" * 64),
    ],
)
def test_digest_normalisation_accepts_pasted_sha256sum_output(raw, expected):
    assert verify_checksum.normalize_digest(raw) == expected


def test_digest_strips_trailing_filename():
    """A digest pasted from `sha256sum file` output still works."""
    pasted = digest_of(None) + "  afl-latest.tgz"
    assert verify_checksum.normalize_digest(pasted) == digest_of(None)


def test_unreadable_file_raises_not_returns_false(artifact):
    with pytest.raises(verify_checksum.ChecksumError):
        verify_checksum.sha256_file(artifact.parent / "does-not-exist")


# --------------------------------------------------------------------------
# Environment-variable driven verification
# --------------------------------------------------------------------------

def test_verify_from_env_matches(artifact):
    env = {"PINNED_SHA256": digest_of(artifact)}
    assert verify_checksum.verify_from_env(artifact, "PINNED_SHA256", environ=env) is True


def test_verify_from_env_requires_the_variable(artifact):
    with pytest.raises(verify_checksum.ChecksumError) as excinfo:
        verify_checksum.verify_from_env(artifact, "PINNED_SHA256", environ={})
    assert "refusing" in str(excinfo.value).lower()


# --------------------------------------------------------------------------
# CLI contract
# --------------------------------------------------------------------------

def test_cli_success_returns_zero(artifact, capsys):
    code = verify_checksum.main([str(artifact), "--sha256", digest_of(artifact)])
    assert code == verify_checksum.EXIT_OK
    assert "matches the pinned SHA-256" in capsys.readouterr().out


def test_cli_mismatch_returns_one_and_says_refusing(artifact, capsys):
    code = verify_checksum.main([str(artifact), "--sha256", "0" * 64])
    captured = capsys.readouterr()
    assert code == verify_checksum.EXIT_MISMATCH
    assert "MISMATCH" in captured.err
    assert "Refusing to use this file" in captured.err


def test_cli_unpinned_returns_usage_error(artifact, capsys):
    code = verify_checksum.main([str(artifact), "--sha256", "UNPINNED"])
    assert code == verify_checksum.EXIT_USAGE
    assert "unpinned" in capsys.readouterr().err.lower()


def test_cli_unpinned_leaves_no_approval(artifact, capsys):
    """An unpinned digest must be a hard failure, not a warning."""
    assert verify_checksum.main([str(artifact), "--sha256", "UNPINNED"]) != verify_checksum.EXIT_OK