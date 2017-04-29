#!/bin/bash
export PATH=/sbin:/usr/sbin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin


get_repo()
{
    if (( $# != 1 )); then
        echo "usage:    $0 repo(mainland, oversea)"
        echo "e.g:      $0 mainland"
        exit 0
    fi

    repo=idevopscloud

    if [[ "$1" == "mainland" ]]; then
        repo=index.idevopscloud.com:5000/idevops
    elif [[ "$1" == "oversea" ]]; then
        repo=idevopscloud
    else
        echo "error repo type"
        exit 1
    fi
}

wait_for_service_ready()
{
  local port=$1
  attempt=0
  while true; do
	rsp_code=`curl -o /dev/null -s -m 10 --connect-timeout 10 -w %{http_code} http://localhost:${port}/xplanner-plus/do/login`
    if [[ ${rsp_code} != "200" ]]; then
      if (( attempt > 10 )); then
        echo "failed to start xplanner-plus."
        exit 1
      fi
    else
      echo "Attempt $(($attempt+1)): xplanner-plus is ready"
      break
    fi
    echo "Attempt $(($attempt+1)): xplanner-plus not ready yet"
    attempt=$(($attempt+1))
    sleep 5
  done
}

install_mysql()
{
    local mysql_img="${repo}/mysql:5.5"
    echo "pulling ${mysql_img}..."
    docker pull ${mysql_img} > /dev/null

    echo 'kill old mysql container if it exist'
    docker rm -f mysql_xplanner
    mkdir -p ${PERSIST_DISK}/docker/mysql_xplanner
    docker run --name mysql_xplanner -h mysql_xplanner \
        -v ${PERSIST_DISK}/docker/mysql_xplanner:/var/lib/mysql \
        -e MYSQL_ROOT_PASSWORD=Letmein123 \
        -d ${mysql_img}
    echo 'sleep 5s to ensure mysql is ready'
    sleep 5 
    echo 'intalled mysql'
}

install_xplanner()
{
    local xplanner="${repo}/xplanner-plus:1.0b3"
    echo "pulling ${xplanner}..."
    docker pull ${xplanner} > /dev/null

    docker rm -f xplanner
    docker run -d \
        --link mysql_xplanner:mysql_xplanner\
        -e MYSQL_HOST_IP=mysql_xplanner \
        -e MYSQL_USER=root \
        -e MYSQL_PASSWORD=Letmein123 \
        -p 28081:8080\
        --name xplanner -h xplanner ${xplanner}
    wait_for_service_ready 28081
}

PERSIST_DISK=/mnt/master-pd

get_repo $*

install_mysql
install_xplanner
