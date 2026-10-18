"""Regression tests for the command injection in checkversions.py.

Original code (checkversions.py:55-58):

    nmap_cmd  = "nmap -sV --min-rate=5000 -Pn -vvv -script=vulners " + url
    if args.output:
        nmap_cmd += f" -oX {args.output}"
    output = subprocess.run(nmap_cmd, shell=True, check=True)

With shell=True the assembled line is parsed by the system shell. Note where
the injection actually is:

  * `-t/--target` is incidentally safe. The regex at checkversions.py:17 uses a
    capture group of `[a-zA-Z0-9-.]+`, so `url` can only ever be those
    characters. It validates host *format*, not shell metacharacters, but in
    this particular case the allowlist is strict enough to exclude them.
  * `-o/--output` was interpolated with NO validation whatsoever. It was the
    live injection vector:
        checkversions.py -t http://example.com -o "out.xml & <command>"

Both are now moot: the command is an argv list run with shell=False, so every
value is exactly one argument and nothing is ever parsed as shell syntax.

These tests are careful never to run a real scan. `nmap` is installed on some
machines, so a stub `nmap` that exits non-zero is placed first on PATH. The
only thing that ever really executes is the harmless sentinel payload.
"""

import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "checkversions.py"


class _FakeResponse:
    status_code = 200
    headers = {"Server": "nginx/1.2.3"}
    text = ""


# A harmless stand-in for nmap, used to replace the program name in the
# command the ORIGINAL code hands to the shell.
#
# Why this is needed: the original ran
#     subprocess.run("nmap -sV ... <target> -oX <output>", shell=True)
# so the command really is executed by the system shell. To demonstrate the
# injection honestly the test has to let that happen -- but it must never
# launch a real nmap against a real host.
#
# On Windows, CreateProcess only appends ".exe" to a bare program name, so a
# "nmap.cmd" stub on PATH is NOT picked up by subprocess with shell=False, and
# the real nmap.exe on PATH would run instead. Rewriting the program name in
# the command string sidesteps that entirely and is faithful to what is being
# tested: the shell still parses the whole line, and the payload after the
# command separator still runs.
_HARMLESS_PROGRAM = f'"{sys.executable}" -c "import sys; sys.exit(1)"'


@pytest.fixture
def stub_nmap(tmp_path, monkeypatch):
    """A harmless stand-in for nmap so no real scan can ever happen.

    The fixture is now belt-and-braces: the recorder below never executes a
    list argv at all, and any string argv that does get executed has its
    program name replaced by _HARMLESS_PROGRAM. The PATH stub remains for the
    case where the code under test resolves `nmap` itself.
    """
    bindir = tmp_path / "bin"
    bindir.mkdir()

    if os.name == "nt":
        stub = bindir / "nmap.cmd"
        stub.write_bytes(b"@echo off\r\nexit /b 1\r\n")
    else:
        stub = bindir / "nmap"
        stub.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        stub.chmod(0o755)

    monkeypatch.setenv("PATH", str(bindir) + os.pathsep + os.environ.get("PATH", ""))
    return stub


