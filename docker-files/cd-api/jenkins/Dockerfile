FROM ubuntu:14.04

RUN apt-get update \
      && apt-get install -y  python-dev python-setuptools \
      && easy_install flask flask-restful flask_httpauth jenkinsapi \
      && mkdir -p /ido

ADD cd-api /ido/cd-api
EXPOSE 23006

CMD ["bash", "-c", "/ido/cd-api/bin/start.sh"]
