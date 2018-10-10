#!/bin/bash
strings /var/lib/redis/dump.rdb | grep admin

echo -n "Contraseña? "
read -s PWD
#echo $PWD
MD5PWD=`echo -n $PWD | md5sum|cut -d'-' -f 2`
#echo $MD5PWD|cut -d' ' -f 2
redis-cli ping
redis-cli SET ntopng.user.admin.password $MD5PWD
