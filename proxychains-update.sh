#!/bin/bash

# Define the URL for each proxy list
HTTP_URL="https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt"
SOCKS4_URL="https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt"
SOCKS5_URL="https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt"

# Define the output file for proxychains
PROXYCHAINS_CONF="proxychains.conf"

# Create or overwrite the proxychains.conf file
echo "# proxychains.conf" > $PROXYCHAINS_CONF
echo "# ProxyChains configuration file" >> $PROXYCHAINS_CONF
echo "#" >> $PROXYCHAINS_CONF
echo "# Add proxy here ..." >> $PROXYCHAINS_CONF
echo "# meanwile" >> $PROXYCHAINS_CONF
echo "# defaults set to \"tor\"" >> $PROXYCHAINS_CONF
echo "#" >> $PROXYCHAINS_CONF
echo "# [ProxyList]" >> $PROXYCHAINS_CONF
echo "#" >> $PROXYCHAINS_CONF
echo "# Examples:" >> $PROXYCHAINS_CONF
echo "# socks5 127.0.0.1 9050" >> $PROXYCHAINS_CONF
echo "# http 192.168.1.1 8080" >> $PROXYCHAINS_CONF
echo "" >> $PROXYCHAINS_CONF

# Add HTTP Proxies
echo "[ProxyList]" >> $PROXYCHAINS_CONF
echo "# HTTP Proxies" >> $PROXYCHAINS_CONF
curl -s $HTTP_URL | head -n 10 | awk '{print "http " $1 " " $2}' >> $PROXYCHAINS_CONF

# Add SOCKS4 Proxies
echo "" >> $PROXYCHAINS_CONF
echo "# SOCKS4 Proxies" >> $PROXYCHAINS_CONF
curl -s $SOCKS4_URL | head -n 10 | awk '{print "socks4 " $1 " " $2}' >> $PROXYCHAINS_CONF

# Add SOCKS5 Proxies
echo "" >> $PROXYCHAINS_CONF
echo "# SOCKS5 Proxies" >> $PROXYCHAINS_CONF
curl -s $SOCKS5_URL | head -n 10 | awk '{print "socks5 " $1 " " $2}' >> $PROXYCHAINS_CONF

echo "" >> $PROXYCHAINS_CONF
echo "# End of Proxy List" >> $PROXYCHAINS_CONF

echo "proxychains.conf file updated with the latest 10 proxies from each list."

