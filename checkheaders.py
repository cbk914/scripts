# Check Headers
# Author cbk914
import argparse
import requests
import os
import re

# Set up the command-line argument parser
parser = argparse.ArgumentParser(description="Analyze headers of a website")
parser.add_argument("-t", "--target", required=True, help="Target website to analyze")
parser.add_argument("-f", "--file", help="File to save headers to")
parser.add_argument("--help", action='help', default=argparse.SUPPRESS, help='show this help message and exit')

# Parse the command-line arguments
args = parser.parse_args()

# Sanitize the input
if not re.match(r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}$", args.target):
    parser.error("Invalid target format. Only domain names are allowed")

if args.file is not None:
    if not re.match(r"^[a-zA-Z0-9_-]+\.txt$", args.file):
        parser.error("Invalid file name format. Only alphanumeric characters, '_' and '-' are allowed, and must have .txt extension")

try:
    # Send a GET request to the target website
    protocol = "https://" if "https://" in args.target else "http://"
    response = requests.get(protocol + args.target)
    headers = response.headers
    status_code = response.status_code
except requests.exceptions.RequestException as e:
    print(f"Error connecting to target website: {e}")
    exit(1)
else:
    # Print headers
    print(f"Status code: {status_code}")
    print(headers)

  # Save headers to file
    if args.file is not None:
        try:
            with open(args.file, 'w') as f:
                f.write(f"Status code: {status_code}\n")
                for header in headers:
                    f.write(f"{header}: {headers[header]}\n")
            print(f"Headers saved to {args.file}")
        except Exception as e:
            print(f"Error saving headers to file: {e}")

# Compare headers with ASVS v4 and WSTG recommendations
security_headers = ['Strict-Transport-Security', 'X-Frame-Options', 'X-XSS-Protection', 'X-Content-Type-Options']
missing_headers = []
headers_lower = {k.lower(): v for k, v in headers.items()}
for header in security_headers:
    if header.lower() not in headers_lower:
        missing_headers.append(header)
if missing_headers:
    print(f"Missing security headers: {missing_headers}")
else:
    print("All recommended security headers are present")
    
# Analyze Content Security Policy
csp = headers.get("Content-Security-Policy", None)
if csp:
    print("Content Security Policy found:")
    print(csp)
    # Check for recommended CSP directives
    csp_directives = ["default-src 'self'", "script-src 'self'", "object-src 'none'", "base-uri 'self'"]
    missing_directives = []
    for directive in csp_directives:
        if directive not in csp:
            missing_directives.append(directive)
    if missing_directives:
        print(f"Missing recommended CSP directives: {missing_directives}")
    else:
        print("All recommended CSP directives are present")
else:
    print("Content Security Policy not found. Recommend implementing one.")    
