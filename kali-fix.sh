#!/bin/bash
# Check for new keyrings after expiration: https://pkg.kali.org/pkg/kali-archive-keyring
# Another option - sudo wget https://archive.kali.org/archive-key.asc -O /etc/apt/trusted.gpg.d/kali-archive-keyring.asc
gpg --keyserver keyserver.ubuntu.com --recv-key 7D8D0BF6
gpg --fingerprint 7D8D0BF6
gpg -a --export 7D8D0BF6 | apt-key add -
# wget https://ftp.cc.uoc.gr/mirrors/linux/kali/kali/pool/main/k/kali-archive-keyring/kali-archive-keyring_2022.1_all.deb
# apt install ./kali-archive-keyring_2022.1_all.deb
apt-get update
