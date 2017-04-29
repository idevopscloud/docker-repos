### 环境要求
>* docker 1.8.3+

### Feature
>* 支持Master/Slave集群
>* 支持Jobs的并发处理

### installation

**Build and Start the container**
```
./jenkins_restart.sh
```
或者
```
$ docker build -t myjenk .

$ docker run -d -v /var/run/docker.sock:/var/run/docker.sock -v $(which docker):/usr/bin/docker -p 8080:8080 --name=myjenk njuicsgz/myjenk

$ docker exec -it myjenk bash -c "java -jar /var/jenkins_home/war/WEB-INF/jenkins-cli.jar -s http://localhost:8080 create-job app_img < /tmp/app_img_config.xml"
```

### 通过API调用Jenkins Demo
```
# docker images | grep my_img | grep 1.0.3
# curl -X POST http://172.30.80.65:8080/job/xxxx/build --data-urlencode json='{"parameter": [{"name":"run_img", "value":"ubuntu:14.04"}, {"name":"img_tag","value":"1.0.3"}, {"name":"git_addr", "value":"https://njuicsgz:Letmein123@bitbucket.org/idevops/test.git"}]}'
# docker images | grep my_img | grep 1.0.3
localhost:5000/my_img   1.0.3               66b83cadb446        About a minute ago   196.6 MB
```

### 配置Jenkins集群
* “Jenkins” -> “系统管理” -> “节点管理” -> “新建节点”
* 输入远程执行目录、SSH的用户名、密码
