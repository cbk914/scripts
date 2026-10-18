"""Tests for lib/verify_download.sh, the fail-closed shell download helper.

The installers that source this helper download an archive or a firmware image
and then execute it, normally as root. Two of them used plaintext HTTP:

    fuzzing_suricata_install.sh:39  wget http://lcamtuf.coredump.cx/afl/...
    fuzzing_suricata_install.sh:101 wget http://lcamtuf.coredump.cx/afl/...
    upgrade_firmware.sh:4           wget http://downloads.openwrt.org/...

and install_tools_ARM.sh:14 piped a remote script straight into bash:

    curl https://getcroc.schollz.com | bash

These tests exercise the helper under a real POSIX shell. The refusal tests
need no network and no download. The end-to-end test serves a file from a
local HTTPS server; nothing external is contacted.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HELPER = REPO_ROOT / "lib" / "verify_download.sh"


def _find_bash():
    """Locate a bash that actually runs here.

    Windows may resolve `bash` to the WSL launcher, which is not usable from
    this context, so prefer the Git-for-Windows shell when present.
    """
    candidates = [
        os.environ.get("TEST_BASH"),
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
        shutil.which("bash"),
        shutil.which("sh"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            probe = subprocess.run(
                [candidate, "-c", "exit 0"], capture_output=True, timeout=30
            )
        except (OSError, subprocess.SubprocessError):
            continue
        if probe.returncode == 0:
            return candidate
    return None


BASH = _find_bash()

pytestmark = pytest.mark.skipif(BASH is None, reason="no usable POSIX shell available")


def run_helper(tmp_path, body, path_prepend=None, env=None):
    """Source the helper in a fresh shell and run `body`.

    `path_prepend` puts a directory at the front of PATH *inside* the shell,
    using cygpath to convert it. That is how the wget stub below is injected.
    """
    lines = [f'. "{HELPER}"']
    if path_prepend is not None:
        lines.append(f'export PATH="$(cygpath -u \'{path_prepend}\'):$PATH"')
    lines.append(body)

    script = tmp_path / "drive.sh"
    script.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    environment = dict(os.environ)
    environment.update(env or {})
    environment["MSYS_NO_PATHCONV"] = "1"

    return subprocess.run(
        [BASH, str(script)], capture_output=True, text=True, timeout=120, env=environment
    )


# --------------------------------------------------------------------------
# Refusals: no network required
# --------------------------------------------------------------------------

def test_refuses_plaintext_http(tmp_path):
    result = run_helper(
        tmp_path,
        'verify_download "http://example.com/x.tgz" "$PWD/x.tgz" ' + '"' + "a" * 64 + '"',
    )

    assert result.returncode == 2
    assert "refusing non-HTTPS" in result.stderr


def test_refuses_unpinned_digest(tmp_path):
    result = run_helper(
        tmp_path,
        'verify_download "https://example.com/x.tgz" "$PWD/x.tgz" "$UNPINNED"',
    )

    assert result.returncode == 2
    assert "no pinned SHA-256" in result.stderr


def test_refuses_empty_digest(tmp_path):
    result = run_helper(
        tmp_path, 'verify_download "https://example.com/x.tgz" "$PWD/x.tgz" ""'
    )

    assert result.returncode == 2
    assert "no pinned SHA-256" in result.stderr


def test_unpinned_download_never_creates_the_file(tmp_path):
    """The refusal must happen before anything is written."""
    target = tmp_path / "should-not-exist.tgz"
    result = run_helper(
        tmp_path,
        f'verify_download "https://example.com/x.tgz" "{target}" "$UNPINNED"',
    )

    assert result.returncode == 2
    assert not target.exists()


def test_no_curl_or_bash_pipe_remains_in_installers():
    """No installer may pipe a download straight into a shell."""
    offenders = []
    for script in REPO_ROOT.glob("*.sh"):
        for lineno, line in enumerate(
            script.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "curl" in stripped and ("| bash" in stripped or "|sh" in stripped.replace(" ", "")):
                offenders.append(f"{script.name}:{lineno}: {stripped}")

    assert offenders == [], "curl|bash remains: " + "; ".join(offenders)


def test_no_plaintext_http_download_remains():
    """No installer may fetch an artifact over plaintext HTTP."""
    offenders = []
    for script in REPO_ROOT.glob("*.sh"):
        text = script.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if ("wget " in stripped or "curl " in stripped) and "http://" in stripped:
                offenders.append(f"{script.name}:{lineno}: {stripped}")

    assert offenders == [], "plaintext HTTP download remains: " + "; ".join(offenders)


# --------------------------------------------------------------------------
# Verification logic, exercised through a wget stub
# --------------------------------------------------------------------------
#
# A real end-to-end HTTPS download cannot be tested on this host: the curl that
# ships with Git for Windows is built against schannel, which validates against
# the Windows certificate store and ignores CURL_CA_BUNDLE/SSL_CERT_FILE, so a
# throwaway self-signed certificate cannot be trusted without modifying the
# machine's trust store.
#
# Instead the helper's *download* step is satisfied by a stub `wget` placed
# first on PATH. The helper itself is unmodified and still enforces HTTPS-only
# URLs; the stub simply hands it local bytes, after which the real
# sha256sum -c verification and the real failure cleanup both run.

WGET_STUB = """#!/bin/sh
# Minimal wget stand-in for tests: `wget -q -O <outfile> <url>`.
# Copies PRETEND_CONTENT_FILE to the requested output path.
cp "$PRETEND_CONTENT_FILE" "$2"
exit 0
"""

CURL_STUB = """#!/bin/sh
# Minimal curl stand-in for tests. Honours `-o <outfile>` and copies
# PRETEND_CONTENT_FILE there. No network access is performed.
out=""
prev=""
for a in "$@"; do
  if [ "$prev" = "-o" ]; then out="$a"; fi
  prev="$a"
