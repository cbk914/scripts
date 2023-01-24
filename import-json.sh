#!/bin/bash
# Author cbk914

function display_help {
    echo "Usage: $0 -f file -u url [-h]"
    echo "Retrieves URLs from a JSON file and sends a request to each URL using curl"
    echo "  -f file         path to the JSON file"
    echo "  -u url          base URL to append the URI to"
    echo "  -h              display this help and exit"
    exit 0
}

while getopts "f:u:p:h" opt; do
  case $opt in
    f) file="$OPTARG"
    ;;
    u) url_base="$OPTARG"
    ;;
    p) proxy="$OPTARG"
    ;;
    h) display_help
    ;;
    \?) echo "Invalid option -$OPTARG" >&2
    exit 1
    ;;
  esac
done

# Check that both -f and -u options are set
if [ -z "$file" ] || [ -z "$url_base" ]; then
    echo "Error: -f and -u options are required" >&2
    exit 1
fi

# Iterate through each line of the file
while read line; do
    # Extract the URI using jq
    uri=$(echo $line | jq -r '.result.uri')
    # Construct the full URL
    url="$url_base$uri"
    # Remove duplicates
    if [[ ! " ${url[@]} " =~ " ${url} " ]]; then
    # Print the URL
    echo $url
    url+=($url)
    fi
    echo "Duplicate URLs removed."
    # Use curl to send a request to the URL
    if [ -z "$proxy" ]; then
        curl -k $url
    else
        curl -k -x $proxy $url
    fi
done < $file
