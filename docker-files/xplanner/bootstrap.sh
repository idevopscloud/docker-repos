#!/bin/bash
export PATH=/sbin:/usr/sbin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin

dir_xplanner=/var/lib/tomcat6/webapps/xplanner-plus
mkdir -p $dir_xplanner
cd $dir_xplanner && jar xf /xplanner-plus.war
cp /xplanner-custom.properties $dir_xplanner/WEB-INF/classes/xplanner-custom.properties

# init db
    mysql \
        -h${MYSQL_HOST_IP} \
        -u${MYSQL_USER} \
        -p${MYSQL_PASSWORD} \
        -e "CREATE DATABASE IF NOT EXISTS xplanner DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;";

    mysql \
        -h${MYSQL_HOST_IP} \
        -u${MYSQL_USER} \
        -p${MYSQL_PASSWORD} \
        -e "grant all privileges on xplanner.* to xplanner@'localhost' identified by 'xplanner' with grant option;"

    mysql \
        -h${MYSQL_HOST_IP} \
        -u${MYSQL_USER} \
        -p${MYSQL_PASSWORD} \
        -e "grant all privileges on xplanner.* to xplanner@'%' identified by 'xplanner' with grant option;"

    mysql \
        -h${MYSQL_HOST_IP} \
        -u${MYSQL_USER} \
        -p${MYSQL_PASSWORD} \
	-e "flush privileges;"

service tomcat6 start
while true; do sleep 1000; done

