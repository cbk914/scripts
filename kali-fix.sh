#!/bin/bash
wget https://ftp.cc.uoc.gr/mirrors/linux/kali/kali/pool/main/k/kali-archive-keyring/kali-archive-keyring_2022.1_all.deb
apt install ./kali-archive-keyring_2022.1_all.deb
apt-get update
