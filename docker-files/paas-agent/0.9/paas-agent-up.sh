#!/bin/bash
export PATH=/sbin:/usr/sbin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin

export WORKDIR=$( cd ` dirname $0 ` && pwd )
cd "$WORKDIR" || exit 1

pull_imgs(){
    docker pull $img > /dev/null
}

rm_old_contains(){
    containers=`docker ps -a | egrep "${paas_agent_cname}" | awk '{print $1}'`
    for c in $containers; do 
        echo "removing container: $c"
        docker rm -vf $c > /dev/null
    done
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
        echo "Attempt $(($attempt+1)) [$PORT running]"
      break
    fi
    echo "Attempt $(($attempt+1)): [$PORT not working yet]"
    attempt=$(($attempt+1))
    sleep 3 
  done
}

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

get_repo $*
img=${repo}/paas-agent:0.9.1
paas_agent_cname=ido-paas-agent
persist_dir=/mnt/master-pd/docker/paas-agent/etc/conf

pull_imgs
rm_old_contains
mkdir -p $persist_dir && cp ${WORKDIR}/platform.json $persist_dir/platform.json

docker run -d \
	-v /proc:/host/proc:ro \
	-v /sys:/host/sys:ro \
	-v /:/rootfs:ro \
	-v $persist_dir:/ido/paas-agent/conf \
	-p 22305:12305 \
	--name=${paas_agent_cname} $img

wait_for_service_ready 22305
