#!/bin/bash
export PATH=/sbin:/usr/sbin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin
export WORKDIR=$( cd ` dirname $0 ` && pwd )

cd $WORKDIR
bash ../../docker-files/jenkins/1.6/jenkins_restart.sh
bash ../../docker-files/cd-api/jenkins/restart.sh
