#!/usr/bin/env python3

"""
TLS Renegotiation Assessment Tool

Checks:

1. OpenSSL availability/version.
2. TLS 1.0 / 1.1 / 1.2 / 1.3 protocol support.
3. RFC 5746 secure renegotiation support.
4. Client-initiated TLS renegotiation.
5. Repeated client-initiated renegotiation on the same connection.
6. Legacy/insecure renegotiation compatibility.
7. TLS 1.3 applicability.
8. Generates a concise security assessment.

Important distinctions:

- "Secure Renegotiation IS supported"
    Means RFC 5746 secure renegotiation is supported.
    It DOES NOT mean renegotiation is disabled.

- Successful "R" renegotiation
    Means the server allows client-initiated renegotiation.

- Successful repeated "R" renegotiations
    Means one client can repeatedly trigger TLS handshakes on the same
    connection. This can represent a resource-exhaustion attack surface,
    but DOES NOT by itself prove denial of service.

- TLS 1.3
    Does not support TLS renegotiation. Post-handshake authentication and
    KeyUpdate are different mechanisms.

Requires:
    Python 3.8+
    OpenSSL CLI

Examples:

    python3 tls_reneg_check.py -t example.com:443

    python3 tls_reneg_check.py \
        -t example.com:443 \
        --repeat 5 \
        --delay 1.5

    python3 tls_reneg_check.py \
        -t example.com:443 \
        --repeat 5 \
        --save-dir evidence/tls-reneg \
        --verbose
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


PROTOCOLS = {
    "TLS 1.0": {
        "flag": "-tls1",
        "openssl_name": "TLSv1",
    },
    "TLS 1.1": {
        "flag": "-tls1_1",
        "openssl_name": "TLSv1.1",
    },
    "TLS 1.2": {
        "flag": "-tls1_2",
        "openssl_name": "TLSv1.2",
    },
    "TLS 1.3": {
        "flag": "-tls1_3",
        "openssl_name": "TLSv1.3",
    },
}


@dataclass
class CommandResult:
    command: List[str]
    output: str
    returncode: Optional[int]
    timed_out: bool
    elapsed: float


@dataclass
class ProtocolResult:
    name: str
    supported: Optional[bool]
    negotiated_protocol: Optional[str]
    result: CommandResult
    note: str = ""


@dataclass
class RenegotiationResult:
    requested: int
    markers: int
    successful: int
    output: str
    result: CommandResult


def parse_target(target: str) -> Tuple[str, int]:
    """
    Parse:
        hostname
        hostname:443
        [2001:db8::1]:443
    """

    target = target.strip()

    if not target:
        raise ValueError("Target cannot be empty")

    if target.startswith("["):
        match = re.match(r"^\[(.+)](?::(\d+))?$", target)

        if not match:
            raise ValueError(
                "Invalid IPv6 target. Expected format: [IPv6]:port"
            )

        host = match.group(1)
        port = int(match.group(2) or 443)

    elif target.count(":") == 1:
        host, port_text = target.rsplit(":", 1)

        if not port_text.isdigit():
            raise ValueError(
                "Invalid port. Expected target in host:port format."
            )

        port = int(port_text)

    elif ":" not in target:
        host = target
        port = 443

    else:
        raise ValueError(
            "IPv6 targets must use bracket notation, e.g. "
            "[2001:db8::1]:443"
        )

    if not host:
        raise ValueError("Hostname cannot be empty")

    if port < 1 or port > 65535:
        raise ValueError("Port must be between 1 and 65535")

    return host, port


def format_connect_target(host: str, port: int) -> str:
    """
    Format hostname/IP for openssl s_client -connect.
    """

    if ":" in host:
        return f"[{host}]:{port}"

    return f"{host}:{port}"


def sanitize_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def check_openssl() -> str:
    """
    Verify openssl exists and return its version.
    """

    executable = shutil.which("openssl")

    if not executable:
        print("[ERROR] openssl was not found in PATH.")
        print()
        print("Install OpenSSL and try again.")
        sys.exit(2)

    try:
        result = subprocess.run(
            ["openssl", "version", "-a"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=5,
            check=False,
        )

    except Exception as exc:
        print(f"[ERROR] Unable to execute openssl: {exc}")
        sys.exit(2)

    first_line = result.stdout.splitlines()[0] if result.stdout else "Unknown"

    return first_line.strip()


def run_s_client(
    connect_target: str,
    sni: Optional[str],
    protocol_flag: str,
    *,
    extra_args: Optional[List[str]] = None,
    renegotiations: int = 0,
    initial_delay: float = 1.0,
    delay: float = 1.0,
    timeout: float = 15.0,
) -> CommandResult:
    """
    Execute openssl s_client.

    If renegotiations > 0, writes interactive 'R' commands one by one
    with delays between them, then sends 'Q'.

    Temporary files are used for stdout/stderr so repeated certificate
    output cannot fill a subprocess pipe and deadlock the process.
    """

    cmd = [
        "openssl",
        "s_client",
        "-connect",
        connect_target,
    ]

    if sni:
        cmd.extend([
            "-servername",
            sni,
        ])

    cmd.extend([
        protocol_flag,
        "-state",
    ])

    if extra_args:
        cmd.extend(extra_args)

    start = time.monotonic()
    timed_out = False
    returncode: Optional[int] = None

    with tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as output_file:

        stdin_config = (
            subprocess.PIPE
            if renegotiations > 0
            else subprocess.DEVNULL
        )

        try:
            process = subprocess.Popen(
                cmd,
                stdin=stdin_config,
                stdout=output_file,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

        except Exception as exc:
            elapsed = time.monotonic() - start

            return CommandResult(
                command=cmd,
                output=f"Unable to execute command: {exc}",
                returncode=None,
                timed_out=False,
                elapsed=elapsed,
            )

        try:
            if renegotiations > 0 and process.stdin is not None:

                time.sleep(initial_delay)

                for _ in range(renegotiations):
                    if process.poll() is not None:
                        break

                    try:
                        process.stdin.write("R\n")
                        process.stdin.flush()

                    except (BrokenPipeError, OSError):
                        break

                    time.sleep(delay)

                if process.poll() is None:
                    try:
                        process.stdin.write("Q\n")
                        process.stdin.flush()

                    except (BrokenPipeError, OSError):
                        pass

                try:
                    process.stdin.close()
                except (BrokenPipeError, OSError):
                    pass

                process.stdin = None

            # Allow enough time for intentionally delayed renegotiations.
            total_timeout = (
                timeout
                + initial_delay
                + (renegotiations * delay)
                + 2.0
            )

            process.wait(timeout=total_timeout)

        except subprocess.TimeoutExpired:
            timed_out = True

            try:
                process.kill()
            except Exception:
                pass

            try:
                process.wait(timeout=2)
            except Exception:
                pass

        except KeyboardInterrupt:
            try:
                process.kill()
            except Exception:
                pass

            raise

        returncode = process.returncode

        output_file.flush()
        output_file.seek(0)
        output = output_file.read()

    elapsed = time.monotonic() - start

    return CommandResult(
        command=cmd,
        output=output,
        returncode=returncode,
        timed_out=timed_out,
        elapsed=elapsed,
    )


def extract_negotiated_protocol(output: str) -> Optional[str]:
    """
    Extract negotiated protocol from common OpenSSL output variants.
    """

    patterns = [
        r"New,\s+(TLSv1(?:\.[0-3])?)\s*,",
        r"Protocol\s*:\s*(TLSv1(?:\.[0-3])?)",
        r"Protocol version\s*:\s*(TLSv1(?:\.[0-3])?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, output, re.IGNORECASE)

        if match:
            return match.group(1)

    return None


def local_option_error(output: str) -> bool:
    lowered = output.lower()

    indicators = [
        "unknown option",
        "unrecognized option",
        "use -help for summary",
        "unknown cipher",
    ]

    return any(indicator in lowered for indicator in indicators)


def protocol_failure_reason(output: str) -> str:
    lowered = output.lower()

    if "unsafe legacy renegotiation disabled" in lowered:
        return "OpenSSL blocked unsafe legacy renegotiation"

    if "protocol version" in lowered:
        return "Protocol rejected"

    if "handshake failure" in lowered:
        return "TLS handshake rejected"

    if "no protocols available" in lowered:
        return "Protocol unavailable in local OpenSSL"

    if "no ciphers available" in lowered:
        return "No compatible local cipher suites"

    if "unsupported protocol" in lowered:
        return "Protocol unsupported"

    if "connection refused" in lowered:
        return "Connection refused"

    if "connect:errno" in lowered:
        return "Connection error"

    return "Handshake did not complete"


def test_protocol(
    connect_target: str,
    sni: Optional[str],
    protocol_name: str,
    timeout: float,
) -> ProtocolResult:

    config = PROTOCOLS[protocol_name]

    result = run_s_client(
        connect_target,
        sni,
        config["flag"],
        timeout=timeout,
    )

    if result.timed_out:
        return ProtocolResult(
            name=protocol_name,
            supported=None,
            negotiated_protocol=None,
            result=result,
            note="Timed out",
        )

    if local_option_error(result.output):
        return ProtocolResult(
            name=protocol_name,
            supported=None,
            negotiated_protocol=None,
            result=result,
            note="Local OpenSSL does not support this test option",
        )

    negotiated = extract_negotiated_protocol(result.output)

    if negotiated == config["openssl_name"]:
        return ProtocolResult(
            name=protocol_name,
            supported=True,
            negotiated_protocol=negotiated,
            result=result,
        )

    return ProtocolResult(
        name=protocol_name,
        supported=False,
        negotiated_protocol=negotiated,
        result=result,
        note=protocol_failure_reason(result.output),
    )


def parse_secure_renegotiation(output: str) -> Optional[bool]:
    if "Secure Renegotiation IS supported" in output:
        return True

    if "Secure Renegotiation IS NOT supported" in output:
        return False

    return None


def count_renegotiation_markers(output: str) -> int:
    return len(
        re.findall(
            r"(?m)^RENEGOTIATING\s*$",
            output,
        )
    )


def count_successful_renegotiations(output: str) -> int:
    """
    Count successful renegotiations conservatively.

    Each successful renegotiation must have:

        RENEGOTIATING
        ...
        SSLv3/TLS read finished

    We split output into individual renegotiation sections.
    """

    parts = re.split(
        r"(?m)^RENEGOTIATING\s*$",
        output,
    )

    if len(parts) <= 1:
        return 0

    successful = 0

    for section in parts[1:]:

        success_indicators = [
            "SSL_connect:SSLv3/TLS read finished",
            "SSL_connect:SSL negotiation finished successfully",
        ]

        failure_indicators = [
            "no renegotiation",
            "renegotiation not allowed",
            "handshake failure",
            "alert handshake failure",
        ]

        has_success = any(
            indicator in section
            for indicator in success_indicators
        )

        has_failure = any(
            indicator.lower() in section.lower()
            for indicator in failure_indicators
        )

        if has_success and not has_failure:
            successful += 1

    return successful


def test_renegotiation(
    connect_target: str,
    sni: Optional[str],
    protocol_flag: str,
    *,
    repetitions: int,
    initial_delay: float,
    delay: float,
    timeout: float,
    extra_args: Optional[List[str]] = None,
) -> RenegotiationResult:

    result = run_s_client(
        connect_target,
        sni,
        protocol_flag,
        extra_args=extra_args,
        renegotiations=repetitions,
        initial_delay=initial_delay,
        delay=delay,
        timeout=timeout,
    )

    markers = count_renegotiation_markers(result.output)
    successful = count_successful_renegotiations(result.output)

    return RenegotiationResult(
        requested=repetitions,
        markers=markers,
        successful=successful,
        output=result.output,
        result=result,
    )


def save_evidence(
    save_dir: Path,
    filename: str,
    content: str,
) -> None:

    save_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = save_dir / filename

    path.write_text(
        content,
        encoding="utf-8",
        errors="replace",
    )


def print_section(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def print_protocol_results(
    protocol_results: Dict[str, ProtocolResult],
) -> None:

    print_section("PROTOCOL SUPPORT")

    for protocol_name in PROTOCOLS:

        result = protocol_results[protocol_name]

        if result.supported is True:
            print(
                f"[OK]   {protocol_name:<8} supported "
                f"({result.negotiated_protocol})"
            )

        elif result.supported is False:
            print(
                f"[INFO] {protocol_name:<8} not negotiated "
                f"({result.note})"
            )

        else:
            print(
                f"[?]    {protocol_name:<8} inconclusive "
                f"({result.note})"
            )


def build_summary(
    *,
    target: str,
    openssl_version: str,
    protocol_results: Dict[str, ProtocolResult],
    reneg_protocol_name: Optional[str],
    secure_renegotiation: Optional[bool],
    single_result: Optional[RenegotiationResult],
    repeated_result: Optional[RenegotiationResult],
    legacy_result: Optional[RenegotiationResult],
    legacy_confirmed: Optional[bool],
) -> Tuple[List[str], int]:

    lines: List[str] = []

    lines.append("=" * 72)
    lines.append("FINAL TLS RENEGOTIATION ASSESSMENT")
    lines.append("=" * 72)
    lines.append("")
    lines.append(f"Target:               {target}")
    lines.append(f"OpenSSL:              {openssl_version}")
    lines.append("")

    lines.append("Protocol support:")

    for name in PROTOCOLS:
        protocol = protocol_results[name]

        if protocol.supported is True:
            value = "SUPPORTED"

        elif protocol.supported is False:
            value = "NOT SUPPORTED"

        else:
            value = "INCONCLUSIVE"

        lines.append(
            f"  {name:<10} {value}"
        )

    lines.append("")

    if reneg_protocol_name:
        lines.append(
            f"Renegotiation tested:  {reneg_protocol_name}"
        )
    else:
        lines.append(
            "Renegotiation tested:  No TLS <= 1.2 protocol available"
        )

    if secure_renegotiation is True:
        lines.append(
            "RFC 5746 support:       YES - secure renegotiation negotiated"
        )

    elif secure_renegotiation is False:
        lines.append(
            "RFC 5746 support:       NO"
        )

    else:
        lines.append(
            "RFC 5746 support:       INCONCLUSIVE"
        )

    if single_result is not None:

        if single_result.successful >= 1:
            lines.append(
                "Client-initiated:      ENABLED"
            )
        else:
            lines.append(
                "Client-initiated:      NOT CONFIRMED"
            )

    else:
        lines.append(
            "Client-initiated:      NOT TESTED"
        )

    if repeated_result is not None:

        lines.append(
            "Repeated renegotiation: "
            f"{repeated_result.successful}/"
            f"{repeated_result.requested} successful"
        )

    else:
        lines.append(
            "Repeated renegotiation: NOT TESTED"
        )

    if legacy_confirmed is True:
        lines.append(
            "Legacy insecure mode:   CONFIRMED"
        )

    elif legacy_confirmed is False:
        lines.append(
            "Legacy insecure mode:   NOT CONFIRMED"
        )

    else:
        lines.append(
            "Legacy insecure mode:   NOT INDICATED / INCONCLUSIVE"
        )

    if protocol_results["TLS 1.3"].supported is True:
        lines.append(
            "TLS 1.3 renegotiation:  NOT APPLICABLE BY PROTOCOL DESIGN"
        )
    else:
        lines.append(
            "TLS 1.3 renegotiation:  NOT APPLICABLE"
        )

    lines.append("")
    lines.append("-" * 72)
    lines.append("SECURITY INTERPRETATION")
    lines.append("-" * 72)

    exit_code = 0

    if legacy_confirmed is True:

        lines.append(
            "[FAIL] Legacy/insecure TLS renegotiation appears to be accepted."
        )
        lines.append("")
        lines.append(
            "This is materially different from RFC 5746 secure "
            "renegotiation and should be investigated as a security issue."
        )

        exit_code = 1

    elif (
        repeated_result is not None
        and repeated_result.successful >= 2
    ):

        lines.append(
            "[WARN] Repeated client-initiated TLS renegotiation is enabled."
        )
        lines.append("")
        lines.append(
            "The server negotiated RFC 5746 secure renegotiation, so this "
            "is NOT evidence of CVE-2009-3555."
        )
        lines.append("")
        lines.append(
            "However, unauthenticated clients can repeatedly request "
            "computationally expensive TLS handshakes on an existing "
            "connection. This represents a potential resource-exhaustion "
            "attack surface."
        )
        lines.append("")
        lines.append(
            "This result alone DOES NOT demonstrate denial of service."
        )
        lines.append("")
        lines.append(
            "Suggested reporting classification: Low or Informational, "
            "unless availability impact is demonstrated separately."
        )

        exit_code = 1

    elif (
        single_result is not None
        and single_result.successful >= 1
    ):

        lines.append(
            "[WARN] Client-initiated TLS renegotiation is enabled."
        )
        lines.append("")
        lines.append(
            "RFC 5746 secure renegotiation is used if reported as "
            "supported, therefore this should not be described as "
            "insecure legacy renegotiation."
        )
        lines.append("")
        lines.append(
            "A potential resource-exhaustion attack surface exists, but "
            "repeated renegotiation or denial-of-service impact was not "
            "demonstrated."
        )

        exit_code = 1

    elif reneg_protocol_name:

        lines.append(
            "[OK] Client-initiated TLS renegotiation was not confirmed."
        )

        if secure_renegotiation is True:
            lines.append(
                "[OK] RFC 5746 secure renegotiation support was observed."
            )

    else:

        lines.append(
            "[OK] No protocol supporting traditional TLS renegotiation "
            "was successfully negotiated."
        )

    lines.append("")
    lines.append(
        "Note: server-initiated renegotiation cannot be generically forced "
        "by this client-side test. Application-specific behavior may be "
        "required to evaluate that scenario."
    )

    return lines, exit_code


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Comprehensive TLS renegotiation assessment using OpenSSL."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-t",
        "--target",
        required=True,
        help="Target as host:port. Port defaults to 443.",
    )

    parser.add_argument(
        "--sni",
        help=(
            "TLS SNI hostname. Defaults to the target hostname "
            "unless the target is an IP address."
        ),
    )

    parser.add_argument(
        "--repeat",
        type=int,
        default=5,
        help=(
            "Number of renegotiation attempts for the repeated "
            "renegotiation test."
        ),
    )

    parser.add_argument(
        "--initial-delay",
        type=float,
        default=1.0,
        help=(
            "Delay before sending the first OpenSSL R command."
        ),
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help=(
            "Delay between renegotiation requests."
        ),
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help=(
            "Base timeout for each OpenSSL operation."
        ),
    )

    parser.add_argument(
        "--save-dir",
        type=Path,
        help=(
            "Directory in which raw OpenSSL evidence and the summary "
            "will be saved."
        ),
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print raw OpenSSL output.",
    )

    args = parser.parse_args()

    if args.repeat < 2:
        parser.error("--repeat must be at least 2")

    if args.repeat > 50:
        parser.error(
            "--repeat is limited to 50. This tool is intended for "
            "validation, not load testing."
        )

    if args.delay < 0:
        parser.error("--delay cannot be negative")

    if args.initial_delay < 0:
        parser.error("--initial-delay cannot be negative")

    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")

    try:
        host, port = parse_target(args.target)

    except ValueError as exc:
        parser.error(str(exc))

    connect_target = format_connect_target(
        host,
        port,
    )

    # Use explicit --sni when supplied.
    #
    # Otherwise use the hostname when it looks like a DNS name.
    # Sending an IP as SNI is normally unnecessary.
    if args.sni:
        sni = args.sni

    elif re.fullmatch(
        r"\d{1,3}(?:\.\d{1,3}){3}",
        host,
    ):
        sni = None

    elif ":" in host:
        sni = None

    else:
        sni = host

    openssl_version = check_openssl()

    print("=" * 72)
    print("TLS RENEGOTIATION ASSESSMENT")
    print("=" * 72)
    print(f"Target:          {connect_target}")
    print(f"SNI:             {sni or '(none)'}")
    print(f"OpenSSL:         {openssl_version}")
    print(f"Repeat attempts: {args.repeat}")
    print(f"Delay:           {args.delay:.2f}s")

    #
    # 1. Protocol discovery
    #

    protocol_results: Dict[str, ProtocolResult] = {}

    print()
    print("[*] Testing TLS protocol support...")

    for protocol_name in PROTOCOLS:

        result = test_protocol(
            connect_target,
            sni,
            protocol_name,
            args.timeout,
        )

        protocol_results[protocol_name] = result

        if args.save_dir:
            filename = (
                "protocol_"
                + sanitize_filename(protocol_name.lower())
                + ".txt"
            )

            save_evidence(
                args.save_dir,
                filename,
                result.result.output,
            )

    print_protocol_results(
        protocol_results,
    )

    #
    # Select highest protocol <= TLS 1.2 that supports traditional
    # renegotiation.
    #

    reneg_protocol_name: Optional[str] = None

    for candidate in [
        "TLS 1.2",
        "TLS 1.1",
        "TLS 1.0",
    ]:
        if protocol_results[candidate].supported is True:
            reneg_protocol_name = candidate
            break

    secure_renegotiation: Optional[bool] = None
    single_result: Optional[RenegotiationResult] = None
    repeated_result: Optional[RenegotiationResult] = None
    legacy_result: Optional[RenegotiationResult] = None
    legacy_confirmed: Optional[bool] = None

    if reneg_protocol_name:

        config = PROTOCOLS[reneg_protocol_name]

        baseline_output = protocol_results[
            reneg_protocol_name
        ].result.output

        secure_renegotiation = parse_secure_renegotiation(
            baseline_output
        )

        print_section("RFC 5746 SECURE RENEGOTIATION")

        if secure_renegotiation is True:
            print(
                "[OK] Secure Renegotiation IS supported."
            )
            print(
                "     RFC 5746 protection is negotiated."
            )

        elif secure_renegotiation is False:
            print(
                "[WARN] Secure Renegotiation IS NOT supported."
            )
            print(
                "       Legacy/insecure renegotiation testing is required."
            )

        else:
            print(
                "[?] OpenSSL did not provide a definitive RFC 5746 result."
            )

        #
        # 2. Single client-initiated renegotiation
        #

        print_section("CLIENT-INITIATED RENEGOTIATION")

        print(
            f"[*] Sending one renegotiation request using "
            f"{reneg_protocol_name}..."
        )

        single_result = test_renegotiation(
            connect_target,
            sni,
            config["flag"],
            repetitions=1,
            initial_delay=args.initial_delay,
            delay=args.delay,
            timeout=args.timeout,
        )

        if single_result.successful >= 1:
            print(
                "[WARN] Client-initiated renegotiation ACCEPTED."
            )
            print(
                f"       Successful: "
                f"{single_result.successful}/1"
            )

        elif single_result.markers >= 1:
            print(
                "[OK] Client requested renegotiation, but the server "
                "did not complete it."
            )

        else:
            print(
                "[INFO] OpenSSL did not reach a renegotiation sequence."
            )

        if args.save_dir:
            save_evidence(
                args.save_dir,
                "client_initiated_single.txt",
                single_result.output,
            )

        if args.verbose:
            print()
            print("--- Raw single-renegotiation output ---")
            print(single_result.output.rstrip())

        #
        # 3. Repeated renegotiation
        #

        print_section("REPEATED CLIENT-INITIATED RENEGOTIATION")

        print(
            f"[*] Requesting {args.repeat} renegotiations on the same "
            "TLS connection..."
        )

        repeated_result = test_renegotiation(
            connect_target,
            sni,
            config["flag"],
            repetitions=args.repeat,
            initial_delay=args.initial_delay,
            delay=args.delay,
            timeout=args.timeout,
        )

        print(
            f"[*] Renegotiation markers observed: "
            f"{repeated_result.markers}"
        )

        print(
            f"[*] Successful renegotiations:       "
            f"{repeated_result.successful}/{args.repeat}"
        )

        if repeated_result.successful >= 2:

            print(
                "[WARN] Repeated client-initiated renegotiation "
                "is ENABLED."
            )

            print(
                "[WARN] This creates a potential TLS handshake "
                "resource-exhaustion attack surface."
            )

            print(
                "[INFO] This test does NOT demonstrate an actual "
                "denial-of-service condition."
            )

        elif repeated_result.successful == 1:

            print(
                "[INFO] One renegotiation succeeded, but repeated "
                "renegotiation was not demonstrated."
            )

        else:

            print(
                "[OK] Repeated client-initiated renegotiation "
                "was not confirmed."
            )

        if args.save_dir:
            save_evidence(
                args.save_dir,
                "client_initiated_repeated.txt",
                repeated_result.output,
            )

        if args.verbose:
            print()
            print("--- Raw repeated-renegotiation output ---")
            print(repeated_result.output.rstrip())

        #
        # 4. Legacy compatibility mode
        #

        print_section("LEGACY / INSECURE RENEGOTIATION")

        print(
            "[*] Repeating a renegotiation test with "
            "OpenSSL -legacy_renegotiation..."
        )

        legacy_result = test_renegotiation(
            connect_target,
            sni,
            config["flag"],
            repetitions=1,
            initial_delay=args.initial_delay,
            delay=args.delay,
            timeout=args.timeout,
            extra_args=[
                "-legacy_renegotiation",
            ],
        )

        legacy_secure_status = parse_secure_renegotiation(
            legacy_result.output
        )

        if (
            legacy_secure_status is False
            and legacy_result.successful >= 1
        ):

            legacy_confirmed = True

            print(
                "[FAIL] Legacy/insecure renegotiation appears to "
                "have completed successfully."
            )

            print(
                "[FAIL] This is distinct from ordinary RFC 5746 "
                "secure renegotiation."
            )

        elif secure_renegotiation is True:

            legacy_confirmed = False

            print(
                "[OK] RFC 5746 secure renegotiation was negotiated."
            )

            if legacy_result.successful >= 1:
                print(
                    "[INFO] Renegotiation also succeeds when the "
                    "OpenSSL client permits legacy compatibility."
                )
                print(
                    "[INFO] This DOES NOT prove legacy renegotiation "
                    "was used; RFC 5746 remains negotiated."
                )

            else:
                print(
                    "[INFO] No legacy renegotiation behavior was "
                    "observed."
                )

        elif legacy_result.successful == 0:

            legacy_confirmed = False

            print(
                "[OK] Legacy/insecure renegotiation was not confirmed."
            )

        else:

            legacy_confirmed = None

            print(
                "[?] Legacy renegotiation result is inconclusive."
            )

        if args.save_dir:
            save_evidence(
                args.save_dir,
                "legacy_renegotiation.txt",
                legacy_result.output,
            )

        if args.verbose:
            print()
            print("--- Raw legacy-renegotiation output ---")
            print(legacy_result.output.rstrip())

    else:

        print_section("RENEGOTIATION TESTS")

        print(
            "[INFO] No TLS 1.0, TLS 1.1, or TLS 1.2 connection "
            "was successfully negotiated."
        )

        print(
            "[INFO] Traditional TLS renegotiation therefore could "
            "not be tested."
        )

    #
    # TLS 1.3 interpretation
    #

    print_section("TLS 1.3")

    if protocol_results["TLS 1.3"].supported is True:

        print(
            "[OK] TLS 1.3 is supported."
        )

        print(
            "[INFO] Traditional TLS renegotiation does not exist "
            "in TLS 1.3."
        )

        print(
            "[INFO] TLS 1.3 KeyUpdate and post-handshake "
            "authentication are separate mechanisms."
        )

    else:

        print(
            "[INFO] TLS 1.3 was not negotiated during this test."
        )

    #
    # Final summary
    #

    summary_lines, security_exit_code = build_summary(
        target=connect_target,
        openssl_version=openssl_version,
        protocol_results=protocol_results,
        reneg_protocol_name=reneg_protocol_name,
        secure_renegotiation=secure_renegotiation,
        single_result=single_result,
        repeated_result=repeated_result,
        legacy_result=legacy_result,
        legacy_confirmed=legacy_confirmed,
    )

    print()
    print("\n".join(summary_lines))

    if args.save_dir:

        summary_text = "\n".join(summary_lines) + "\n"

        save_evidence(
            args.save_dir,
            "summary.txt",
            summary_text,
        )

        print()
        print(
            f"[+] Evidence saved to: "
            f"{args.save_dir.resolve()}"
        )

    #
    # The script deliberately returns zero after successful testing.
    #
    # A security finding is not considered a script execution error.
    # This makes it safer to integrate into larger pentest runners.
    #
    # security_exit_code is retained internally in case strict CI-style
    # behavior is added later.
    #

    _ = security_exit_code

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())

    except KeyboardInterrupt:
        print()
        print("[!] Interrupted by user.")
        sys.exit(130)