def _recording_run(monkeypatch, calls):
    """Install a subprocess.run wrapper that records and safely executes.

    A list argv is never executed -- that is the whole point of the fix, and
    it guarantees no scan is performed. A string argv (what the original
    passed to the shell) IS executed, but with the leading `nmap` replaced by
    a harmless program that exits non-zero, so the shell still parses the
    whole line (and the injected payload still runs) while no real scan and
    no external host are involved.
    """
    real_run = subprocess.run

    def wrapper(cmd, *args, **kwargs):
        calls.append({"cmd": cmd, "kwargs": kwargs})

        if isinstance(cmd, list):
            # Fixed code path: never execute, never scan anything.
            class _Result:
                returncode = 0
                stdout = ""
                stderr = ""

            return _Result()

        # Original code path: a string going to the shell. Swap the program.
        # A lambda replacement is used because the replacement text contains
        # backslashes (the Windows interpreter path) and re.sub would treat
        # those as escape sequences in a plain replacement string.
        rewritten = re.sub(r"^\s*nmap\b", lambda _m: _HARMLESS_PROGRAM, cmd, count=1)
        kwargs = dict(kwargs)
        kwargs.pop("check", None)
        return real_run(rewritten, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", wrapper)
    return wrapper


def _exec_script(monkeypatch, argv, calls=None):
    """Run checkversions.py with `argv`, with the HTTP probe stubbed out."""
    if calls is None:
        calls = []

    monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse())
    monkeypatch.setattr(sys, "argv", ["checkversions.py"] + argv)

    spec = importlib.util.spec_from_file_location("checkversions_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except SystemExit:
        # argparse errors and the explicit sys.exit(1) paths are all fine here.
        pass
    except subprocess.CalledProcessError:
        # The original used check=True; a failing nmap raised straight out.
        pass
    return module


def _payload_for(sentinel):
    """An -o value that would run a second command under the system shell.

    `&` is the command separator in both cmd.exe and POSIX sh.
    """
    return (
        'out.xml & python -c '
        "\"import pathlib; pathlib.Path(r'" + str(sentinel) + "').write_text('pwned')\""
    )


# --------------------------------------------------------------------------
# The injection itself
# --------------------------------------------------------------------------

def test_output_argument_cannot_inject(stub_nmap, tmp_path, monkeypatch):
    """The live injection vector: -o/--output reached a shell unvalidated."""
    sentinel = tmp_path / "pwned.txt"
    calls = []
    _recording_run(monkeypatch, calls)

    _exec_script(
        monkeypatch,
        ["-t", "http://example.com", "-o", _payload_for(sentinel)],
        calls=calls,
    )

    assert not sentinel.exists(), (
        "command injection via -o/--output: the payload executed and created " + str(sentinel)
    )


def test_target_argument_cannot_inject(stub_nmap, tmp_path, monkeypatch):
    """Belt and braces: even a hostile target must not execute."""
    sentinel = tmp_path / "pwned2.txt"
    hostile = "http://example.com & python -c \"import pathlib; pathlib.Path(r'" + str(sentinel) + "').write_text('x')\""
    calls = []
    _recording_run(monkeypatch, calls)

    _exec_script(
        monkeypatch,
        ["-t", hostile, "-o", "out.xml"],
        calls=calls,
    )

    assert not sentinel.exists()


def test_no_nmap_process_is_ever_launched(stub_nmap, tmp_path, monkeypatch):
    """Guard rail: the suite must never start a real scan.

    Windows CreateProcess only appends ".exe" to a bare program name, so a
    "nmap.cmd" on PATH is invisible to subprocess with shell=False and a real
    nmap.exe further down PATH would be launched instead. The recorder never
    executes a list argv, and rewrites the program name of any string argv, so
    no scan of any host can happen.
    """
    calls = []
    _recording_run(monkeypatch, calls)

    _exec_script(
        monkeypatch,
        ["-t", "http://example.com", "-o", "report.xml"],
        calls=calls,
    )

    assert calls, "subprocess.run should have been called"
    for call in calls:
        assert isinstance(call["cmd"], list), (
            "a string argv means the code under test asked for a shell"
        )


# --------------------------------------------------------------------------
# Structural proof: list form, shell=False
# --------------------------------------------------------------------------

def test_nmap_is_invoked_as_a_list_without_a_shell(stub_nmap, monkeypatch):
    """The subprocess call must receive a list and must not ask for a shell."""
    captured = {}

    def fake_run(cmd, *args, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs

        class R:
            returncode = 0
            stdout = ""
            stderr = ""

        return R()

    monkeypatch.setattr(subprocess, "run", fake_run)
    _exec_script(monkeypatch, ["-t", "http://example.com", "-o", "report.xml"])

    assert captured, "subprocess.run was never called"
    assert isinstance(captured["cmd"], list), (
        f"nmap was invoked with {type(captured['cmd']).__name__}, expected a list argv"
    )
    assert captured["cmd"][0] == "nmap"
    assert captured["cmd"][-2:] == ["-oX", "report.xml"]
    assert captured["kwargs"].get("shell") in (None, False), (
        "subprocess.run must not pass shell=True"
    )


def test_original_builds_a_shell_string():
    """AST proof that the original called subprocess.run(shell=True) on a string."""
    import ast

    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "run":
                for kw in node.keywords:
                    if kw.arg == "shell" and getattr(kw.value, "value", None) is True:
                        offenders.append(node.lineno)
    assert offenders == [], f"subprocess.run(shell=True) still present at {offenders}"


# --------------------------------------------------------------------------
# Output path validation
# --------------------------------------------------------------------------

def _load_definitions_only():
    """Exec only the module's imports, its constants, and its defs.

    checkversions.py is a script: importing it parses argv and talks to the
    network. To unit test validate_output_path() in isolation, rebuild a module
    namespace from the AST, keeping the nodes that only *define* things and
    dropping the module-level statements that do work.

    The constants that survive are allow-listed by name. `args = parser
    .parse_args()` and `url = re.search(...)` are dropped because they depend
    on real command-line input; `parser` and `_UNSAFE_FILENAME_CHARS` are kept
    because validate_output_path() resolves them at call time.
    """
    import ast
    import types

    keep_names = {"parser", "_UNSAFE_FILENAME_CHARS"}

    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    body = []

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef)):
            body.append(node)
        elif isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if any(name in keep_names for name in targets):
                body.append(node)

    module = types.ModuleType("checkversions_defs")
    exec(compile(ast.Module(body=body, type_ignores=[]), str(SCRIPT), "exec"), module.__dict__)
    return module


@pytest.mark.parametrize(
    "bad",
    [
        "out.xml; whoami",
        "out.xml & whoami",
        "out.xml | whoami",
        "out`whoami`.xml",
        "out$(whoami).xml",
        "out*.xml",
        "out>log",
        "",
        "   ",
    ],
)
def test_validator_rejects_dangerous_output_names(bad):
    module = _load_definitions_only()
    with pytest.raises(SystemExit) as excinfo:
        module.validate_output_path(bad)
    assert excinfo.value.code == 2, "argparse must reject the name with exit code 2"


def test_validator_accepts_ordinary_names():
    module = _load_definitions_only()
    assert module.validate_output_path("report.xml") == "report.xml"
    assert module.validate_output_path("out/report-1.2.xml") == "out/report-1.2.xml"
    assert module.validate_output_path("C:\\tmp\\scan.xml") == "C:\\tmp\\scan.xml"