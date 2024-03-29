#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: cbk914
import nmap
import argparse
import os
import socket
import subprocess

def check_script(nm, script_name):
    """Check if an NSE script is installed and install it if necessary."""
    print(f"Checking for {script_name} script...")
    if script_name not in nm.get_nse_scripts():
        install_script(nm, script_name)
    else:
        print(f"{script_name} script is already installed.")

def install_script(nm, script_name):
    """Install an NSE script using nmap's script download feature."""
    print(f"Installing {script_name} script...")
    nm.script_download(script_name)
    # Check if script was downloaded successfully
    if script_name not in nm.get_nse_scripts():
        print(f"Error: Failed to download {script_name} script. Please check the script name and try again.")
        exit(1)

def main():
    parser = argparse.ArgumentParser(description="Scan a target using nmap and export results to different formats")
    parser.add_argument("-t", "--target", required=True, help="Target to scan")
    parser.add_argument("-o", "--output", help="Output format (xml, txt, html)")
    parser.add_argument("-vs", "--vulnerabilityscan", action="store_true", help="Run vulnerability scan using vuln, vulscan, and vulners.nse scripts")
    args = parser.parse_args()

    # Check if target argument is a file name
    if os.path.isfile(args.target):
        targets = f"-iL {args.target}"
    else:
        targets = args.target
        # Validate target argument
        try:
            socket.gethostbyname(targets)
        except socket.gaierror:
            print(f"Error: Invalid target '{targets}'. Please enter a valid IP address, hostname, or file name.")
            exit(1)


    # Initialize nmap scan object
    nm = nmap.PortScanner()

    # Perform scan
    try:
        if args.vulnerabilityscan:
            check_script(nm, "vuln.nse")
            check_script(nm, "vulscan.nse")
            check_script(nm, "vulners.nse")
            nm.scan(args.target, arguments='-sV -sC -oX scan_results.xml --script vuln,vulscan,vulners')
        else:
            nm.scan(args.target, arguments='-sV -sC -oX scan_results.xml')
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
            with open("scan_results.xml", "r") as f:
                xml_output = f.read()
            print(xml_output)
        elif args.output == "txt":
            nm.export_to_file("scan_results.txt", "grepable")
            with open("scan_results.txt", "r") as f:
                txt_output = f.read()
            print(txt_output)
                elif args.output == "html":
            # Convert the XML output to HTML using xsltproc
            try:
                subprocess.check_output(["xsltproc", "nmap-bootstrap.xsl", "scan_results.xml", "-o", "scan_results.html"], stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                print(f"Error: Failed to convert XML to HTML. Error message: {e.output.decode('utf-8')}")
                exit(1)

            # Print HTML output to console
            with open("scan_results.html", "r") as f:
                html_output = f.read()
            print(html_output)
        else:
            print("Error: Invalid output format. Please specify xml, txt or html.")
            exit(1)

if __name__ == "__main__":
    main()
