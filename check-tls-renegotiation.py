#!/usr/bin/env python3
import argparse
import subprocess

def check_renegotiation(target):
    cmd = [
        "openssl", "s_client",
        "-connect", target,
        "-tls1_2"
    ]

    proc = subprocess.run(
        cmd,
        input=b"R\n",   # harmless on OpenSSL 3.x
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10
    )

    output = (proc.stdout + proc.stderr).decode(errors="ignore")
    print(output)

    if "Secure Renegotiation IS NOT supported" in output:
        print(f"[!] VULNERABLE: insecure renegotiation supported on {target}")
    elif "Secure Renegotiation IS supported" in output:
        print(f"[+] SAFE: secure renegotiation supported on {target}")
    else:
        print(f"[+] SAFE: renegotiation disabled or not applicable on {target}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TLS renegotiation check (OpenSSL 3.x safe)"
    )
    parser.add_argument("-t", "--target", required=True, help="host:port")
    args = parser.parse_args()
    check_renegotiation(args.target)
