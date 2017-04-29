#!/bin/bash
export PATH=/sbin:/usr/sbin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin

export WORKDIR=$( cd ` dirname $0 ` && pwd )
cd "$WORKDIR" || exit 1

pull_imgs(){
    docker pull $img > /dev/null
}

rm_old_contains(){
    containers=`docker ps -a | egrep "${cname}" | awk '{print $1}'`
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

img=index.idevopscloud.com:5000/library/magento:1.7.0.2
cname=ido-magento

#pull_imgs
rm_old_contains

docker run -d \
	-e MYSQL_HOST=172.30.80.10 \
	-e MYSQL_PORT=3307 \
	-e MYSQL_ROOT_PWD=Letmein123 \
	-e SERVICE_ADDR=http://172.30.80.10:40081 \
	-p 40081:80 \
	--name=${cname} $img

wait_for_service_ready 40081
