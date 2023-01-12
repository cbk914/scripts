# Author cbk914
import argparse
import subprocess
import shutil
import re

# ASCII logo
logo = "TLS ANALYZER"

# Set up the command-line argument parser
parser = argparse.ArgumentParser(description="Analyze SSL/TLS certificate using testssl", prog=logo)
parser.add_argument("-t", "--target", required=True, help="Target HTTPS website to analyze")
parser.add_argument("-h", "--help", action='help', default=argparse.SUPPRESS, help='show this help message and exit')

# Parse the command-line arguments
args = parser.parse_args()

# Sanitize the target input
if not re.match(r"^https?://", args.target):
    args.target = "http://" + args.target
if not re.match(r"^https?://[\w.-]+$", args.target):
    print("Invalid target input. Only alphanumeric characters, dots, dashes and slashes are allowed.")
    exit(1)

# Check if testssl is installed
if shutil.which("testssl") is None:
    print("testssl is not installed on this system. Installing...")
    try:
        # Run the command to install testssl according to the OS
        subprocess.run(["apt-get", "install", "-y", "testssl"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error installing testssl: {e}")
        print(e.output.decode())
        exit(1)
    else:
        print("testssl installed successfully!")

try:
    # Run testssl against the target website with -9 and --html options
    testssl_output = subprocess.run(["testssl", "-9", "--html", args.target], capture_output=True, check=True)

    # Print the output from testssl
    print(testssl_output.stdout.decode())
