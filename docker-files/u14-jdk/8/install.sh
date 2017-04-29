#!/bin/bash

apt-get update && apt-get install -y software-properties-common python-software-properties
add-apt-repository -y ppa:webupd8team/java
echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | /usr/bin/debconf-set-selections
apt-get update && apt-get install -y oracle-java8-installer oracle-java8-set-default

rm -rf /var/cache/*
