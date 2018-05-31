#!/bin/bash
# Licensed under WTFPL 2018 by cbk914@riseup.net
# Version 0.1.30b

clear
MAGENTA="\e[35m"
RED="\e[31m"
LIGHTGREEN="\e[92m"
LIGHTYELLOW="\e[93m"
LIGHTCYAN="\e[96m"
NOCOLOR="\e[0m"
echo $MAGENTA"FUZZING SURICATA INSTALLATION"
echo $MAGENTA"============================="
echo ""
echo $RED"Execute this script as root"
echo ""
echo $LIGHTGREEN"[*] Installing pre-requisites..."$NOCOLOR

# Reset files and directories
sh revert.sh 2>&1

# Install dependencies
apt update && apt upgrade
apt install build-essential clang gcc gdb llvm
sleep 3

echo $LIGHTGREEN"[+] Creating directories..."$NOCOLOR
cd /usr/local/bin
mkdir afl
mkdir Suricata_AFL
mkdir Suricata_AFL/fuzzing
mkdir Suricata_AFL/fuzzing/input
mkdir Suricata_AFL/fuzzing/sync
mkdir Suricata_AFL/fuzzing/AFL_testcases
sleep 3

echo $LIGHTGREEN"[+] Downloading and installing American Fuzzy Lop..."$NOCOLOR
cd /usr/local/bin/afl
wget http://lcamtuf.coredump.cx/afl/releases/afl-latest.tgz
tar xzf afl-latest.tgz
mv /usr/local/bin/afl/afl-2.52b/* /usr/local/bin/afl/
rm afl-latest.tgz
rmdir /usr/local/bin/afl/afl-2.52b/
make
sleep 3

echo $LIGHTGREEN"[+] Optimizing fuzzing environment..."$NOCOLOR
cd /usr/local/bin/afl/llvm_mode
LLVM_CONFIG=llvm-config-3.4 make
cd /usr/local/bin/afl
make install
sleep 3

echo $LIGHTGREEN"[+] Preparing random input for AFL..."$NOCOLOR
dd if=/dev/random of=/usr/local/bin/Suricata_AFL/fuzzing/input/rand bs=64 count=1
sleep 3

echo $LIGHTGREEN"[+] Downloading and installing AFL extras..."$NOCOLOR
cd /usr/local/bin/afl
git clone https://github.com/rc0r/afl-utils
sleep 3

echo $LIGHTGREEN"[+] Optimizing performance..."$NOCOLOR
cd /sys/devices/system/cpu
echo performance | tee cpu*/cpufreq/scaling_governor
# Output coredumps as files
echo core > /proc/sys/kernel/core_pattern
sleep 3

echo $LIGHTGREEN"[+] Downloading and installing Suricata stable..."$NOCOLOR
cd /usr/local/bin/Suricata_AFL
git clone https://github.com/OISF/suricata.git
sleep 3

echo $LIGHTGREEN"[+] Compiling and instrumenting Suricata..."$NOCOLOR
cd /usr/local/bin/Suricata_AFL/suricata/
export ac_cv_func_realloc_0_nonnull=yes
export ac_cv_func_malloc_0_nonnull=yes
bash autogen.sh
CC=/usr/local/bin/afl-clang-fast CFLAGS="-fsanitize=address -fno-omit-frame-pointer" ./configure --enable-afl --disable-shared
make
sleep 3

echo $LIGHTGREEN"[+] Creating virtual environment..."$NOCOLOR
cd /usr/local/bin/afl/afl-utils
virtualenv -p python3 venv
source venv/bin/activate
sleep 3

echo $LIGHTGREEN"[+] Installing exploitable in virtualenv..."$NOCOLOR
python setup.py install
echo $RED"To revert changes simply delete 'venv' directory..."$NOCOLOR
sleep 3

echo $LIGHTGREEN"[+] Testing virtualenv..."$NOCOLOR
python setup.py test
sleep 3

echo $LIGHTGREEN"[+] Downloading example testcases..."$NOCOLOR
cd /usr/local/bin/Suricata_AFL/fuzzing/AFL_testcases
wget http://lcamtuf.coredump.cx/afl/demo/afl_testcases.tgz
tar xzf ./afl-testcases.tgz
rm ./afl-testcases.tgz
sleep 3

echo $LIGHTGREEN"[*] All processes finished successfully!!"
echo ""
echo $LIGHTYELLOW"Fuzzing Suricata environment installed at /usr/local/bin/Suricata_AFL/"
echo "You can now start fuzzing Suricata with:"
echo $LIGHTCYAN"<Master>"
echo "/usr/local/bin/afl-fuzz -t 1000 -m none -i fuzzing/input/ -o fuzzing/sync/ -M fuzzer01 -- Suricata_AFL/suricata/src/suricata --afl-rules=@@"
echo "...and for each <Slave>"
echo "/usr/local/bin/afl-fuzz -t 1000 -m none -i fuzzing/input/ -o fuzzing/sync/ -S fuzzer02 -- Suricata_AFL/suricata/src/suricata --afl-rules=@@"
echo $LIGHTYELLOW"You can check status with 'afl-whatsup'"
echo "And reproduce obtained crashes loading them as args to suricata from gdb"
echo "Analyze obtained crashes with:"
echo $LIGHTCYAN"$ afl-collect -d crashes.db -e gdb_script -r -rr ./output_crash_dir_from_afl_fuzz ./afl_collect_output_dir -j 8 -- /path/to/target"
echo $LIGHTYELLOW"For better inspection you can also install some gdb extensions like 'pwndbg' and 'gdb-peda'"
echo $NOCOLOR
sleep 3

# Suricata options for AFL:
#
# app-layer:
# --afl-http-request
# --afl-http
# --afl-tls-request
# --afl-tls
# --afl-dns-request
# --afl-dns
# --afl-ssh-request
# --afl-ssh
# --afl-ftp-request
# --afl-ftp
# --afl-smtp-request
# --afl-smtp
# --afl-smb-request
# --afl-smb
# --afl-modbus-request
# --afl-modbus
#
# packet-decoders:
# --afl-decoder-ppp
#
# misc:
# --afl-mime
# --afl-der
# --afl-rules

exit 0
