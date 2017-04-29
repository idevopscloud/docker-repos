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
  attempt=0
  while true; do
	rsp_code=$(curl -o /dev/null -s -m 10 --connect-timeout 10 -w %{http_code} http://localhost:28080/login)
    if [[ ${rsp_code} != "200" ]]; then
      if (( attempt > 10 )); then
        echo "failed to start Jenkins."
        exit 1
      fi
    else
        echo "Attempt $(($attempt+1)): Jenkins is ready."
      break
    fi
    echo "Attempt $(($attempt+1)): Jenkins not ready yet."
    attempt=$(($attempt+1))
    sleep 5
  done
}

import_job()
{
  local job_name=$1
  attempt=0
  cmd=create-job
  if [ -f "${PERSIST_DISK}/jobs/${job_name}/config.xml" ]; then
      cmd=update-job
  fi

  while true; do
    docker exec -it ${cname} \
        bash -c "java -jar /var/jenkins_home/war/WEB-INF/jenkins-cli.jar -s http://localhost:8080 ${cmd} ${job_name} < /tmp/${job_name}_config.xml"
    local ret=$?
    if [[ ${ret} != 0 ]]; then
      if (( attempt > 10 )); then
        echo "failed to import job."
        exit 1
      fi
    else
        echo "Attempt $(($attempt+1)): ok to import job: $job_name"
      break
    fi
    echo "Attempt $(($attempt+1)): failed to import job."
    attempt=$(($attempt+1))
    sleep 5
  done
}

jenk_config(){
    docker exec -it ${cname} \
        bash -c "cp /tmp/config.xml /var/jenkins_home && curl http://localhost:8080/reload -X POST"
}

ido_registry_login(){
    docker exec -it ${cname} \
        bash -c 'sudo docker login -u read_only -p "d[4|_Gj]jKx:JG" -e cd@idevopscloud.com index.idevopscloud.com:5000'
}

get_repo $*
cname=platform-jenkins
img=${repo}/${cname}:1.0.1

PERSIST_DISK=/mnt/master-pd/docker/var/jenkins_home
mkdir -p ${PERSIST_DISK}
chmod 777 -R ${PERSIST_DISK}

docker pull $img > /etc/null
docker rm -vf ${cname}
docker run -d \
    -v ${PERSIST_DISK}:/var/jenkins_home \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v $(which docker):/usr/bin/docker \
    -v /lib/x86_64-linux-gnu/libapparmor.so.1:/lib/x86_64-linux-gnu/libapparmor.so.1:ro \
    -e JAVA_OPTS=" -Xmx1024m -Xms1024m -Xmn512m " \
    -m 1400m \
    -p 28080:8080 --name=${cname} $img 

wait_for_service_ready
import_job base_img
import_job comp_img
import_job push_img
jenk_config
ido_registry_login
