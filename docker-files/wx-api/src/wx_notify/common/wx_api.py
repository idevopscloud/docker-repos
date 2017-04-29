#!/usr/local/bin/python
#-*-coding:utf-8-*-
import urllib2
import json
import sys

sys.path.append('../..')

from wx_notify.common import log
from wx_notify.common import conf
from wx_notify.common import constant
from wx_notify.common import utils


LOG = log.LOG
CONF = conf.CONF


try:
    appid = CONF.get('wexin', 'appid')
    appsecret = CONF.get('wexin', 'appsecret')
except Exception as ex:
    LOG.exception(ex)
    sys.exit()

url_base = 'https://api.weixin.qq.com/cgi-bin'
uri_token = ('%s/token?grant_type=client_credential&appid=%s&secret=%s'
             % (url_base, appid, appsecret))
uri_send_tmpl_msg = url_base + '/message/template/send?access_token=%s'
uri_usr_list = url_base + '/user/get?access_token=%s'
uri_usr_info = url_base + '/user/info/batchget?access_token=%s'


class WXApi(object):

    @staticmethod
    def __post(url, data=None):
        req = urllib2.Request(url)
        #data = urllib.urlencode(data) if data else None
        # enable cookie
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
        response = opener.open(req, data, timeout=10)
        return response.read()

    @staticmethod
    def __send_msg(uri, json_data):
        try:
            res_str = WXApi.__post(uri, json.dumps(json_data))
            res_json = json.loads(res_str)
            LOG.info("code:%s, msg:%s, msgid:%d"
                     % (res_json.get("errcode"), res_json.get("errmsg"),
                        res_json.get("msgid", 0)))
            return res_str
        except Exception as ex:
            LOG.error("[Fail] data: %s!" % json_data)
            raise

    @staticmethod
    @utils.retry
    def access_token():
        ret = WXApi.__post(uri_token)
        return json.loads(ret)

    @staticmethod
    @utils.retry
    def tmpl_send_msg(token, data):
        url = uri_send_tmpl_msg % token
        data['url'] = 'http://weixin.qq.com'
        tmp = {k:{"value": v, "color":"#173177" if k != 'remark' else "#BE2F2F"}
               for k,v in data['data'].items()}
        data['data'] = tmp
        return WXApi.__send_msg(url, data)

    @staticmethod
    @utils.retry
    def get_user_list(token):
        '''
        NOTE: this method will only pull at most 10000 users
            need improve it when user number > 10000
        '''
        url = uri_usr_list % token
        usrs = WXApi.__post(url)
        openids = json.loads(usrs).get('data', {}).get('openid', [])
        return openids

    @staticmethod
    @utils.retry
    def get_user_info(token, oid_list):
        url = uri_usr_info % token
        users = []

        def __get_usr_batch(oids):
            data = {"user_list": [{"openid": oid} for oid in oids]}
            usrs_str = WXApi.__post(url, json.dumps(data))
            usrs_json = json.loads(usrs_str)
            return usrs_json.get('user_info_list', [])

        max_bat_usr = 100
        for i in range(9999999):
            if len(oid_list) > max_bat_usr * i:
                oids = oid_list[max_bat_usr * i:max_bat_usr * (i + 1)]
                users += __get_usr_batch(oids)
            else:
                break
        return users

if __name__ == '__main__':
    ret = WXApi.access_token()
    print ret
    if "access_token" in ret:
        token = ret['access_token']
 
    openids = WXApi.get_user_list(token)
    print openids
 
    ret = WXApi.get_user_info(token, openids)
    print ret
#     token = 'zhYmCz-b-_ZAeM6FIa_CLQeBdlEZJAKuWMVdOhNy8cpYlqqjLKwv68OcKsBfKjddn40fN7pjiwcwsEIA84e-fwZUAgwM5pli8atjTtjGA6upGFivJ4UHAyr6VqcIBG7aHYOhAIAVMC'
    wx_data = {
        'template_id': '165o9MM_-DE7daIpBNA8iFMVAgXTSKykXk2hL0-ToBo',
        'touser': 'oUDhxwATWhMjrV60F-tJzbHOSEWY',
        'data': {
            'first':'',
            'ts': '2016-11-11 11:04:36',
            'last': '45s',
            'level': 'Error',
            'hostname': "10.1.1.2",
            'service': "CPU Load",
            'msg': "CPU Load > 96%",
            'source': 'Nagios',
            'remark': '备注：告警消失'
        }
    }
    print WXApi.tmpl_send_msg(token, wx_data)
