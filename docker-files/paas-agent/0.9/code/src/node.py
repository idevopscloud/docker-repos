#!/usr/bin/env python
# coding:utf-8
import flask
import json
from flask import request
from flask_restful import Resource

import utils


g_share_dict = None


class Node:

    def __init__(self, name):
        self.name = name
        self.cpu_cores = int(utils.cpu_stat()[0]['cpu cores'])

    def __exist(self, proc, procs):
        for p in procs:
            if p.find(proc) > -1:
                return True
        return False

    def _prob_svc(self, svc):
        rslt = {}
        if svc is None:
            return rslt

        procs = utils.proc_list()
        for name, obj in svc.items():
            rslt[name] = {'proc': None, 'telnet': None, 'http': None}
            if obj.get('proc'):
                rslt[name]['proc'] = self.__exist(name, procs)
            if obj.get('telnet'):
                host, port = obj['telnet'].split(':')
                rslt[name]['telnet'] = {obj['telnet']: utils.chk_port(host, port)}
            if obj.get('http'):
                rslt[name]['http'] = {obj['http']: utils.chk_http(obj['http'])}

        return rslt

    def dump_as_dict(self, svc):
        loadavg = utils.load_stat()
        mem = utils.memory_stat()
        return {
            'name': self.name,
            'cpu': {'cores': self.cpu_cores,
                    'usage': g_share_dict.get('cpu_usage'),
                    'load': {'load1': loadavg['lavg_1'],
                             'load5': loadavg['lavg_5'],
                             'load15': loadavg['lavg_15']
                             }
                    },
            'mem': {"total_mb": mem['MemTotal'] / 1024 / 1024,
                    "free_mb": mem['MemFree'] / 1024 / 1024,
                    "used_mb": mem['MemUsed'] / 1024 / 1024
                    },
            'network': g_share_dict.get('net_stat'),
            'disk': utils.disk_stat(),
            'service': self._prob_svc(svc)
        }


node = Node('127.0.0.1')


class ResourceMachine(Resource):

    def get(self):
        response = flask.make_response(json.dumps(node.dump_as_dict(None)))
        return response

    def post(self):
        svc_json = request.get_json(force=True)
        response = flask.make_response(json.dumps(node.dump_as_dict(svc_json)))
        return response


class ResourcePlatform(Resource):

    def get(self):
        with open('../conf/platform.json', 'r') as fp:
            ps = json.load(fp)
        response = flask.make_response(json.dumps(node.dump_as_dict(ps)))
        return response
