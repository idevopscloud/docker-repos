#!/bin/bash
export PATH=/sbin:/usr/sbin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin
export WORKDIR=$( cd ` dirname $0 ` && pwd )

cd $WORKDIR

python ../src/cd_api.pyc ${jenkins_addr}
