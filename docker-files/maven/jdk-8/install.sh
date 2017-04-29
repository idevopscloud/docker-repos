#!/bin/bash

cd /tmp
wget http://apache.fayea.com/maven/maven-3/3.0.5/binaries/apache-maven-3.0.5-bin.tar.gz
tar -xzvf apache-maven-3.0.5-bin.tar.gz
cp -r apache-maven-3.0.5 /usr/share/maven 
update-alternatives --install /usr/bin/mvn mvn /usr/share/maven/bin/mvn 1
rm -rf /tmp/*
