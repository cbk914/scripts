#!/bin/bash
#strings /var/lib/redis/dump.rdb | grep admin

echo -n "New password? "
read -s PASSWORD
#echo $PASSWORD
MD5PWD=`echo -n $PASSWORD | md5sum|cut -d'-' -f 1`
#echo $MD5PWD|cut -d' ' -f 2
redis-cli ping
redis-cli SET ntopng.user.admin.password $MD5PWD
