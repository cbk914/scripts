#!/bin/bash

set -e

## Alternative 1
# Key server
alternative1() {
	KEY_SRV=${KEY_SRV:-"keyserver.ubuntu.com"}
	#GPG_KEY="7D8D0BF6"
	GPG_KEY="ED444FF07D8D0BF6"
	# kali-archive-keyring
	KEYRING=/usr/share/keyrings/kali-archive-keyring.gpg
	# Instalar certificados
	if [ ! -f $KEYRING ]; then
	  GNUPGHOME="$(mktemp -d)"
	  export GNUPGHOME
	  gpg --keyring=$KEYRING --no-default-keyring --keyserver-options \
		timeout=10 --keyserver "$KEY_SRV" --receive-keys $GPG_KEY
	  rm -rf "${GNUPGHOME}"
	fi
}

## Alternative 2 ( kali-docker based - donwload large file)
# Install Kali archive keyring
alternative2() {
	KEYRING_PKG_URL=$(wget -nv -O - \
			https://http.kali.org/kali/dists/kali-rolling/main/binary-amd64/Packages.gz \
			| gzip -dc | grep ^Filename: | grep kali-archive-keyring | head -n 1 | awk '{print $2}')
	KEYRING_PKG_URL="https://http.kali.org/kali/$KEYRING_PKG_URL"
	wget -nv "$KEYRING_PKG_URL"
	dpkg -i kali-archive-keyring_*_all.deb
	rm kali-archive-keyring_*_all.deb
}

## Alternative 3
alternative3() {
	keyring_url="http://http.kali.org/pool/main/k/kali-archive-keyring/"
	keyring_file=$(curl -s -k $keyring_url | grep -oe "kali*.*all.deb" | sed -e 's/.*">//')
	wget -nv $keyring_url/"$keyring_file"
	dpkg -i "$keyring_file"
	rm -f "$keyring_file"
}

## Alternative 4
alternative4() {
	#apt-get install -y git make jetring
	git clone https://gitlab.com/kalilinux/packages/kali-archive-keyring.git
	cd kali-archive-keyring
	make
	make install
	cd ..
	rm -rf kali-archive-keyring
}

# Benchmark
benchmark() {
	for n in 1 2 3 4; do
		time alternative$n
		echo -e "Alternative $n \n"
	done
	exit 0
}

[ -n $1 ] && benchmark
alternative$1
