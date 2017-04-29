#!/usr/bin/env python
#
# Copyright 2014 tigmi
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''A library that provides a Python interface to the Kubernetes API'''

from os.path import expanduser
import requests
import sys
import urllib
import urllib2
import urlparse
import urllib3
import json
#urllib3.disable_warnings()

from kubernetes import (__version__,
                        _FileCache,
                        simplejson,
                        KubernetesError,
                        PodList,
                        ReplicationControllerList,
                        ServiceList,
                        ReplicationController,
                        Pod,
                        Service,
                        Node,
                        ResourceType,
                        ReqNotSupportedError)

# A singleton representing a lazily instantiated FileCache.
DEFAULT_CACHE = object()
DEFAULT_CERT_PATH = expanduser("~") + "/.kube_cert"

class Api(object):
    '''A python interface into the Kubernetes API'''
    def __init__(self,
                base_url,
                cert_path=DEFAULT_CERT_PATH,
                token=None,
                input_encoding=None,
                request_headers=None,
                cache=DEFAULT_CACHE,
                debugHTTP=None,
                timeout=None):
        '''Instantiate a new kubernetes.Api object

        Args:
          input_encoding:
              The encoding used to encode input strings. [Optional]
          request_headers
              A dictionary of additional HTTP request headers. [Optional]
          cache:
              The cache instance to use. Defaults to DEFAULT_CACHE.
              Use None to disable caching. [Optional]
          base_url:
            The base URL to use to contact the kubernetes API.
            Defaults to https://10.245.1.2/api/v1beta2
          debugHTTP:
              Set to True to enable debug output from urllib2 when performing
            any HTTP requests.  Defaults to False. [Optional]
          timeout:
            Set timeout (in seconds) of the http/https requests. If None the
            requests lib default will be used.  Defaults to None. [Optional]
        '''
        self.SetCache(cache)
        self._urllib    =    urllib2
        self._input_encoding = input_encoding
        self._debugHTTP    =    debugHTTP
        self._timeout    =    timeout
        self.base_url = base_url
        self._cert = None
        self._ishttps = False

        if self.base_url.find('https') == 0:
            self._ishttps = True
            # check if the given credentials can be accessed and readable
            if not self._check_file_readable([cert_path]):
                raise KubernetesError({'message': "The given credentials files cannot be loaded"})
            self.SetCredentials(cert=cert_path)
            if request_headers is not None:
                request_headers.update({"Authorization":"Bearer %s" % token})
            else:
                request_headers = {"Authorization":"Bearer %s" % token}

        self._InitializeRequestHeaders(request_headers)
        self._InitializeUserAgent()
        self._InitializeDefaultParameters()

        if debugHTTP:
            import logging
            import httplib
            httplib.HTTPConnection.debuglevel = 1

            logging.basicConfig()
            logging.getLogger().setLevel(logging.DEBUG)
            requests_log = logging.getLogger("requests.packages.urllib3")
            requests_log.setLevel(logging.DEBUG)
            requests_log.propagate = True

    def _check_file_readable(self, path_list):
        import os
        import os.path

        for path in path_list:
            if not os.path.isfile(path) or not os.access(path, os.R_OK):
                return False
        return True

    def SetCredentials(self, cert):
        '''Set the credentials and https server for this instance
        '''
        self._cert = (cert)

    def DeleteService(self, name, namespace='default'):
        '''Delete a new Service'''

        url = ('%(base_url)s/namespaces/%(ns)s/services/%(name)s' %
               {"base_url":self.base_url, "ns":namespace, "name":name})
        json = self._RequestUrl(url, 'DELETE')
        if json.status_code not in [200, 404]:
            raise KubernetesError({'message': 'parsing error ['+simplejson.dumps(json.content)+']'})

    def DeletePods(self, name, namespace='default'):
        '''Delete a new Pod'''

        url = ('%(base_url)s/namespaces/%(ns)s/pods/%(name)s' %
               {"base_url":self.base_url, "ns":namespace, "name":name})
        json = self._RequestUrl(url, 'DELETE')
        if json.status_code not in [200, 404]:
            raise KubernetesError({'message': 'parsing error ['+simplejson.dumps(json.content)+']'})
        if json.status_code == 404:
            raise KubernetesError({'message': 'can not find the pod <{0}> in namespace <{1}>'.format(name, namespace)})

    def DeleteReplicationController(self, name, namespace='default'):
        '''Delete a new Service'''

        url = ('%(base_url)s/namespaces/%(ns)s/replicationcontrollers/%(name)s' %
               {"base_url":self.base_url, "ns":namespace, "name":name})
        json = self._RequestUrl(url, 'DELETE')
        if json.status_code not in [200, 404]:
            raise KubernetesError({'message': 'parsing error ['+simplejson.dumps(json.content)+']'})

    def CreateService(self, data, namespace='default'):
        '''Create a new Service'''

        url = ('%(base_url)s/namespaces/%(ns)s/services' %
               {"base_url":self.base_url, "ns":namespace})
        json = self._RequestUrl(url, 'POST', data)
        if json.status_code is not 201:
            raise KubernetesError({'message': 'parsing error ['+simplejson.dumps(json.content)+']'})
        result = self._ParseAndCheckKubernetes(json.content)
        return Service.NewFromJsonDict(result)

    def CreateReplicationController(self, data, namespace='default'):
        '''Create a new ReplicationController'''

        url = ('%(base_url)s/namespaces/%(ns)s/replicationcontrollers' %
               {"base_url":self.base_url, "ns":namespace})
        json = self._RequestUrl(url, 'POST', data)
        if json.status_code is not 201:
            raise KubernetesError({'message': 'parsing error ['+simplejson.dumps(json.content)+']'})
        result = self._ParseAndCheckKubernetes(json.content)
        return ReplicationController.NewFromJsonDict(result)

    def CreatePod(self, data, namespace='default'):
        '''Create a new Pod'''

        url = ('%(base_url)s/namespaces/%(ns)s/pods' %
               {"base_url":self.base_url, "ns":namespace})
        json = self._RequestUrl(url, 'PUT', data)
        if json.status_code is not 201:
            raise KubernetesError({'message': 'parsing error ['+simplejson.dumps(json.content)+']'})
        result = self._ParseAndCheckKubernetes(json.content)
        return Pod.NewFromJsonDict(result)

    def GetPod(self, name, namespace='default'):
        '''List the specific pod on this cluster'''

        # Make and send requests
        url = ('%(base_url)s/namespaces/%(ns)s/pods/%(name)s' %
               {"base_url":self.base_url, "ns":namespace, "name":name})
        json = self._RequestUrl(url, 'GET')
        if json.status_code == 404:
            #not exit, just return None
            return None
        data = self._ParseAndCheckKubernetes(json.content)
        return Pod.NewFromJsonDict(data)

    def SetNodeSchedulable(self, node_name, is_scheduable=True):
        ''' Make the node as unscheduable '''

        # Make and send requests
        url = ('%(base_url)s/nodes/%(node_name)s' %
               {"base_url":self.base_url, "node_name":node_name})

        if is_scheduable:
            data = '{"spec":{"unschedulable":false}}'
        else:
            data = '{"spec":{"unschedulable":true}}'

        json = self._RequestUrl(url, 'PATCH', data)
        if json.status_code is not 200:
            raise KubernetesError({'message': 'parsing error ['+simplejson.dumps(json.content)+']'})
        result = self._ParseAndCheckKubernetes(json.content)
        return Pod.NewFromJsonDict(result)

    def _gen_selector_str(self, dict):
        rc = ""
        for key, val in dict.items():
            rc += "%s=%s," % (key, val)

        return rc[:-1]

    def GetPods(self, namespace=None, selector={}):
        '''List all pods on this cluster'''

        # Make and send requests
        if namespace:
            url = ('%(base_url)s/namespaces/%(ns)s/pods' %
                {"base_url":self.base_url, "ns":namespace})
        else:
            url = '%s/pods' % self.base_url
        if len(selector):
            selector_str = self._gen_selector_str(selector)
            url = self._BuildUrl(url, extra_params={'labelSelector':selector_str})
        json = self._RequestUrl(url, 'GET')
        data = self._ParseAndCheckKubernetes(json.content)
        return PodList.NewFromJsonDict(data)

    def _HandleReplicationController(self, name, namespace, action, data_str=None):
        '''Retrieve the specific ReplicationController and convert to dict'''
        # Make and send requests
        url = ('%(base_url)s/namespaces/%(ns)s/replicationcontrollers/%(name)s' %
               {"base_url":self.base_url, "ns":namespace, "name":name})
        json = self._RequestUrl(url, action, data_str)
        return json

    def ResizeReplicationController(self, name, replicas, namespace='default'):
        '''Update an existing ReplicationController by given data'''
        #retrieve the specific replicationcontroller first
        json = self._HandleReplicationController(name=name,
                                                 action='GET',
                                                 namespace=namespace)
        if json.status_code == 404:
            #not exit, just return None
            return None
        if json.status_code is not 200:
            raise KubernetesError({'message': 'parsing error ['+simplejson.dumps(json.content)+']'})
        data = self._ParseAndCheckKubernetes(json.content)
        #update the value of replicas, note, for v1beta3 only
        data['spec']['replicas']=replicas
        json = self._HandleReplicationController(name=name,
                                                 action='PUT',
                                                 namespace=namespace,
                                                 data_str=simplejson.dumps(data))
        if json.status_code is not 200:
            raise KubernetesError({'message': 'parsing error ['+simplejson.dumps(json.content)+']'})
        result = self._ParseAndCheckKubernetes(json.content)
        return ReplicationController.NewFromJsonDict(result)

    def GetReplicationController(self, name, namespace='default'):
        '''Retrieve the specific replicationcontroller on this cluster'''
        json = self._HandleReplicationController(name=name,
                                                       action='GET',
                                                       namespace=namespace)
        if json.status_code == 404:
            #not exit, just return None
            return None
        data = self._ParseAndCheckKubernetes(json.content)
        return ReplicationController.NewFromJsonDict(data)

    def GetReplicationControllers(self, namespace=None):
        '''List all replicationcontrollers on this cluster'''
        # Make and send requests
        if namespace:
            url = ('%(base_url)s/namespaces/%(ns)s/replicationcontrollers' %
                {"base_url":self.base_url, "ns":namespace})
        else:
            url = '%s/replicationcontrollers' % self.base_url
        json = self._RequestUrl(url, 'GET')
        data = self._ParseAndCheckKubernetes(json.content)
        return ReplicationControllerList.NewFromJsonDict(data)

    def GetService(self, name, namespace='default'):
        '''List the specific service on this cluster'''

        # Make and send requests
        url = ('%(base_url)s/namespaces/%(ns)s/services/%(name)s' %
               {"base_url":self.base_url, "ns":namespace, "name":name})
        json = self._RequestUrl(url, 'GET')
        if json.status_code == 404:
            #not exit, just return None
            return None
        data = self._ParseAndCheckKubernetes(json.content)
        return Service.NewFromJsonDict(data)

    def GetServices(self, namespace=None):
        '''List all services on this cluster'''

        # Make and send requests
        if namespace:
            url = ('%(base_url)s/namespaces/%(ns)s/services' %
                {"base_url":self.base_url, "ns":namespace})
        else:
            url = '%s/services' % self.base_url
        json = self._RequestUrl(url, 'GET')
        data = self._ParseAndCheckKubernetes(json.content)
        return ServiceList.NewFromJsonDict(data)

    def GetNodes(self):
        url = ('%(base_url)s/nodes' % {"base_url":self.base_url})
        json = self._RequestUrl(url, 'GET')
        data = self._ParseAndCheckKubernetes(json.content)

        node_list = []
        for item in data['items']:
            node = Node(item)
            node_list.append(node)

        pod_list = self.GetPods()
        for pod in pod_list.Items:
            for node in node_list:
                if node.name == pod.NodeName:
                    node.pod_num += 1
                    node.mem_limit_used += pod.MemLimit

        return node_list

    def SetCache(self, cache):
        '''Override the default cache.  Set to None to prevent caching.

        Args:
          cache:
            An instance that supports the same API as the kubernetes._FileCache
        '''
        if cache == DEFAULT_CACHE:
            self._cache = _FileCache()
        else:
            self._cache = cache

    def _InitializeRequestHeaders(self, request_headers):
        if request_headers:
            self._request_headers = request_headers
        else:
            self._request_headers = {}

    def _InitializeUserAgent(self):
        user_agent = 'Python-urllib/%s (python-kubernetes/%s)' % \
            (self._urllib.__version__, __version__)
        self.SetUserAgent(user_agent)

    def _InitializeDefaultParameters(self):
        self._default_params = {}

    def SetUserAgent(self, user_agent):
        '''Override the default user agent.

        Args:
          user_agent:
              A string that should be send to the server as the user-agent.
        '''
        self._request_headers['User-Agent'] = user_agent

    def _Encode(self, s):
        if self._input_encoding:
            return unicode(s, self._input_encoding).encode('utf-8')
        else:
            return unicode(s).encode('utf-8')

    def _EncodeParameters(self, parameters):
        '''Return a string in key=value&key=value form

        Value of None are not included in the output string.

        Args:
         parameters:
             A dict of (key, value) tuples, where value is encoded as
             specified by self._encoding

        Returns:
         A URL-encoded string in "key=value&key=value" form
        '''
        if parameters is None:
            return None
        else:
            return urllib.urlencode(dict([(k, self._Encode(v)) for k, v in parameters.items() if v is not None]))


    def _BuildUrl(self, url, path_elements=None, extra_params=None):
        # Break url into constituent parts
        (scheme, netloc, path, params, query, fragment) = urlparse.urlparse(url)

        # Add any additional path elements to the path
        if path_elements:
            # Filter out the path elements that have a value of None
            p = [i for i in path_elements if i]
            if not path.endswith('/'):
                path += '/'
            path += '/'.join(p)

        # add any additional query parameters to the query string
        if extra_params and len(extra_params) > 0:
            extra_query = self._EncodeParameters(extra_params)
            # Add it to the existing query
            if query:
                query += '&' + extra_query
            else:
                query = extra_query

        # Return the rebuilt URL
        return urlparse.urlunparse((scheme, netloc, path, params, query, fragment))

    def _RequestUrl(self, url, verb, data=None, request_headers = None):
        '''Request a url.

            Args:
             url:
                 The web location we want to retrieve.
             verb:
                 POST, GET, PUT, DELETE.
             data:
                 a dict of (str, unicode) key/value pairs.

            Returns:
             A JSON object.
        '''
        headers = self._request_headers
        if headers and request_headers:
            headers.update(request_headers)
        elif headers is None:
            headers = request_headers

        if verb == 'POST':
            try:
                return requests.post(
                    url,
                    data=data,
                    auth=None,
                    timeout=self._timeout,
                    verify=self._cert,
                    headers=headers
                    )
            except requests.RequestException as e:
                raise KubernetesError(str(e))
        if verb == 'GET':
            try:
                return requests.get(
                    url,
                    auth=None,
                    timeout=self._timeout,
                    verify=self._cert,
                    headers=headers
                    )
            except requests.RequestException as e:
                raise KubernetesError(str(e))
        if verb == 'PUT':
            try:
                return requests.put(
                    url,
                    data=data,
                    auth=None,
                    timeout=self._timeout,
                    verify=self._cert,
                    headers=headers
                    )
            except requests.RequestException as e:
                raise KubernetesError(str(e))
        if verb == 'DELETE':
            try:
                return requests.delete(
                    url,
                    auth=None,
                    timeout=self._timeout,
                    verify=self._cert,
                    headers=headers
                    )
            except requests.RequestException as e:
                raise KubernetesError(str(e))
        if verb == 'PATCH':
            try:
                return requests.patch(
                    url,
                    data=data,
                    auth=None,
                    timeout=self._timeout,
                    verify=self._cert,
                    headers=headers
                    )
            except requests.RequestException as e:
                raise KubernetesError(str(e))
        return 0

    def _ParseAndCheckKubernetes(self, json):
        '''Try and parse the JSON returned from Kubernetes and return
        an empty dictionary if there is any error
        '''

        try:
            data = simplejson.loads(json)
        except ValueError:
            raise KubernetesError({'message': 'parsing error ['+json+']'})

        return data

    def AddLabel(self, resource_type, resource_name, labels, namespace = None):
        '''
        If the label already exists in the resource, its value will be replaced by new value.
        If the label does not exist in the resource, the label will be added.
        '''

        url = None
        if resource_type == ResourceType.Node:
            # Make and send requests
            url = ('%(base_url)s/nodes/%(node_name)s' %
                   {"base_url":self.base_url, "node_name":resource_name})
            data = {
                'metadata': {
                    'labels': labels
                }
            }
            reply = self._RequestUrl(url, 'PATCH', json.dumps(data), {'Content-Type': 'application/merge-patch+json'})
            if reply.status_code is not 200:
                raise KubernetesError({'message': 'parsing error ['+simplejson.dumps(reply.content)+']'})
        else:
            raise ReqNotSupported

    def RemoveLabel(self, resource_type, resource_name, label_list, namespace = None):
        '''
        If the label already exists in the resource, its value will be replaced by new value.
        If the label does not exist in the resource, the label will be added.
        '''

        url = None
        if resource_type == ResourceType.Node:
            # Make and send requests
            url = ('%(base_url)s/nodes/%(node_name)s' %
                   {"base_url":self.base_url, "node_name":resource_name})
            data = list()
            for label in label_list:
                data.append({ 'op': 'remove', 'path': '/metadata/labels/'+label })
            reply = self._RequestUrl(url, 'PATCH', json.dumps(data), {'Content-Type': 'application/json-patch+json'})
            if reply.status_code is not 200:
                raise KubernetesError({'message': 'parsing error ['+simplejson.dumps(reply.content)+']'})
        else:
            raise ReqNotSupported

