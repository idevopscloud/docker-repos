#!/usr/bin/env python

import psutil
import os
import re
import sys
import time
import json
from flask_restful import Resource
from flask import Flask, g
import flask
from flask_restful import Resource, Api
import sys 
import requests
import copy
import datetime
import getopt

from multiprocessing import Process
from multiprocessing import Manager

import node as node_v1_1
import utils

cadvisor_IP = '127.0.0.1'
cadvisor_port = 4194
port = 12305
node = None


class Node:
    def __init__(self, name):
        mem =  psutil.virtual_memory()
        self.name = name
        self.num_cores = psutil.cpu_count()
        self.mem_total = mem.total

    def dump_as_dict(self):
        load1, load5, load15 = os.getloadavg()
        mem =  psutil.virtual_memory()
        return {
            'name': self.name,
            'num_cores': self.num_cores,
            'mem_total': self.mem_total,
            'mem_available': mem.available,
            'load1': load1,
            'load5': load5,
            'load15': load15
        }

class ReosurcePodContainerList(Resource):
    def get(self):
        url = 'http://{}:{}/api/v1.2/docker/'.format(cadvisor_IP, cadvisor_port)
        reply = requests.get(url)
        if reply.status_code != 200:
            response = flask.make_response(json.dumps({'kind': 'Status', 'code': reply.status_code, 'message': 'kubelet error'}))
            return response

        reply_data = {}
        container_json = reply.json()
        for key, container in container_json.items():
            try:
                if 'io.kubernetes.pod.name' not in container['spec']['labels']:
                    continue
            except:
                continue
            container_id = os.path.basename(key)
            if container_id in reply_data:
                if container['stats'][-1]['cpu']['usage']['total'] == 0:
                    continue
            memory_stats = container['stats'][-1]['memory']
            cpu_stats = container['stats'][-1]['cpu']
            cpu_percentage = self.parse_cpu(node.num_cores, container)
            cpu_stats['cpu_percentage'] = cpu_percentage

            container['stats'] = {
                'memory': memory_stats,
                'cpu': cpu_stats
            }
            pod_name = container['spec']['labels']['io.kubernetes.pod.name']
            namespace = container['spec']['labels']['io.kubernetes.pod.namespace']
            container['namespace'] = namespace
            container['pod_name'] = pod_name
            reply_data[os.path.basename(key)] = container
            reply_data[container_id] = container

        response = flask.make_response(json.dumps(reply_data))
        return response

    def get_interval(self, cur, prev):
        '''
        return the seconds between curl and prev
        '''
        cur_date =  datetime.datetime.strptime(cur[:24], '%Y-%m-%dT%H:%M:%S.%f')
        prev_date =  datetime.datetime.strptime(prev[:24], '%Y-%m-%dT%H:%M:%S.%f')
        time_delta = cur_date - prev_date
        ret = time_delta.seconds + time_delta.microseconds / 1000000.0
        return ret

    def parse_cpu(self, core_nums, container_data):
        if (container_data['spec']['has_cpu'] and len(container_data['stats']) >= 2):
            data = container_data['stats']
            cur = data[-1]
            prev = data[-2]
            time_seconds = self.get_interval(cur['timestamp'], prev['timestamp'])
            raw_usage = cur['cpu']['usage']['total']    \
                        - prev['cpu']['usage']['total']
            usage = float(raw_usage) / pow(10,9) /time_seconds * 100
            return round(usage, 2)
        return -1

    def get_mem_from_str(self, mem_str):
        '''
        memstr = nnnGi/nnnMi
        '''
        unit = mem_str[-2:]
        if unit.upper() == 'GI':
            return float(mem_str[:-2]) * 1024
        elif unit.upper() == 'MI':
            return float(mem_str[:-2])
        elif unit.upper() == 'KI':
            return float(mem_str[:-2]) / 1024

        return -1

class ResourceNode(Resource):
    def get(self):
        response = flask.make_response(json.dumps(node.dump_as_dict()))
        return response

def usage():
    print "Usage: paas-agent.py --port=12305 --cadvisor-address=127.0.0.1:4194"


def start_ws(opts, _share_dict):
    global node, port, cadvisor_IP, cadvisor_port

    for opt, arg in opts:
        if opt == "--cadvisor-address":
            cadvisor_IP, cadvisor_port = arg.split(':')
            cadvisor_port = int(cadvisor_port)
        if opt == "--port":
            port = int(arg)
        if opt in ['-h', '--help']:
            usage()
            sys.exit(0)

    node = Node(cadvisor_IP)

    node_v1_1.g_share_dict = _share_dict

    app = Flask(__name__)
    api = Api(app)
    api.add_resource(ReosurcePodContainerList, '/api/v1.0/docker')
    api.add_resource(ResourceNode, '/api/v1.0/machine')
    api.add_resource(node_v1_1.ResourceMachine, '/api/v1.1/machine')
    api.add_resource(node_v1_1.ResourcePlatform, '/api/v1.1/platform')

    app.run(host="0.0.0.0", port=port, debug=True, threaded=True)


def start_monitor(_share_dict):
    last_idle, last_total = utils.get_cpu_usage()
    sys_path='/host/sys'
    devs = [d for d in os.listdir('%s/class/net/' % sys_path)
            if re.match('(^eth|lo)', d)]
    ns1 = {dev: utils.get_net_flow(dev) for dev in devs}
    while True:
        time.sleep(1)

        idle, total = utils.get_cpu_usage()
        idle_delta, total_delta = idle - last_idle, total - last_total
        usage = 100.0 * (1.0 - idle_delta / total_delta)
        _share_dict['cpu_usage'] = round(usage, 2)
        last_idle, last_total = idle, total

        ns2 = {dev: utils.get_net_flow(dev) for dev in devs}
        net = {dev: {'rx_byte_sec': ns2[dev]['rx_byte'] - ns1[dev]['rx_byte'],
                 'tx_byte_sec': ns2[dev]['tx_byte'] - ns1[dev]['tx_byte']}
               for dev in devs}
        _share_dict['net_stat'] = net
        ns1 = copy.deepcopy(ns2)


if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help", "cadvisor-address="])
    except getopt.GetoptError as err:
        print str(err)
        usage()
        sys.exit(2)

    _share_dict = Manager().dict()

    monitor = Process(target=start_monitor, args=(_share_dict,))
    monitor.start()
    time.sleep(2)
    ws = Process(target=start_ws, args=(opts, _share_dict))
    ws.start()
    ws.join()
    monitor.join()

