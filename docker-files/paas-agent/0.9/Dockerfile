FROM ubuntu:14.04

RUN apt-get update \
      && apt-get install -y  python-dev python-setuptools \
      && easy_install flask flask-restful psutil requests httplib2 \
      && mkdir -p /ido

ADD code /ido/paas-agent
EXPOSE 12305

CMD ["bash", "-c", "/ido/paas-agent/bin/start.sh"]
