#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: cbk914
import getpass
import paramiko
import subprocess
import signal
import sys

def cleanup(process):
    if process.poll() is None:
        process.terminate()

def handler(signum, frame):
    print('Signal handler called with signal', signum)
    process.kill()
    
def check_ssh_config(ssh_client):
    print("Checking SSH configuration...")

    ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command("sudo cat /etc/ssh/sshd_config")

    for line in ssh_stdout:
        line = line.strip()
        if line.startswith('#') or len(line) == 0:
            continue
        key, value = line.split(' ', 1)
        value = value.strip()
        if key == 'AllowTcpForwarding' and value == 'no':
            print("Warning: TCP forwarding is disabled. Change AllowTcpForwarding to yes.")
        if key == 'PermitTunnel' and value == 'no':
            print("Warning: Tunneling is disabled. Change PermitTunnel to yes.")
    print("SSH configuration check completed.")

try:
    remote_server = input("Enter the remote server address: ")
    ssh_user = input("Enter the SSH user: ")
    ssh_password = getpass.getpass(prompt="Enter the SSH password: ")

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(remote_server, username=ssh_user, password=ssh_password)

    check_ssh_config(ssh_client)

    ssh_client.close()

    tunnel_type = input("Enter the tunnel type (local, remote, proxy): ")    

try:
    remote_server = input("Enter the remote server address: ")
    ssh_user = input("Enter the SSH user: ")
    ssh_password = getpass.getpass(prompt="Enter the SSH password: ")
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

