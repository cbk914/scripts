#!/bin/bash
# Author: cbk914
function display_help {
    echo "Usage: $0 -f file -u url [-o output] [-p proxy] [-h]"
    echo "Retrieves URLs from a JSON file and sends a request to each URL using curl"
    echo "  -f file         path to the JSON file"
    echo "  -u url          base URL to append the URI to"
    echo "  -o output       specify the output file name without extension"
    echo "  -oc outputclean specify the output file name without extension with full URLs only"
    echo "  -p proxy        send URL requests to proxy"
    echo "  -h              display this help and exit"
    exit 0
}

while getopts "f:u:o:p:hoc" opt; do
  case $opt in
    f) file="$OPTARG"
    ;;
    u) url_base="$OPTARG"
    ;;
    o) output="$OPTARG"
    ;;
    oc) output_clean=1
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

urls=()
# Iterate through each line of the file
while IFS='' read -r line || [[ -n "$line" ]]; do
    # Extract the URI using jq
    uri=$(echo $line | jq -r '.result.uri')
    # Construct the full URL
    url="$url_base$uri"
    # Remove duplicates
    if [[ ! " ${urls[@]} " =~ " ${url} " ]]; then
    # Print the URL
    echo $url
    urls+=($url)
    else
        echo "Duplicate URL skipped."
    fi
    # Use curl to send a request to the URL
    if [ -z "$proxy" ] || [ "$proxy" == "null" ]; then
        if [ -n "$output" ]; then
            response_code=$(curl -o /dev/null --silent --head --write-out '%{http_code}' $url)
            echo "URL: $url Response Code: $response_code" >> $output
            if [ $response_code -eq 200 ]; then
                echo "URL: $url Response Code: $response_code" >> $output-200.txt
            elif [ $response_code -eq 404 ]; then
                echo "URL: $url Response Code: $response_code" >> $output-404.txt
            elif [ $response_code -eq 500 ]; then
                echo "URL: $url Response Code: $response_code" >> $output-500.txt
            else
                echo "URL: $url Response Code: $response_code" >> $output-other.txt
            fi
        else
            curl -k -L $url
        fi
    else
        if [ -n "$outputclean" ]; then
        echo "$url" >> $output
    else
        response_code=$(curl -o /dev/null --silent --head --write-out '%{http_code}' $url)
        echo "URL: $url Response Code: $response_code" >> $output
        if [ $response_code -eq 200 ]; then
            echo "URL: $url Response Code: $response_code" >> $output-200.txt
        elif [ $response_code -eq 404 ]; then
            echo "URL: $url Response Code: $response_code" >> $output-404.txt
        elif [ $response_code -eq 403 ]; then
            echo "URL: $url Response Code: $response_code" >> $output-403.txt
        elif [ $response_code -eq 500 ]; then
            echo "URL: $url Response Code: $response_code" >> $output-500.txt
        else
            echo "URL: $url Response Code: $response_code" >> $output-other.txt
        fi
        else
            curl -k -L -x $proxy $url
        fi
    fi
    if [ $? -ne 0 ]; then
        echo "Error: curl command failed"
    fi
done < "$file"
