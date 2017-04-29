#!/bin/bash
export PATH=/sbin:/usr/sbin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin

pull_imgs(){
    imgs="$img "
    for img in $imgs;do
        docker inspect $img 2>&1 > /dev/null
        if (( 0 != $? )); then
                echo "pulling $img..."
                docker pull $img > /dev/null
        fi
    done
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

img=index.idevopscloud.com:5000/idevops/paas-agent:0.8
paas_agent_cname=ido-paas-agent
pull_imgs
rm_old_contains
docker run -d \
	-p 22305:12305 --name=${paas_agent_cname} $img

wait_for_service_ready 22305
