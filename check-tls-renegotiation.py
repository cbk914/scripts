#!/bin/python
# Author: cbk914
import argparse
import subprocess

def check_renegotiation(target):
    """
    Check for insecure SSL/TLS renegotiation on the specified target.
    """
    result = subprocess.run(['openssl', 's_client', '-connect', target, '-msg'],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    print(result.stdout.decode())
    if "Secure Renegotiation IS NOT supported" in result.stdout.decode():
        print("[*] Insecure renegotiation is supported on target " + target)
    else:
        print("[*] Insecure renegotiation is not supported on target " + target)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check for SSL/TLS insecure renegotiation.")
    parser.add_argument("-t", "--target", required=True, help="Target hostname and port (e.g. example.com:443)")
    args = parser.parse_args()
    check_renegotiation(args.target)