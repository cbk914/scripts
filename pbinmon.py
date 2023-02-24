import os
import re
import time
import requests

STATIC_SLEEP = 15
DYNAMIC_SLEEP = 1
DIR = "."
URL = "http://pastebin.com/"
DWN = "pastebin.php?dl="

while True:
    download = 0
    date = time.strftime("%H:%M:%S %d-%m-%Y")
    date_dir = date.split()[1]
    if not os.path.isdir(os.path.join(DIR, date_dir)):
        print(f"{date} - Creating new download directory {os.path.join(DIR, date_dir)}")
        os.makedirs(os.path.join(DIR, date_dir))
    html = requests.get(URL).text
    pastes = re.findall(r'<a href="http://pastebin.com/([^"]+)">', html)
    for file in pastes:
        if not os.path.isfile(os.path.join(DIR, date_dir, file)):
            print(f"{date} - Downloading {file} {URL}{DWN}{file}")
            with open(os.path.join(DIR, date_dir, file), "wb") as f:
                f.write(requests.get(f"{URL}{DWN}{file}").content)
            download += 1
    if DYNAMIC_SLEEP == 1:
        if download == 0:
            sleep = 65
        elif download > 8:
            sleep = 2
        elif download > 5:
            sleep = 5
        elif download > 3:
            sleep = 15
        else:
            sleep = 45
    else:
        sleep = STATIC_SLEEP
    print(f"{date} - Sleeping ZzZzz ({sleep}s) zZzZzz")
    time.sleep(sleep)
