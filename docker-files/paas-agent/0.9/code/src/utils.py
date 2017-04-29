#!/usr/bin/env python
# coding:utf-8
import os
import re
import httplib2
import telnetlib
import time


h = httplib2.Http(timeout=1)


def unicode_to_str(ustr):
    if type(ustr) == unicode:
        return ustr.encode('utf-8')


def memory_stat(proc_path='/host/proc'):
    mem = {}
    f = open("%s/meminfo" % proc_path)
    lines = f.readlines()
    f.close()
    for line in lines:
        if len(line) < 2:
            continue
        name = line.split(':')[0]
        var = line.split(':')[1].split()[0]
        mem[name] = long(var) * 1024.0
    mem['MemUsed'] = mem['MemTotal'] - \
        mem['MemFree'] - mem['Buffers'] - mem['Cached']
    return mem


def get_net_flow(dev, sys_path='/host/sys'):
    def __get_val(file):
        with open(file, 'r') as fd:
            return float(fd.read().strip())
    return {
        'rx_byte': __get_val('%s/class/net/%s/statistics/rx_bytes'
                             % (sys_path, dev)),
        'tx_byte': __get_val('%s/class/net/%s/statistics/tx_bytes'
                             % (sys_path, dev))
    }


def net_stat(sys_path='/host/sys'):
    # /proc/net/dev is not work in container
    devs = [d for d in os.listdir('%s/class/net/' % sys_path)
            if re.match('(^eth|lo)', d)]
    ns1 = {dev: get_net_flow(dev) for dev in devs}
    time.sleep(1)
    ns2 = {dev: get_net_flow(dev) for dev in devs}
    net = {dev: {'rx_byte_sec': ns2[dev]['rx_byte'] - ns1[dev]['rx_byte'],
                 'tx_byte_sec': ns2[dev]['tx_byte'] - ns1[dev]['tx_byte']}
           for dev in devs}
    return net


def cpu_stat(proc_path='/host/proc'):
    cpu = []
    cpuinfo = {}
    f = open("%s/cpuinfo" % proc_path)
    lines = f.readlines()
    f.close()
    for line in lines:
        if line == '\n':
            cpu.append(cpuinfo)
            cpuinfo = {}
        if len(line) < 2:
            continue
        name = line.split(':')[0].rstrip()
        var = line.split(':')[1].strip()
        cpuinfo[name] = var
    return cpu


def load_stat(proc_path='/host/proc'):
    loadavg = {}
    f = open("%s/loadavg" % proc_path)
    con = f.read().split()
    f.close()
    loadavg['lavg_1'] = con[0]
    loadavg['lavg_5'] = con[1]
    loadavg['lavg_15'] = con[2]
    loadavg['nr'] = con[3]
    loadavg['last_pid'] = con[4]
    return loadavg


def disk_stat(root_path='/rootfs'):
    hd = {}
    disk = os.statvfs(root_path)
    hd['available_mb'] = disk.f_bsize * disk.f_bavail / 1024 /1024
    hd['total_mb'] = disk.f_bsize * disk.f_blocks / 1024 /1024
    hd['used_mb'] = hd['total_mb'] - hd['available_mb']
    return {'/': hd}


def proc_list(proc_path='/host/proc'):
    procs = []
    for dirname in os.listdir(proc_path):
        try:
            with open('{}/{}/cmdline'.format(proc_path, dirname),
                      mode='rb') as fd:
                content = fd.read().decode().split('\x00')
                procs.append(' '.join(content))
        except Exception:
            continue
    return list(set(procs))



def get_cpu_usage(proc_path='/host/proc'):
    with open('%s/stat' % proc_path) as f:
        fields = [float(column)
                  for column in f.readline().strip().split()[1:]]
        return fields[3], sum(fields)


def cpu_usage(proc_path='/host/proc'):
    last_idle, last_total = get_cpu_usage(proc_path)
    time.sleep(1)
    idle, total = get_cpu_usage()
    idle_delta, total_delta = idle - last_idle, total - last_total
    utils = 100.0 * (1.0 - idle_delta / total_delta)
    return round(utils, 2)


def chk_port(host, port):
    try:
        telnetlib.Telnet(unicode_to_str(host), unicode_to_str(port), 3)
    except Exception:
        return False
    else:
        return True

def chk_http(addr):
    try:
        if addr.find('http://') == -1:
            addr = 'http://' + addr
        (resp_headers, content) = h.request(addr, method="HEAD")
        return int(resp_headers.get('status', '499')) < 400
    except Exception:
        return False
    else:
        return True


if __name__ == '__main__':
#     from pprint import pprint
#     pprint(memory_stat())
#     pprint(net_stat())
#     pprint(cpu_stat())
#     pprint(load_stat())
#     pprint(disk_stat())
#     pprint(proc_list())
#     pprint(cpu_usage())
#     print chk_port('123.207.145.176', 28081)
#     print chk_port('123.207.145.176', 28080)
    print chk_http('www.qq.com')    
    print chk_http('qq.com:8080/ping')
