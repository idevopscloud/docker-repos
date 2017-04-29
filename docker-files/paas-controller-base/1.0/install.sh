#!/bin/bash

apt-get update
apt-get install -y python-pip
apt-get install -y python-dev
pip install -v python-etcd eventlet==0.19.0 greenlet==0.4.10 requests==2.11.1 httplib2

rm -rf /var/cache/*
