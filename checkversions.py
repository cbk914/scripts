#!/usr/bin/env python
# Author cbk914
import re
import argparse
import requests
import subprocess
import sys

# Characters that have no business in an output filename. The argv list form
# already makes injection impossible; this is defence in depth so a filename
# containing shell syntax is rejected loudly rather than passed to nmap.
# Backslash is deliberately NOT listed: it is a normal path separator on
# Windows and rejecting it would break ordinary absolute paths.
_UNSAFE_FILENAME_CHARS = set(';&|$`\n\r<>|*?"\'')

def validate_output_path(path):
	"""Return a safe nmap output path, or exit with an error."""
	if not path or not path.strip():
		parser.error("Output file name must not be empty")
	bad = sorted(_UNSAFE_FILENAME_CHARS & set(path))
	if bad:
		parser.error(f"Invalid output file name {path!r}: contains {bad!r}")
	return path

# Set up the command-line argument parser
parser = argparse.ArgumentParser(description="Check server software and version")
parser.add_argument("-t", "--target", required=True, help="Target URL")
parser.add_argument("-o", "--output", help="Output file name in XML format")

# Parse the command-line arguments
args = parser.parse_args()

# Sanitize the input
url = re.search(r"^https?://([a-zA-Z0-9-.]+)", args.target)
if not url:
	parser.error("Invalid target format. Only URLs with valid domain name are allowed")
url = url.group(1)

# Define a function to check the software and versions
def check_versions(url):
    try:
        # Send a GET request to the URL
        response = requests.get(url)
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to target: {e}")
        return
    
    # Check the status code of the response
    if response.status_code == 200:
        # Check the Server header to get the web software
        server = response.headers.get('Server')

        # If the Server header exists, check the version
        if server:
            # Search for a version in the Server header
            version = re.search('\d+\.\d+', server)

            # If a version was found, print it
            if version:
                print(f'The web software is {server} and version is {version.group()}')

            # If no version was found, print the web software
            else:
                print(f'The web software is {server}')

        # If the Server header does not exist, print a message
        else:
            print('The web server is not specified')

# Run nmap for version and vulnerabilities check
check_versions(url)

# Build the nmap invocation as an argv list, never a shell string.
#
# The original was:
#     nmap_cmd  = "nmap -sV ... " + url
#     nmap_cmd += f" -oX {args.output}"
#     output = subprocess.run(nmap_cmd, shell=True, check=True)
#
# With shell=True the whole line is parsed by the system shell. The target was
# incidentally protected by the regex above, whose capture group only admits
# [a-zA-Z0-9-.], but the -o/--output value was interpolated with no validation
# at all, so `-o "out.xml; <command>"` executed that command.
#
# A list plus the default shell=False removes the class of bug rather than
# filtering one instance of it: each value becomes exactly one argv element.
nmap_cmd = ["nmap", "-sV", "--min-rate=5000", "-Pn", "-vvv",
            "--script=vulners", url]

if args.output:
    output_path = validate_output_path(args.output)
    nmap_cmd += ["-oX", output_path]

try:
    output = subprocess.run(nmap_cmd, shell=False, check=True,
                            capture_output=True, text=True)
except FileNotFoundError:
    print("Error: nmap was not found on PATH. Install it and retry.")
    sys.exit(1)
except subprocess.CalledProcessError as exc:
    print(f"nmap exited with status {exc.returncode}")
    if exc.stderr:
        print(exc.stderr)
    sys.exit(exc.returncode)

if output.stdout:
    print(output.stdout)
if output.stderr:
    print(output.stderr, file=sys.stderr)
