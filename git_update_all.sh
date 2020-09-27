#!/bin/bash
echo "[+] Updating Github directories..."
echo "[+] =============================="
#find . -maxdepth 1 -type d -print -execdir echo git --git-dir={}/.git --work-tree=$PWD/{} fetch origin master:master \;
#content=`ls -l | grep '^d'`
#for dir in $content;
#do 
#	cd $dir; git pull; cd ..;
#done

for i in */.git; do ( echo $i; cd $i/..; git pull; ); done


echo "[+] Update finished"
exit 0