done
if [ -n "$out" ]; then cp "$PRETEND_CONTENT_FILE" "$out"; fi
exit 0
"""


@pytest.fixture
def wget_stub(tmp_path):
    """Stubs for curl and wget that serve local bytes.

    The helper prefers curl when it is on PATH, so both are stubbed. This
    keeps the helper itself unmodified while letting its real verification
    and cleanup logic run.
    """
    bindir = tmp_path / "stubbin"
    bindir.mkdir()

    for name, body in (("wget", WGET_STUB), ("curl", CURL_STUB)):
        stub = bindir / name
        stub.write_text(body, encoding="utf-8", newline="\n")
        stub.chmod(0o755)

    return bindir


def _sha256(data):
    import hashlib

    return hashlib.sha256(data).hexdigest()


def test_correct_digest_download_is_accepted(wget_stub, tmp_path):
    """A matching SHA-256 must let the download through untouched."""
    payload = b"a fake release tarball\n"
    served = tmp_path / "served.bin"
    served.write_bytes(payload)
    target = tmp_path / "good.tgz"

    result = run_helper(
        tmp_path,
        f'verify_download "https://example.invalid/x.tgz" "{target}" "{_sha256(payload)}"',
        path_prepend=wget_stub,
        env={"PRETEND_CONTENT_FILE": str(served)},
    )

    assert result.returncode == 0, result.stderr
    assert target.exists()
    assert target.read_bytes() == payload


def test_wrong_digest_is_rejected_and_file_removed(wget_stub, tmp_path):
    """A tampered or substituted download must not survive verification."""
    payload = b"attacker substituted content\n"
    served = tmp_path / "served.bin"
    served.write_bytes(payload)
    target = tmp_path / "bad.tgz"

    result = run_helper(
        tmp_path,
        f'verify_download "https://example.invalid/x.tgz" "{target}" ' + '"' + "b" * 64 + '"',
        path_prepend=wget_stub,
        env={"PRETEND_CONTENT_FILE": str(served)},
    )

    assert result.returncode == 1
    assert "CHECKSUM MISMATCH" in result.stderr
    assert not target.exists(), "a rejected download must not be left on disk"


def test_plaintext_http_is_refused_even_with_a_valid_digest(wget_stub, tmp_path):
    """HTTPS enforcement must hold independently of the checksum."""
    payload = b"content\n"
    served = tmp_path / "served.bin"
    served.write_bytes(payload)
    target = tmp_path / "plain.tgz"

    result = run_helper(
        tmp_path,
        f'verify_download "http://example.invalid/x.tgz" "{target}" "{_sha256(payload)}"',
        path_prepend=wget_stub,
        env={"PRETEND_CONTENT_FILE": str(served)},
    )

    assert result.returncode == 2
    assert "refusing non-HTTPS" in result.stderr
    assert not target.exists()


def test_unpinned_is_refused_even_when_bytes_are_available(wget_stub, tmp_path):
    """An unpinned digest must fail closed before any fetch happens."""
    payload = b"content\n"
    served = tmp_path / "served.bin"
    served.write_bytes(payload)
    target = tmp_path / "unpinned.tgz"

    result = run_helper(
        tmp_path,
        f'verify_download "https://example.invalid/x.tgz" "{target}" "$UNPINNED"',
        path_prepend=wget_stub,
        env={"PRETEND_CONTENT_FILE": str(served)},
    )

    assert result.returncode == 2
    assert not target.exists()