FROM njuicsgz/heat:kilo-k8s-1.0.6 
MAINTAINER allen.gao


ADD supervisord.conf /etc/supervisord.conf
ADD heat-start /usr/local/bin/

#install heat kubernetes plugins
ADD heat-kubernetes-plugin /heat-kubernetes-plugin
RUN chmod +x /usr/local/bin/heat-start && cd /heat-kubernetes-plugin/heat_kubernetes && python setup.py install

CMD ["heat-start"]
