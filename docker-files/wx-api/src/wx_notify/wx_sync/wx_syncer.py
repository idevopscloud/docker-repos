#!/usr/bin/env python
# coding:utf-8
import copy

from wx_notify.common import log
from wx_notify.common import utils
from wx_notify.common.mysql import DBOperator
from wx_notify.common.wx_api import WXApi
from wx_notify.model.tables import WXUser, WXToken


LOG = log.LOG


class WXSyncer(object):

    def __init__(self):
        self.db = DBOperator()
        self.wx_user_map = {}

    def __reset_user_map(self):
        _nickname_map = {}
        _remark_map = {}
        _user_map = {}
        for wf in self._wx_users:
            if wf.get('subscribe') == 1:
                _nickname_map[wf['nickname']] = wf
                _user_map[wf['openid']] = wf
                if wf['remark']:
                    _remark_map[wf['remark']] = wf
        self.wx_user_map = _user_map
        return (_nickname_map, _remark_map)

    def sync_token(self, g_wx_token):
        '''
        This method should be called in left 2hours according to WX's rule
        '''
        # 1. get from WeiXin platform
        try:
            ret = WXApi.access_token()
        except Exception as e:
            LOG.exception(e)
            LOG.error('access token from wx platform failed, NOT update token')

        g_wx_token.value = ret['access_token']

        # update into DB, the data is needed in distribute environment
        try:
            if self.db.get_wx_token():
                self.db.upd_wx_token(utils.get_utc_ts(), ret['expires_in'],
                                     g_wx_token.value)
            else:
                wt = WXToken(token=g_wx_token.value,
                             ts_upd=utils.get_utc_ts(),
                             ttl_sec=ret['expires_in'])
                self.db.insert_obj(wt)
        except Exception as e:
            LOG.exception(e)
            LOG.error('Update token into DB failed, this server will use '
                      'latest token in memory cache rightly. '
                      'But other servers may got error.')

    def sync_users(self, g_wx_token, g_wx_user_map):
        # 1. get user list from WeiXin platform
        try:
            openids = WXApi.get_user_list(g_wx_token.value)
            self._wx_users = WXApi.get_user_info(g_wx_token.value, openids)
            (nickname, remark) = self.__reset_user_map()
            g_wx_user_map["nickname"] = nickname
            g_wx_user_map["remark"] = remark
        except Exception as e:
            LOG.exception(e)
            LOG.error('access token from wx platform failed, NOT update token')

        # 2. update into DB, the data is needed in distribute environment
        try:
            db_user = copy.deepcopy(self.db.get_wx_usr())
            db_oids = []
            # 2.1 for delete and update case
            for du in db_user:
                db_oids.append(du.openid)
                if du.openid not in self.wx_user_map:
                    # do not delete this user, just set unsubscribe
                    db_oids.subscribe = 0
                else:
                    wu = self.wx_user_map[du.openid]
                    if (du.nickname != wu['nickname']
                            or du.remark != wu['remark']):
                        du.nickname = wu['nickname']
                        du.remark = wu['remark']
                self.db.upd_wx_usr(du)

            # 2.2 for add case
            add_usr = list(set(self.wx_user_map.keys()) - set(db_oids))
            for oid in add_usr:
                wu = self.wx_user_map[oid]
                du = WXUser(openid=oid,
                            nickname=wu['nickname'],
                            sex=wu['sex'],
                            subscribe=wu['subscribe'],
                            language=wu['language'],
                            country=wu['country'],
                            province=wu['province'],
                            city=wu['city'],
                            ts_subscribe=wu['subscribe_time'],
                            unionid=0,
                            remark=wu['remark'])
                self.db.insert_obj(du)
        except Exception as e:
            LOG.exception(e)
            LOG.error('Update user into DB failed, just skip this round.')

        LOG.debug("sync user (%d) to db complete." % len(openids))
