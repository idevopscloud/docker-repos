#!/bin/bash
export PATH=/sbin:/usr/sbin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin

./build.sh 1
./paas-agent-up.sh 1
curl localhost:22305/api/v1.1/machine
