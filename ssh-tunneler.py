#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: cbk914

import subprocess
import signal
import sys

class SSHTunnel:
    def __init__(self):
        self.process = None

    def cleanup(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()

    def handler(self, signum, frame):
        print("Signal received, cleaning up...")
        self.cleanup()
        sys.exit(0)

    def establish_tunnel(self):
        try:
            remote_server = input("Enter the remote server address: ").strip()
            ssh_user = input("Enter the SSH user: ").strip()
            tunnel_type = input("Enter the tunnel type (local, remote, proxy, x_tunnel_trusted, x_tunnel_untrusted): ").strip()

            if tunnel_type not in ['local', 'remote', 'proxy', 'x_tunnel_trusted', 'x_tunnel_untrusted']:
                print("Invalid tunnel type. Please enter 'local', 'remote', 'proxy', 'x_tunnel_trusted', or 'x_tunnel_untrusted'.")
                sys.exit(1)

            if tunnel_type in ['local', 'remote']:
                local_port = input("Enter the local port: ").strip()
                remote_port = input("Enter the remote port: ").strip()

            if tunnel_type == 'local':
                command = [
                    'ssh',
                    '-L',
                    f'{local_port}:127.0.0.1:{remote_port}',
                    '-N',
                    '-f',
                    '-o', 'ExitOnForwardFailure=yes',
                    f'{ssh_user}@{remote_server}'
                ]
            elif tunnel_type == 'remote':
                command = [
                    'ssh',
                    '-R',
                    f'{remote_port}:127.0.0.1:{local_port}',
                    '-N',
                    '-f',
                    '-o', 'ExitOnForwardFailure=yes',
                    f'{ssh_user}@{remote_server}'
                ]
            elif tunnel_type == 'proxy':
                proxy_port = input("Enter the proxy port: ").strip()
                command = [
                    'ssh',
                    '-D',
                    f'{proxy_port}',
                    '-N',
                    '-f',
                    '-o', 'ExitOnForwardFailure=yes',
                    f'{ssh_user}@{remote_server}'
                ]
            elif tunnel_type == 'x_tunnel_trusted':
                command = [
                    'ssh',
                    '-Y',
                    f'{ssh_user}@{remote_server}'
                ]
            elif tunnel_type == 'x_tunnel_untrusted':
                command = [
                    'ssh',
                    '-X',
                    f'{ssh_user}@{remote_server}'
                ]

            persistent_tunnel = input("Do you want to create a persistent tunnel? (y/n): ").strip()
            if persistent_tunnel.lower() == 'y':
                command.extend(['-o', 'ServerAliveInterval=60'])

            with subprocess.Popen(command) as self.process:
                print(f"SSH {tunnel_type} tunnel established.")
                if tunnel_type in ['local', 'remote']:
                    print(f"Connect to it using localhost:{local_port}")
                elif tunnel_type == 'proxy':
                    print(f"Connect to the proxy using localhost:{proxy_port}")

                # Register cleanup function to be called upon exit
                signal.signal(signal.SIGTERM, self.handler)
                signal.signal(signal.SIGINT, self.handler)

                # Wait for the subprocess to finish
                self.process.wait()

                if self.process.returncode != 0:
                    print(f"SSH command failed with return code {self.process.returncode}")
                    sys.exit(1)

        except subprocess.CalledProcessError as e:
            print(f"SSH command failed: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            print("User interrupted the process.")
            self.cleanup()
            sys.exit(0)
        except Exception as e:
            print(f"Exception: {e}")
            sys.exit(1)

def main():
    tunnel = SSHTunnel()
    tunnel.establish_tunnel()

if __name__ == "__main__":
    main()
