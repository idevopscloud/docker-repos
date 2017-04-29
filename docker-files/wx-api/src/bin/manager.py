#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import getopt
import sys
import os
import signal
import time

import multiprocessing
from multiprocessing import Process
from multiprocessing import Manager
from ctypes import c_char_p

g_wx_token = None
g_wx_user_map = None


sys.path.append('..')
from wx_notify.common import conf, utils
from wx_notify.common import constant
from wx_notify.common import log
from wx_notify.common import threadgroup
from wx_notify.log_svr import log_svr
#from wx_notify.wx_sync import proc_share
from wx_notify.wx_sync import wx_syncer
from wx_notify.web_service import ws_wx_notify


CONF = conf.CONF
LOG = log.LOG


def usage():
    print sys.argv[0]
    print sys.argv[0], "db_host db_port"


def start_wx_sync(g_wx_token, g_wx_user_map):
    utils.set_encoding()

    tg = threadgroup.ThreadGroup()

    wx = wx_syncer.WXSyncer()
    tg.add_timer(3600, wx.sync_token, 0, g_wx_token)
    tg.add_timer(300, wx.sync_users, 2, g_wx_token, g_wx_user_map)

    utils.prevent_zombie(1)


def start_log_svr():
    utils.set_encoding()
    log_svr.start_log_svr()


def start_ws_wx(g_wx_token, g_wx_user_map):
    utils.set_encoding()
    ws_wx_notify.start_ws(g_wx_token, g_wx_user_map)


def stop_daemons(plist):
    for p in plist:
        if p.is_alive():
            p.terminate()
    for p in plist:
        p.join(10)


def start_daemons():
    plist_daemon = []
    log_svc = Process(target=start_log_svr, name='start_log_svr')
    log_svc.start()
    plist_daemon.append(log_svc)
    # enable log server is ready
    time.sleep(3)

    wx_sync = Process(target=start_wx_sync, name='start_wx_sync', args=(
        g_wx_token, g_wx_user_map))
    wx_sync.start()
    plist_daemon.append(wx_sync)
    time.sleep(3)

    ws = Process(target=start_ws_wx, name='start_ws_wx', args=(
        g_wx_token, g_wx_user_map))
    ws.start()
    plist_daemon.append(ws)

    return plist_daemon


def chk_child_procs(plist):
    procs = []
    for p in plist:
        if not p.is_alive():
            LOG.warn("[%s] is not alive, will restart.." % p.name)
            p2 = Process(target=p._target, name=p._name, kwargs=p._kwargs)
            p2.start()
            procs.append(p2)
            time.sleep(3)
            if p2.is_alive():
                LOG.info("Started [%s] successfully." % p2.name)
            else:
                LOG.error("Start [%s] failed." % p2.name)
        else:
            procs.append(p)
    return procs


def procs_ctrl():
    plist_daemon = start_daemons()

    parent_pid = os.getpid()

    def _my_exit(*args):
        if parent_pid == os.getpid():
            stop_daemons(plist_daemon)
        sys.exit()

    signal.signal(signal.SIGINT, _my_exit)
    signal.signal(signal.SIGTERM, _my_exit)

    while True:
        time.sleep(3)
        plist_daemon = chk_child_procs(plist_daemon)


def main():
    utils.set_encoding()

#     proc_share.init()
    manager = Manager()

    global g_wx_token
    global g_wx_user_map

    g_wx_token = manager.Value(c_char_p, "token string")
    g_wx_user_map = manager.dict()

    if len(sys.argv) == 1:
        procs_ctrl()
    elif len(sys.argv) == 3:
        CONF.set("db_wx", "db_host", sys.argv[1])
        CONF.set("db_wx", "db_port", sys.argv[2])
        procs_ctrl()
    else:
        usage()

if __name__ == '__main__':
    main()
