#!/bin/bash
export PATH=/sbin:/usr/sbin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin


get_repo()
{
    if (( $# != 1 )); then
        echo "usage:    $0 repo(1:mainland, 2:oversea)"
        echo "e.g:      $0 2"
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

pull_imgs(){
    imgs="$wx_api_img $mysql_img"
    for img in $imgs;do
        docker inspect $img 2>&1 > /dev/null
        # Force pull image always to use latest version
        if (( 8888 != $? )); then
                echo "pulling $img..."
                docker pull $img > /dev/null
        fi
    done
}

rm_old_contains(){
    containers="${wx_api_name} ${mysql_name}"
    for c in $containers; do 
        docker rm -f $c > /dev/null 2>&1
    done
}

install_mysql()
{
    mkdir -p ${PERSIST_DISK}/docker/${mysql_name}
    docker run --name ${mysql_name} -h ${mysql_name} \
        -v ${PERSIST_DISK}/docker/${mysql_name}:/var/lib/mysql \
        -e MYSQL_ROOT_PASSWORD=Letmein123 \
        -p 23301:3306 \
        -d ${mysql_img}
    echo 'sleep 5s to ensure mysql is ready'
    sleep 5 
    echo 'intalled mysql'
}


install_wx_api()
{
    docker run -d \
        --link ${mysql_name}:${mysql_name} \
        -e MYSQL_HOST_IP=${mysql_name} \
        -e MYSQL_PORT=3306 \
        -e MYSQL_USER=root \
        -e MYSQL_PASSWORD=Letmein123 \
        -v ${log_dir}:/ido/log \
        -p 52001:52001 \
        --name ${wx_api_name} -h ${wx_api_name} ${wx_api_img}
}


get_repo $*

wx_api_img="${repo}/ido-wx-api:1.0"
wx_api_name="ido-wx-api"
mysql_img="${repo}/mysql:5.5"
mysql_name="ido-wx-api-mysql"


my_ip=$(ip route get 1.0.0.0 | head -1 | cut -d' ' -f8)
PERSIST_DISK=/mnt/master-pd
log_dir="${PERSIST_DISK}/docker/${wx_api_name}/log"


pull_imgs
rm_old_contains
install_mysql
install_wx_api
