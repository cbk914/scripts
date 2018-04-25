#!/bin/bash
sudo iptables -I INPUT -j NFQUEUE
sudo iptables -I OUTPUT -j NFQUEUE
suricata -c /etc/suricata/suricata.yaml -q 0 
# IPS MODE
# -i <iface> for IDS mode
sleep 10
tail -f /var/log/suricata/fast.log|ccze
