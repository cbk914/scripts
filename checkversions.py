#!/usr/bin/env python
# Author cbk914
import re
import argparse
import requests
import subprocess

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
nmap_cmd = "nmap -sV --min-rate=5000 -Pn -vvv -script=vulners " + url
if args.output:
    nmap_cmd += f" -oX {args.output}"
output = subprocess.run(nmap_cmd, shell=True, check=True)

print(output)
