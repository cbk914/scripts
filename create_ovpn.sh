#!/bin/bash
#Dir where easy-rsa is placed
EASY_RSA_DIR="/etc/ssl/easy-rsa"
KEYS_DIR="$EASY_RSA_DIR/keys"
# Dir where profiles will be placed
OVPN_PATH="/root/ovpn"
REMOTE="your.server port"
 
 
if [ -z "$1" ]
then 
        echo -n "Enter new client common name (CN): "
        read -e CN
else
        CN=$1
fi
 
 
if [ -z "$CN" ]
        then echo "You must provide a CN."
        exit
fi
 
cd $EASY_RSA_DIR
if [ -f $KEYS_DIR/$CN.crt ]
then 
        echo "Certificate with the CN $CN already exists!"
        echo " $KEYS_DIR/$CN.crt"
else
source ./vars > /dev/null
./pkitool $CN
fi
 
cat > $OVPN_PATH/${CN}.ovpn << END
client
dev tun
resolv-retry infinite
nobind
persist-key
persist-tun
verb 1
comp-lzo
proto tcp
remote $REMOTE
 
<ca>
`cat $KEYS_DIR/ca.crt`
</ca>
 
<cert>
`sed -n '/BEGIN/,$p' $KEYS_DIR/${CN}.crt`
</cert>
 
<key>
`cat $KEYS_DIR/${CN}.key`
</key>
END