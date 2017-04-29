#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from sqlalchemy import Column, String, Integer, ForeignKey, SmallInteger
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class WXToken(Base):
    __tablename__ = 'tb_wx_token'

    tid = Column(Integer, primary_key=True)
    token = Column(String(1024))
    ts_upd = Column(Integer)
    ttl_sec = Column(Integer)

    #Base.metadata.create_all()


class WXUser(Base):
    """
    @param sex:
        0: unknown
        1: mal
        2: femal
    @param subscribe:
        0: not subscribe, no this follower
        1: normal
    """
    __tablename__ = 'tb_wx_user'

    openid = Column(String(128), primary_key=True)
    nickname = Column(String(128))
    sex = Column(SmallInteger)
    subscribe = Column(SmallInteger)
    language = Column(String(16))
    country = Column(String(32))
    province = Column(String(32))
    city = Column(String(32))
    ts_subscribe = Column(Integer)
    unionid = Column(Integer)
    remark = Column(String(128))

    #Base.metadata.create_all()

    def __repr__(self):
        return ("<openid:%2, nickname:%s, remark:%s>"
                % (self.openid, self.nickname, self.remark))


class WXSendResult(Base):
    __tablename__ = 'tb_wx_send_result'

    msg_id = Column(Integer, primary_key=True)
    svc_id = Column(String(128))
    openid = Column(String(128))
    ts_create = Column(Integer)
    msg_type = Column(String(64))
    msg_event = Column(String(64))
    status = Column(String(256))

    #Base.metadata.create_all()
