import requests
import re
import sys
import argparse
import logging

logging.basicConfig(filename="download.log", level=logging.DEBUG, format="%(asctime)s: %(message)s")

parser = argparse.ArgumentParser()
parser.add_argument("-y", "--year", type=int, help="Download data for specific year (yyyy)")
args = parser.parse_args()

# Verify SSL certificate for secure connection
try:
    r = requests.get('https://nvd.nist.gov/vuln/data-feeds#JSON_FEED', verify=True)
except requests.exceptions.SSLError as e:
    logging.error("Error in SSL certificate verification: %s" % e)
    sys.exit(1)

for filename in re.findall("nvdcve-1.1-[0-9]*\.json\.zip",r.text):
    if args.year:
        if str(args.year) not in filename:
            continue
    print(filename)
    # Use session to persist the connection and reuse it
    with requests.Session() as session:
        session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
        try:
            r_file = session.get("https://nvd.nist.gov/feeds/json/cve/1.1/" + filename, stream=True)
            # Raise an error in case of unsuccessful response status
            r_file.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error("Error in downloading %s: %s" % (filename, e))
            continue
        with open("nvd/" + filename, 'wb') as f:
            for chunk in r_file.iter_content(chunk_size=8192):
                # write the content to the file in chunks to avoid memory exhaustion
                f.write(chunk)
                downloaded = f.tell()
                print("Downloaded %.2f%% of %s" % (downloaded / int(r_file.headers['Content-Length']) * 100, filename))
    logging.info("Successfully downloaded %s" % filename)
