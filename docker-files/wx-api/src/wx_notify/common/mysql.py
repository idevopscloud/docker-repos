#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import sys

from sqlalchemy import create_engine
from sqlalchemy import func, or_, not_, and_
from sqlalchemy.orm import sessionmaker

from wx_notify.common import conf
from wx_notify.common import constant
from wx_notify.common import log
from wx_notify.common import utils
from wx_notify.model.tables import WXToken, WXUser, WXSendResult


CONF = conf.CONF
LOG = log.LOG


class DBOperator(object):
    engine = None
    session = None
    query_wx_token = None
    query_wx_usr = None
    query_wx_send_res = None

    def __init__(self):
        if DBOperator.engine is None or DBOperator.session is None:
            self.__init_db("db_wx")

    def __init_db(self, db):
        db_host = CONF.get(db, "db_host")
        db_port = CONF.get(db, "db_port")
        db_user = CONF.get(db, "db_user")
        db_pass = CONF.get(db, "db_pass")
        db_name = CONF.get(db, "db_name")

        DB_CONNECT_STRING = ('mysql+mysqldb://%s:%s@%s:%s/%s?charset=utf8' %
                             (db_user, db_pass, db_host, db_port, db_name))
        DB_CREATE_STRING = ('mysql+mysqldb://%s:%s@%s:%s/?charset=utf8' %
                            (db_user, db_pass, db_host, db_port))

        self.__prepare_db(DB_CREATE_STRING)
        self.__init_connection(DB_CONNECT_STRING)
        self.__prepare_table()

    def __prepare_db(self, create_str):
        try:
            engine = create_engine(create_str, echo=False)
            engine.execute(
                'create database IF NOT EXISTS %s DEFAULT CHARACTER SET '
                'utf8 DEFAULT COLLATE utf8_general_ci;'
                % CONF.get("db_wx", "db_name"))
        except Exception as e:
            pass

    def __prepare_table(self):
        try:
            WXToken.metadata.create_all(DBOperator.engine)
            WXUser.metadata.create_all(DBOperator.engine)
            WXSendResult.metadata.create_all(DBOperator.engine)
        except Exception as e:
            pass


    def __init_connection(self, connect_str):
        try:
            DBOperator.engine = create_engine(connect_str, echo=False)
            DBSession = sessionmaker(bind=DBOperator.engine, autocommit=True)
            '''
            expire_on_commit=True
                means all instances will be expired after each commit,
                because this session is always do write operation or 
                read result is used immediately.
            '''
            DBOperator.session = DBSession()

            DBOperator.query_wx_token = (DBOperator.session.query(WXToken))
            DBOperator.query_wx_usr = DBOperator.session.query(
                WXUser)
            DBOperator.query_wx_send_res = DBOperator.session.query(
                WXSendResult)
        except Exception as ex:
            print "init DB session failed."
            LOG.exception(ex)
            sys.exit()

    @utils.retry
    def insert_obj(self, obj):
        DBOperator.session.add(obj)
        DBOperator.session.flush()

    @utils.retry
    def get_wx_usr(self):
        return DBOperator.query_wx_usr.all()

    @utils.retry
    def upd_wx_usr(self, usr):
        DBOperator.query_wx_usr.filter(
            WXUser.openid == usr.openid).update(
            {WXUser.nickname: usr.nickname,
             WXUser.remark: usr.remark,
             WXUser.subscribe: usr.subscribe})

    @utils.retry
    def get_wx_result_by_msgid(self, msg_id):
        res = DBOperator.query_wx_send_res.filter(
            WXSendResult.msg_id == msg_id).first()
        return res

    @utils.retry
    def get_wx_token(self):
        return DBOperator.query_wx_token.first()

    @utils.retry
    def upd_wx_token(self, ts_upd, ttl, token):
        DBOperator.query_wx_token.update(
            {WXToken.ts_upd: ts_upd, WXToken.ttl_sec: ttl,
             WXToken.token: token})
