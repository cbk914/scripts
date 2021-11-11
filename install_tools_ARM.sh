#!/bin/bash
################################################################
# Basic pentesting tooling for Raspberry Pi non-Kali (ARM64)
# Pentesting Environment: Windows
# Version 0.1 Bouw
################################################################
# Update system
sudo apt update
sudo apt upgrade -y
sudo apt autoremove

# Install small basic tools
sudo apt install vim golang-go telnet screen rdesktop python3-pi python3-pip venv iptraf-ng xsltproc
curl https://getcroc.schollz.com | bash

# Some customizations
touch ~/.vimrc && echo "set mouse-=a" > ~/.vimrc

# Install minimum windows compatibility
sudo apt install wine32

# Install some python dependencies
pip3 install libtmux impacket termcolor #libnmap 

# Install Powershell
# Install libunwind8 and libssl1.0
# Regex is used to ensure that we do not install libssl1.0-dev, as it is a variant that is not required
sudo apt-get install '^libssl1.0.[0-9]$' libunwind8 -y

###################################
# Download and extract PowerShell

# Grab the latest tar.gz
wget https://github.com/PowerShell/PowerShell/releases/download/v7.2.0/powershell-7.2.0-linux-arm64.tar.gz

# Make folder to put powershell
mkdir ~/powershell

# Unpack the tar.gz file
tar -xvf ./powershell-7.2.0-linux-arm64.tar.gz -C ~/powershell

# Start PowerShell
# ~/powershell/pwsh

# Create symbolic link for pwsh
sudo ln -s ~/powershell/pwsh /usr/bin/pwsh

# Install Metasploit
#sudo apt-get install rbenv
#rbenv rehash
#apt-get install git ruby rubygems ruby-pg postgresql-common libpq-dev libpcap0.8 bundler ruby-pcaprub libpcap0.8 libpcap0.8-dev libsqlite3-dev 
#sudo gem install bundler
#git clone git://github.com/rapid7/metasploit-framework
#cd ~/metasploit-framework; ./msfupdate
#bundle install
curl https://raw.githubusercontent.com/rapid7/metasploit-omnibus/master/config/templates/metasploit-framework-wrappers/msfupdate.erb > msfinstall && \
  chmod 755 msfinstall && ./msfinstall
msfdb init
msfupdate

# Install Veil Framework
sudo apt-get -y install git
git clone https://github.com/Veil-Framework/Veil.git
cd Veil/
./config/setup.sh --force --silent
cd ~

# Install ExploitDB
git clone https://github.com/offensive-security/exploitdb.git /opt/exploit-database
sudo  ln -sf /opt/exploit-database/searchsploit /usr/local/bin/searchsploit
cp -n /opt/exploit-database/.searchsploit_rc ~/

# Install PowerSploit
cd ~/
git clone https://github.com/PowerShellMafia/PowerSploit.git

# Install Powershell-Empire
git clone https://github.com/EmpireProject/Empire.git
cd Empire/; ./setup/install.sh
cd ~/

# Install nishang
sudo apt install nishang

# Install nuclei
git clone https://github.com/projectdiscovery/nuclei.git
cd nuclei/v2/cmd/nuclei
go build
mv nuclei /usr/local/bin/
#nuclei -version
nuclei -ut
cd ~/ 

# Install evil-winRM
git clone https://github.com/Hackplayers/evil-winrm.git

# Install Sticky Keys Hunter
git clone https://github.com/ztgrace/sticky_keys_hunter.git

# Install Double Pulsar checker
git clone https://github.com/countercept/doublepulsar-detection-script.git

# Install Eternal Blue checker
git clone https://github.com/3ndG4me/AutoBlue-MS17-010.git

# Install AD Tools
git clone https://github.com/DanMcInerney/icebreaker.git
git clone https://github.com/dirkjanm/krbrelayx.git
git clone https://github.com/dev-2null/ADCollector.git

# WMI
git clone https://github.com/rootclay/WMIHACKER.git
git clone https://github.com/Orange-Cyberdefense/wmi-shell.git

# RDP
git clone https://github.com/robertdavidgraham/rdpscan.git

# RPC
git clone https://github.com/topotam/PetitPotam.git

# Samba
git clone https://github.com/giuseppsss/sambacry-pw2.git
git clone https://github.com/d4t4s3c/SMBploit.git
