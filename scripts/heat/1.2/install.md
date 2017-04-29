#1. install mysql(Master)
```
# docker pull mysql:5.5
mkdir -p /pdata/docker/mysql
docker run --name mysql \
  -v /pdata/docker/mysql:/var/lib/mysql \
  -e MYSQL_ROOT_PASSWORD=Letmein123 \
  -h mysql -d njuicsgz/mysql:5.5
```
#2. install keystone (Master，rerun该container会自动删除并重建DB)
```
docker run -d \
  --link mysql:mysql\
  -e OS_TENANT_NAME=admin \
  -e OS_USERNAME=admin \
  -e OS_PASSWORD=ADMIN_PASS \
  -p 35357:35357\
  -p 5000:5000 \
  --name keystone -h ${my_ip} njuicsgz/keystone:juno
```
HOSTNAME Must the IP of OS_SERVICE_ENDPOINT which will provice service: 'http://${KEYSTONE_HOST}:35357/v2.0' to enable external access by host ip and port
# Verify
```
docker exec -t -i keystone bash
cd /root
source admin-openrc.sh
keystone user-list
```

PS：如果配置HOSTNAME=10.2.240.12，'http://10.2.240.12:35357/v2.0'，则该IP在container内外部都可以访问。
#3. install rabbitmq (与heat同在Master)
```
$docker run -d \
    --hostname rabbitmq \
    --name rabbitmq \
    -e RABBITMQ_DEFAULT_PASS=Letmein123 \
    njuicsgz/rabbitmq:3.6.1
```
#4. install heat
```
mkdir -p /pdata/docker/heat
# You MUST write k8s certification into this file
touch /pdata/docker/heat/.kube_cert
docker run \
  -p 8004:8004 \
  --link mysql:mysql\
  --link rabbitmq:rabbitmq\
  --link keystone:keystone\
  -v /var/log/heat:/var/log/heat \
  -v /pdata/docker/heat/:/root \
  --hostname heat \
  --name heat \
  -e KEYSTONE_HOST_IP=${my_ip} \
  -e HOST_IP=heat \
  -e MYSQL_HOST_IP=mysql \
  -e MYSQL_USER=root \
  -e MYSQL_PASSWORD=Letmein123 \
  -e ADMIN_PASS=ADMIN_PASS \
  -e RABBIT_HOST_IP=rabbitmq \
  -e RABBIT_PASS=Letmein123 \
  -e HEAT_PASS=Letmein123 \
  -e HEAT_DBPASS=Letmein123 \
  -e HEAT_DOMAIN_PASS=Letmein123 \
  -e ETC_HOSTS='172.30.10.185 dev.k8s.paas.ndp.com' \
  -d njuicsgz/heat:kilo-k8s-1.0.6
```
```
PS: 
1. MySQL可以使用单独可路由的外部DB，此时不在需要--link mysql:mysql
2. 创建之后，heat的endpoint将会是：--publicurl http://${KEYSTONE_HOST_IP}:8000/v1
3. 需要将所需访问k8s的根证书放在/pdata/docker/heat/.kube_cert中，否则heat无法访问k8s
```
# Verify
```
# heat resource-type-list | grep Google
| GoogleInc::Kubernetes::ReplicationController |
| GoogleInc::Kubernetes::Service               |

# heat stack-list
+--------------------------------------+------------+-----------------+----------------------+
| id                                   | stack_name | stack_status    | creation_time        |
+--------------------------------------+------------+-----------------+----------------------+
| 1824a6c4-09bf-41ba-a455-5c18ce2d39a8 | kk3        | CREATE_COMPLETE | 2016-03-17T08:49:14Z |
+--------------------------------------+------------+-----------------+----------------------+
# heat stack-delete kk3
+--------------------------------------+------------+--------------------+----------------------+
| id                                   | stack_name | stack_status       | creation_time        |
+--------------------------------------+------------+--------------------+----------------------+
| 1824a6c4-09bf-41ba-a455-5c18ce2d39a8 | kk3        | DELETE_IN_PROGRESS | 2016-03-17T08:49:14Z |
+--------------------------------------+------------+--------------------+----------------------+
```
