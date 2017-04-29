#!/bin/bash
export PATH=/sbin:/usr/sbin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin


get_repo()
{
    if (( $# != 1 )); then
        echo "usage:    $0 repo(1:mainland, 2:oversea)"
        echo "e.g:      $0 mainland"
        exit 0
    fi

    repo=idevopscloud

    if [[ "$1" == "1" ]]; then
        repo=index.idevopscloud.com:5000/idevops
    elif [[ "$1" == "2" ]]; then
        repo=idevopscloud
    else
        echo "error repo type"
        exit 1
    fi
}


wait_for_service_ready()
{
  local PORT=$1
  attempt=0
  while true; do
    local ok=1
    curl --connect-timeout 3 http://localhost:$PORT > /dev/null 2>&1 || ok=0
    if [[ ${ok} == 0 ]]; then
      if (( attempt > 10 )); then
        echo "failed to start $PORT on localhost." 
        exit 1
      fi
    else
        echo "Attempt $(($attempt+1)): $PORT running"
      break
    fi
    echo "Attempt $(($attempt+1)): $PORT not working yet"
    attempt=$(($attempt+1))
    sleep 3 
  done
}

get_repo $*
img=${repo}/cd-api:1.0.1
docker pull $img
docker rm -vf cd-api
docker run -d -e jenkins_addr=http://172.30.80.10:28080 \
	-p 23006:23006 --name=cd-api $img

wait_for_service_ready 23006

