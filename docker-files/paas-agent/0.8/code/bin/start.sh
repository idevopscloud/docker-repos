#!/bin/bash
export PATH=/sbin:/usr/sbin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin
export WORKDIR=$( cd ` dirname $0 ` && pwd )

cd $WORKDIR

docker0=$(ip route show | awk '/default/ {print $3}')

python ../src/paas-agent.pyc ${docker0} 12305
