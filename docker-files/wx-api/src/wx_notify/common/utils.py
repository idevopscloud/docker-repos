#!/usr/bin/env python
# coding:utf-8
import copy
import hashlib
import os
import sys
import time

from eventlet import greenthread

from wx_notify.common import log
from wx_notify.common import constant


LOG = log.LOG


inet_ntoa = lambda x: '.'.join([str(x/(256**i)%256) for i in range(3,-1,-1)])


def get_utc_ts():
    return int(time.time())


def utc_ts_to_str_beijing(seconds):
    return time.strftime("%Y-%m-%d %H:%M:%S",
                         time.gmtime(seconds + 3600 * 8))


def unicode_to_str(ustr):
    if type(ustr) == unicode:
        return ustr.encode('utf-8')
    else:
        return ustr


def utf8_str_to_unicode(utf8_str):
    if type(utf8_str) == str:
        return utf8_str.decode('utf-8')
    else:
        return utf8_str


def md5(text):
    m = hashlib.md5()
    m.update(text)
    return m.hexdigest()


def second_to_str(second):
    day = second / 86400
    hour = second % 86400 / 3600
    minute = second % 3600 / 60
    sday = "%d天" % day if day > 0 else ''
    shour = "%d小时" % hour if (hour > 0 or day > 0) else ''
    smin = "%d分钟" % minute
    return sday + shour + smin


def retry(func):
    def wrapper(*args, **kwargs):
        # retry 3 times before raise an exception
        for i in range(3):
            try:
                return func(*args, **kwargs)
            except Exception as ex:
                LOG.exception(ex)
                LOG.warning("retry...")
                if i < 3:
                    greenthread.sleep((i + 1))
                    continue
                else:
                    raise
                    # sys.exit()
    return wrapper


def set_encoding(coding='utf-8'):
    reload(sys)
    sys.setdefaultencoding(coding)


def get_ppid():
    try:
        return os.getppid()
    except Exception:
        # It is not a Linux OS
        return -1


def prevent_zombie(chk_interval):
    while True:
        greenthread.sleep(chk_interval)
        if get_ppid() == 1:
            LOG.warn("I am being zombie process, I will kill myself.")
            sys.exit()
