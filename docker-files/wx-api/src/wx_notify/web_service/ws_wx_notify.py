#!/usr/bin/env python
# coding=utf-8
import json
import hashlib
import xmltodict

from flask import abort, Flask, jsonify, make_response, request

from flask.ext.restful import reqparse
from flask.ext.httpauth import HTTPBasicAuth

from wx_notify.common import utils
from wx_notify.common import constant
from wx_notify.common import conf
from wx_notify.common import log
from wx_notify.common.wx_api import WXApi
from wx_notify.common.mysql import DBOperator
from wx_notify.model.tables import WXSendResult


g_wx_token = None
g_wx_user_map = None
db = None


LOG = log.LOG
CONF = conf.CONF

auth = HTTPBasicAuth()
app = Flask(__name__)
access_record = {}

parser_msg_rslt = reqparse.RequestParser()
parser_msg_rslt.add_argument('msgid', type=int, required=True)


class AccessRecord(object):

    def __init__(self):
        self.__reset()

    def __reset(self):
        self.access_num = 1
        self.ts_begin_utc = utils.get_utc_ts()

    def is_overload(self, threshold):
        now = utils.get_utc_ts()
        if (now - self.ts_begin_utc > constant.WS_OVERLOAD_CHECK_INTERVAL_SEC):
            self.__reset()
        else:
            self.access_num += 1
            if self.access_num > threshold:
                return True
        return False


@app.errorhandler(403)
def custom403(error):
    response = jsonify({'message': error.description})
    response.status_code = 403
    return response


def overload_protect(func):
    def wrapper(*args, **kwargs):
        usr = request.authorization.username
        if usr in access_record:
            ar = access_record[usr]
            threshold = 3 if usr == 'test' else constant.WS_OVERLOAD_THRESHOLD
            if ar.is_overload(threshold):
                err_msg = ("Over load protect, please contact admin. User: %s, "
                           "Access number: %d > %d in %ds"
                           % (usr, ar.access_num, threshold,
                              constant.WS_OVERLOAD_CHECK_INTERVAL_SEC))
                LOG.warn(err_msg)
                abort(403, err_msg)
        else:
            access_record[usr] = AccessRecord()
        return func(*args, **kwargs)
    return wrapper


@auth.get_password
def get_password(username):
    if username == constant.WS_HTTPS_USER:
        return constant.WS_HTTPS_PASS
    elif username == 'paas':
        return 'jJjLiMVBNeklji'
    elif username == 'test':
        return 'test'

    return None


@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)


def __get_openid(uname):
    LOG.debug(g_wx_user_map.get('nickname').keys())
    LOG.debug(uname)
    uname = utils.utf8_str_to_unicode(uname)
    if uname in g_wx_user_map['nickname']:
        return g_wx_user_map['nickname'][uname].get('openid')
    elif uname in g_wx_user_map['remark']:
        return g_wx_user_map['remark'][uname].get('openid')
    else:
        return None


@app.route('/api/v1.0/send_tmpl_msg', methods=['POST'])
@overload_protect
@auth.login_required
def send_tmpl_msg():
    data = request.json
    if 'touser' not in data or 'template_id' not in data or 'data' not in data:
        return 'Bad Args', 400

    LOG.info('CIP[%s], user[%s], data[%s]'
             % (request.remote_addr, request.authorization.username, data))
    oid = __get_openid(data['touser'])
    if not oid:
        ret = {
            'errcode': 1, 'errmsg': 'Unknown user name[%s]' % data['touser']}
        return json.dumps(ret), 200

    data['touser'] = oid

    return WXApi.tmpl_send_msg(g_wx_token.value, data), 200


def __insert_db_msg_rslt(rslt):
    try:
        db.insert_obj(rslt)
    except Exception:
        LOG.error("Insert to db failed: %s" % rslt)


def __chk_signature(signature, timestamp, nonce):
    args = []
    args.append(CONF.get("wexin", "mytoken"))
    args.append(timestamp)
    args.append(nonce)
    args.sort()
    mysig = hashlib.sha1(''.join(args)).hexdigest()
    return mysig == signature


@app.route('/api/v1.0/cb', methods=['POST', 'GET'])
def callback():
    sign = request.args.get('signature')
    ts = request.args.get('timestamp')
    nonce = request.args.get('nonce')
    if not (sign and ts and nonce):
        return "", 400

    echostr = request.args.get('echostr')
    if echostr:
        if __chk_signature(sign, ts, nonce):
            return echostr, 200
        else:
            return "check failed", 401

    xml_data = request.data
    json_data = xmltodict.parse(xml_data).get("xml")
    msg_type = json_data.get("MsgType")
    event = json_data.get("Event")
    if msg_type == "event" and event == "TEMPLATESENDJOBFINISH":
        rslt = WXSendResult(msg_id=int(json_data.get("MsgID")),
                            svc_id=json_data.get("ToUserName"),
                            openid=json_data.get("FromUserName"),
                            ts_create=int(json_data.get("CreateTime")),
                            msg_type=msg_type,
                            msg_event=event,
                            status=json_data.get("Status"))
        __insert_db_msg_rslt(rslt)
    else:
        LOG.info("recv other msg: %s" % json_data)

    return "ok", 200


@app.route('/api/v1.0/msg_result', methods=['GET'])
@auth.login_required
def msg_rslt():
    args = parser_msg_rslt.parse_args(strict=True)
    msgid = args['msgid']
    LOG.info('CIP[%s], user[%s], msgid[%s]'
             % (request.remote_addr, request.authorization.username, msgid))
    rslt = db.get_wx_result_by_msgid(msgid)
    if not rslt:
        ret = {'errcode': 1, 'errmsg': 'no record'}
    else:
        ret = {'errcode': 0, 'errmsg': 'ok', 'msgid': msgid,
               'status': rslt.status, 'ts_create': rslt.ts_create}

    return json.dumps(ret), 200


def __env_prepare(_wx_token, _wx_user_map):
    global db
    global g_wx_token
    global g_wx_user_map

    db = DBOperator()
    g_wx_token = _wx_token
    g_wx_user_map = _wx_user_map


def start_ws(_wx_token, _wx_user_map):
    __env_prepare(_wx_token, _wx_user_map)
    port = CONF.getint("wx_service", "ws_port")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
