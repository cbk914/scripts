#!/usr/bin/env python3
import argparse
import subprocess
import time

REN_COUNT = 10   # keep this LOW to avoid DoS accusations

def demonstrate_renegotiation(target):
    cmd = [
        "openssl", "s_client",
        "-connect", target,
        "-tls1_2"
    ]

    print(f"[+] Connecting to {target}")
    print(f"[+] Sending {REN_COUNT} renegotiation requests\n")

    # Prepare renegotiation triggers
    renegotiation_input = b"R\n" * REN_COUNT

    proc = subprocess.run(
        cmd,
        input=renegotiation_input,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=15
    )

    output = (proc.stdout + proc.stderr).decode(errors="ignore")
    print(output)

    if "Secure Renegotiation IS NOT supported" in output:
        print("\n[!!!] VULNERABLE")
        print("[!!!] Server accepts insecure renegotiation")
        print("[!!!] This allows session injection / MITM attacks")
    elif "Secure Renegotiation IS supported" in output:
        print("\n[+] SAFE")
        print("[+] Secure renegotiation enforced (RFC 5746)")
    else:
        print("\n[+] SAFE")
        print("[+] Renegotiation disabled or ignored")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TLS insecure renegotiation PoC (safe)"
    )
    parser.add_argument(
        "-t", "--target",
        required=True,
        help="host:port"
    )
    args = parser.parse_args()
    demonstrate_renegotiation(args.target)
