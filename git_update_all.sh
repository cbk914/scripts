#!/bin/bash
echo "[+] Updating Github directories..."
echo "[+] =============================="

for i in */.git; do ( echo $i; cd $i/..; git branch; git pull; ); done


echo "[+] Update finished"
exit 0

