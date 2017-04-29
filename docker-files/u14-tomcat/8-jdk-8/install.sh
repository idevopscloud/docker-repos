#!/bin/bash

TOMCAT_VERSION="8.0.36"

cd /tmp
wget https://www.apache.org/dist/tomcat/tomcat-8/v$TOMCAT_VERSION/bin/apache-tomcat-${TOMCAT_VERSION}.tar.gz
tar -xzvf apache-tomcat-${TOMCAT_VERSION}.tar.gz
cp -r apache-tomcat-${TOMCAT_VERSION} /opt/tomcat
rm -rf /tmp/*

