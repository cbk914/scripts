#!/usr/bin/env python3
# Author: cbk914
import argparse
import json
import requests

def display_help():
    print("Usage: python import-json.py -f file -u url [-o output] [-p proxy] [-h]")
    print("Retrieves URLs from a JSON file and sends a request to each URL using requests")
    print("  -f file         path to the JSON file")
    print("  -u url          base URL to append the URI to")
    print("  -o output       specify the output file name")
    print("  -p proxy        send URL requests to proxy")
    print("  -h              display this help and exit")
    exit(0)

parser = argparse.ArgumentParser(description="Retrieves URLs from a JSON file and sends a request to each URL using requests")
parser.add_argument("-f", "--file", type=str, required=True, help="path to the JSON file")
parser.add_argument("-u", "--url", type=str, required=True, help="base URL to append the URI to")
parser.add_argument("-o", "--output", type=str, help="specify the output file name")
parser.add_argument("-p", "--proxy", type=str, help="send URL requests to proxy")
args = parser.parse_args()

# Check that both -f and -u options are set
if not args.file or not args.url:
    print("Error: -f and -u options are required")
    exit(1)

urls = []
# Iterate through each line of the file
with open(args.file) as f:
    for line in f:
        # Extract the URI using json.loads
        uri = json.loads(line)['result']['uri']
        # Construct the full URL
        url = args.url + uri
        # Remove duplicates
        if url not in urls:
            # Print the URL
            print(url)
            urls.append(url)
        else:
            print("Duplicate URL skipped.")
        # Use requests to send a request to the URL
        if args.proxy:
            response = requests.get(url, proxies={'http': args.proxy, 'https': args.proxy})
        else:
            response = requests.get(url)
        response_code = response.status_code
        #write to file
        if args.output:
            with open(args.output, 'a') as file:
                file.write(f"URL: {url} Response Code: {response_code}\n")
            if response_code == 200:
                with open(args.output+'-200', 'a') as file:
                    file.write(f"URL: {url} Response Code: {response_code}\n")
            elif response_code == 404:
                with open(args.output+'-404', 'a') as file:
                    file.write(f"URL: {url} Response Code: {response_code}\n")
			elif response_code == 403:
				with open(args.output+'-403', 'a') as file:
                    file.write(f"URL: {url} Response Code: {response_code}\n")
            elif response_code == 500:
                with open(args.output+'-500', 'a') as file:
                    file.write(f"URL: {url} Response Code: {response_code}\n")
            else:
                with open(args.output+'-other', 'a') as file:
                    file.write(f"URL: {url} Response Code: {response_code}\n")
        # Print the response code
        print(f"Response Code: {response_code}")
