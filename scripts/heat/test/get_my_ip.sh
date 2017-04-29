#!/bin/bash
export PATH=/sbin:/usr/sbin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin

get_my_ip()
{
    my_ip=$(ip route get 1.0.0.0 | head -1 | cut -d' ' -f8)
    if [ ! -n "$my_ip" ]; then  
      my_ip=$(ifconfig eth0 | grep -oP 'inet addr:\K\S+')
      if [ ! -n "$my_ip" ]; then
            my_ip=$(hostname -I|cut -d' ' -f1)
      fi
    fi

    echo $my_ip
}

echo $1
my_ip=$(get_my_ip)
echo $my_ip
