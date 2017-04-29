#!/bin/bash
export PATH=/sbin:/usr/sbin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin
export WORKDIR=$( cd ` dirname $0 ` && pwd )

cd "$WORKDIR" || exit 1


python manager.pyc ${MYSQL_HOST_IP} ${MYSQL_PORT}
