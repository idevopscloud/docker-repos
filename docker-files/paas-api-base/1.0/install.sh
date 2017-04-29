#!/bin/bash

apt-get update
apt-get install -y python-pip
apt-get install -y python-dev
pip install -v python-etcd flask flask-restful requests python-heatclient==0.3.0 python-keystoneclient==1.2.0 oslo.config==1.9.3 oslo.i18n==1.5.0 oslo.serialization==1.4.0 oslo.utils==1.4.0

rm -rf /var/cache/*
