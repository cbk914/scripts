
import json
import argparse
import requests

def display_help():
    print("Usage: python script.py -f file -u url [-h]")
    print("Retrieves URLs from a JSON file and sends a request to each URL using requests")
    print("  -f file         path to the JSON file")
    print("  -u url          base URL to append the URI to")
    print("  -h              display this help and exit")
    exit(0)

# Define the command-line options
parser = argparse.ArgumentParser(description='Retrieves URLs from a JSON file and sends a request to each URL using requests')
parser.add_argument('-f', '--file', help='path to the JSON file', required=True)
parser.add_argument('-u', '--url', help='base URL to append the URI to', required=True)
parser.add_argument('-h', '--help', action='store_true', help='display this help and exit')
args = parser.parse_args()

if args.help:
    display_help()

# Open the file and iterate through each line
with open(args.file, 'r') as file:
    for line in file:
        # Load the JSON data
        data = json.loads(line)
        # Extract the URI
        uri = data['result']['uri']
        # Construct the full URL
        url = args.url + uri
        # Print the URL
        print(url)
        # Send a request to the URL
        response = requests.get(url)
        print(response.text)
