#!/bin/bash
# Fri Dec  4 11:04:15 CET 2009 <aramosf @ unsec.net>
# http://www.securitybydefault.com
# Pastebin monitor
#

STATICSLEEP="15"
DYNAMICSLEEP="1"
DIR="."
URL="http://pastebin.com/"
DWN="pastebin.php?dl="



while true; do
 DOWNLOAD=0
 DATE=`date '+%H:%M:%S %d-%m-%Y'`
 DATEDIR=`echo $DATE|awk '{ print $2}'`
 if [ ! -d ${DIR}/${DATEDIR} ]; then 
   echo "$DATE - Creating new download directory ${DIR}/$DATEDIR"
   mkdir -p ${DIR}/${DATEDIR}
 fi
 HTML=`curl -s "$URL"`
 PASTES=`echo "$HTML"|grep '<a href="http://pastebin.com/'|sed -e 's|.*.com/\(.*\)">.*|\1|g'`
 for file in `echo "$PASTES"`; do
  if [ ! -f ${DIR}/${DATEDIR}/${file} ]; then
	echo "$DATE - Downloading $file ${URL}${DWN}${file}"
	curl -s "${URL}${DWN}${file}" -o "${DIR}/${DATEDIR}/${file}"
	DOWNLOAD=$(( $DOWNLOAD + 1 ))
  fi
 done
 if [ $DYNAMICSLEEP -eq 1 ]; then
   if [ $DOWNLOAD -eq 0  ]; then SLEEP="65"; fi
   if [ $DOWNLOAD -gt 0  ]; then SLEEP="45"; fi
   if [ $DOWNLOAD -gt 3  ]; then SLEEP="15"; fi
   if [ $DOWNLOAD -gt 5  ]; then SLEEP="5"; fi
   if [ $DOWNLOAD -gt 8 ]; then SLEEP="2"; fi
 else
   SLEEP=$STATICSLEEP
 fi 
 echo "$DATE - Sleeping ZzZzz (${SLEEP}s) zZzZzz"
 sleep $SLEEP
done




