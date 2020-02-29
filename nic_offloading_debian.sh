#!/bin/bash
# Put this script on /etc/network/interfaces.d/
# Other option is put it in /etc/network/interfaces
# Changing lines 15-16 for:
# post-up for i in rx tx gso ; do ethtool -K $IFACE $i off; done

RUN=true
case "${IF_NO_TOE,,}" in
    no|off|false|disable|disabled)
        RUN=false
    ;;
esac

if [ "$MODE" = start -a "$RUN" = true ]; then
  TOE_OPTIONS="rx tx sg tso ufo gso gro lro rxvlan txvlan rxhash"
  for TOE_OPTION in $TOE_OPTIONS; do
    /sbin/ethtool --offload "$IFACE" "$TOE_OPTION" off &>/dev/null || true
  done
fi
