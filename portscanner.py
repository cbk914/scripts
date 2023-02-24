# Portscanner - an nmap wrapper
# Author cbk914
import nmap
import argparse
import os

def install_script(script_name):
    """Install an NSE script using nmap's script download feature."""
    print(f"Trying to install {script_name}...")
    nm = nmap.PortScanner()
    nm.script_download(script_name)
    # Check if script was downloaded successfully
    if script_name not in nm.get_nse_scripts():
        print(f"Error: Failed to download {script_name}. Please check the script name and try again.")
        exit(1)

def main():
    parser = argparse.ArgumentParser(description="Scan a target using nmap and export results to different formats")
    parser.add_argument("-t", "--target", required=True, help="Target to scan")
    parser.add_argument("-o", "--output", help="Output format (xml, txt, html)")
    parser.add_argument("-vs", "--vulnerabilityscan", action="store_true", help="Run vulnerability scan using vulners.nse script")
    args = parser.parse_args()

    # Initialize nmap scan object
    nm = nmap.PortScanner()

    # Perform scan
    try:
        if args.vulnerabilityscan:
            # Check if vuln.nse script fails to execute
            nm.scan(args.target, arguments='-sV -sC -oA scan_results --script vuln')
            if "Failed to execute" in nm.stderr:
                # Attempt to install the script and run the scan again
                install_script("vuln.nse")
                nm.scan(args.target, arguments='-sV -sC -oA scan_results --script vuln')

            # Check if vulscan.nse script fails to execute
            nm.scan(args.target, arguments='-sV -sC -oA scan_results --script vulscan')
            if "Failed to execute" in nm.stderr:
                # Attempt to install the script and run the scan again
                install_script("vulscan.nse")
                nm.scan(args.target, arguments='-sV -sC -oA scan_results --script vulscan')

            # Check if vulners.nse script fails to execute
            nm.scan(args.target, arguments='-sV -sC -oA scan_results --script vulners')
            if "Failed to execute" in nm.stderr:
                # Attempt to install the script and run the scan again
                install_script("vulners.nse")
                nm.scan(args.target, arguments='-sV -sC -oA scan_results --script vulners')

        else:
            nm.scan(args.target, arguments='-sV -sC -oA scan_results')
    except nmap.PortScannerError:
        print("Error: nmap module is not found or improperly installed")
        exit(1)
    except Exception as e:
        print("Error: ", e)
        exit(1)


    # Extract information from scan results
    hosts = nm.all_hosts()
    for host in hosts:
        print("Host: ", host)
        for protocol in nm[host].all_protocols():
            lport = nm[host][protocol].keys()
            for port in lport:
                print("Port: ", port)
                print("Service: ", nm[host][protocol][port]['name'])
                if 'script' in nm[host][protocol][port]:
                    for script in nm[host][protocol][port]['script']:
                        if "vuln" in script:
                            print("Vulnerability: ", script)

    # Export results to different formats
    if args.output:
        if args.output == "xml":
            nm.export("scan_results.xml")
        elif args.output == "txt":
            nm.export("scan_results.txt")
        elif args.output == "html":
            nm.export("scan_results.xml")
            # Convert the XML output to HTML using xsltproc
            xsltproc_cmd = "xsltproc nmap-bootstrap.xsl scan_results.xml > scan_results.html"
            os.system(xsltproc_cmd)
        else:
            print("Error: Invalid output format. Please specify xml, txt or html.")
            exit(1)

if __name__ == "__main__":
    main()
