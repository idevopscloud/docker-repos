FROM shaddock/seed:latest 
MAINTAINER allen.gao

#install heat
RUN apt-get -y update
RUN apt-get install -y --force-yes heat-api heat-engine python-heatclient

ADD supervisord.conf /etc/supervisord.conf

ADD heat-start /usr/local/bin/
ADD configparse.py /usr/local/bin/
RUN chmod +x /usr/local/bin/heat-start
RUN chmod +x /usr/local/bin/configparse.py

#install python-kubernetes
ADD python-kubernetes /python-kubernetes
RUN cd /python-kubernetes && python setup.py install


#install heat kubernetes plugins
ADD heat-kubernetes-plugin /heat-kubernetes-plugin
RUN cd /heat-kubernetes-plugin/heat_kubernetes && python setup.py install


EXPOSE 8004

CMD ["heat-start"]
