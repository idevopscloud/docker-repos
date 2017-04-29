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

get_repo $*

docker build -t ${repo}/platform-jenkins:1.0.1 .
docker push ${repo}/platform-jenkins:1.0.1
