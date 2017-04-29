#!/bin/bash

workdir=/tmp/idevops/workdir/paas-api-docker
registry=aws-seoul.repo.idevopscloud.com:5000
package_server=http://172.31.0.11/idevops
version=""

usage()
{
    echo "build.sh [--registry] [--package-server] [-h] VERSION"
}

OPTS=`getopt -o "h" -l registry: -- "$@"`
if [ $? != 0 ]; then
    echo "Usage error"
    exit 1
fi
eval set -- "$OPTS"

while true ; do
    case "$1" in
        -h) usage; exit 0;; 
        --registry) registry=$2; shift 2;; 
        --package-server) package_server=$2; shift 2;; 
        --) shift; break;;
    esac
done

if [[ $# != 1 ]]; then
    usage
    exit 1
fi

version=$1
workdir="$workdir/$version-$(date +%m%d%H%M%S-%N)"

mkdir -p $workdir 2>&1>/dev/null
rm -r $workdir/* 2>&1>/dev/null
cp install.sh $workdir
cp Dockerfile $workdir
cp start.sh $workdir

cd $workdir
wget ${package_server}/paas-api/paas-api-${version}.tar.gz
gunzip paas-api-${version}.tar.gz
mv paas-api-${version}.tar paas-api.tar

wget ${package_server}/common/python-kubernetes-0.8.1.tar.gz
gunzip python-kubernetes-0.8.1.tar.gz
mv python-kubernetes-0.8.1.tar python-kubernetes.tar

docker build -t $registry/idevops/paas-api:$version ./

