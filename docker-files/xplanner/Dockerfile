FROM ubuntu:14.04

RUN apt-get update \
      && apt-get install -y openjdk-6-jdk tomcat6 mysql-client-5.5

ADD xplanner-plus.war /
ADD bootstrap.sh xplanner-custom.properties /

CMD /bin/sh -c "/bootstrap.sh"

