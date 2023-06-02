#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: cbk914
import subprocess
import getpass
import signal
import sys

def cleanup(process):
    if process.poll() is None:
        process.terminate()

def handler(signum, frame):
    print("Signal received, cleaning up...")
    cleanup(process)
    sys.exit(0)

try:
    remote_server = input("Enter the remote server address: ")
    ssh_user = input("Enter the SSH user: ")
    tunnel_type = input("Enter the tunnel type (local, remote, proxy): ")

    if tunnel_type not in ['local', 'remote', 'proxy']:
        print("Invalid tunnel type. Please enter 'local', 'remote' or 'proxy'.")
        sys.exit(1)

    if tunnel_type in ['local', 'remote']:
        local_port = input("Enter the local port: ")
        remote_port = input("Enter the remote port: ")

    if tunnel_type == 'local':
        command = [
            'ssh',
            '-L',
            f'{local_port}:127.0.0.1:{remote_port}',
            '-N',
            '-f',
            f'{ssh_user}@{remote_server}'
        ]
    elif tunnel_type == 'remote':
        command = [
            'ssh',
            '-R',
            f'{remote_port}:127.0.0.1:{local_port}',
            '-N',
            '-f',
            f'{ssh_user}@{remote_server}'
        ]
    elif tunnel_type == 'proxy':
        proxy_port = input("Enter the proxy port: ")
        command = [
            'ssh',
            '-D',
            f'{proxy_port}',
            '-N',
            '-f',
            f'{ssh_user}@{remote_server}'
        ]

    process = subprocess.Popen(command)

    print(f"SSH {tunnel_type} tunnel established.")
    if tunnel_type in ['local', 'remote']:
        print(f"Connect to it using localhost:{local_port}")
    else:
        print(f"Connect to the proxy using localhost:{proxy_port}")

    # Register cleanup function to be called upon exit
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    while True:
        pass

except Exception as e:
    print(f"Exception: {e}")
    sys.exit(1)

