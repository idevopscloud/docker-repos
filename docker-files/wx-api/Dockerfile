FROM ubuntu:14.04

RUN apt-get update \
	&& apt-get install -y python-dev libffi-dev libssl-dev python-setuptools libmysqld-dev python-pip mysql-client-core-5.5 \
	&& easy_install flask flask-httpauth eventlet sqlalchemy mysql-python \
	&& pip install PyOpenSSL flask-restful \
	&& mkdir -p /ido

ADD src /ido

CMD /bin/sh -c "/ido/bin/start.sh"
