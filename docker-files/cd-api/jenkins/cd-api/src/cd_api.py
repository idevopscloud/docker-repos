#!/usr/bin/env python
# coding=utf-8
import platform
import sys
import time
import urllib2

sys.path.append('..')

from flask import abort, Flask, jsonify, make_response, request

from flask_restful import reqparse
from flask_httpauth import HTTPBasicAuth

from jenkinsapi.jenkins import Jenkins

from src.common import conf
from src.common import constant
from src.common import log


LOG = log.LOG
CONF = conf.CONF

auth = HTTPBasicAuth()
app = Flask(__name__)
access_record = {}

J = None

parser_base_img = reqparse.RequestParser()
parser_base_img.add_argument('img_in', type=str, required=True)
parser_base_img.add_argument('img_out', type=str, required=True)
parser_base_img.add_argument('repo_usr', type=str, required=True)
parser_base_img.add_argument('repo_pwd', type=str, required=True)
parser_base_img.add_argument('commands', type=str, required=True)
parser_base_img.add_argument('callback', type=str, required=True)

parser_comp_img = reqparse.RequestParser()
parser_comp_img.add_argument('img_in', type=str, required=True)
parser_comp_img.add_argument('img_out', type=str, required=True)
parser_comp_img.add_argument('repo_usr', type=str, required=True)
parser_comp_img.add_argument('repo_pwd', type=str, required=True)
parser_comp_img.add_argument('git_addr', type=str, required=True)
parser_comp_img.add_argument('callback', type=str, required=True)
parser_comp_img.add_argument('git_tag', type=str, required=True)
parser_comp_img.add_argument('build_path', type=str, required=True)
parser_comp_img.add_argument('start_path', type=str, required=True)

parser_push_img = reqparse.RequestParser()
parser_push_img.add_argument('img_in', type=str, required=True)
parser_push_img.add_argument('img_out', type=str, required=True)
parser_push_img.add_argument('in_repo_usr', type=str, required=True)
parser_push_img.add_argument('in_repo_pwd', type=str, required=True)
parser_push_img.add_argument('out_repo_usr', type=str, required=True)
parser_push_img.add_argument('out_repo_pwd', type=str, required=True)
parser_push_img.add_argument('callback', type=str, required=True)

parser_console = reqparse.RequestParser()
parser_console.add_argument('job', type=str, required=True,
                            choices=['base_img', 'comp_img', 'push_img'])
parser_console.add_argument('build_num', type=int, required=True)
parser_console.add_argument('start', type=int, required=False)

parser_job_stop = reqparse.RequestParser()
parser_job_stop.add_argument('job', type=str, required=True,
                             choices=['base_img', 'comp_img', 'push_img'])
parser_job_stop.add_argument('build_num', type=int, required=True)


def get_utc_ts():
    return int(time.time())


class AccessRecord(object):

    def __init__(self):
        self.__reset()

    def __reset(self):
        self.access_num = 1
        self.ts_begin_utc = get_utc_ts()

    def is_overload(self, threshold):
        now = get_utc_ts()
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
        addr = request.remote_addr
        if addr in access_record:
            ar = access_record[addr]
            if ar.is_overload(constant.WS_OVERLOAD_THRESHOLD):
                err_msg = ("Over load protect, please contact admin. "
                           "Client: %s, Access number: %d > %d in %ds"
                           % (addr, ar.access_num,
                              constant.WS_OVERLOAD_THRESHOLD,
                              constant.WS_OVERLOAD_CHECK_INTERVAL_SEC))
                LOG.warn(err_msg)
                abort(403, err_msg)
        else:
            access_record[addr] = AccessRecord()
        return func(*args, **kwargs)
    return wrapper


@auth.get_password
def get_password(username):
    if username == constant.WS_HTTPS_USER:
        return constant.WS_HTTPS_PASS
    else:
        return None


@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)


def __dict_strip(d):
    for k, v in d.items():
        d[k] = v.strip() if type(v) == str else v


@app.route('/ping', methods=['GET', 'HEAD'])
def ping():
    return "OK", 200


@app.route('/api/v1.0/base_img', methods=['POST'])
#@overload_protect
@auth.login_required
def base_img():
    args = parser_base_img.parse_args(strict=True)
    __dict_strip(args)
    cmds = args['commands'].split('\r\n')
    args['commands'] = ' && '.join([e.strip() for e in cmds if e.strip()])
    LOG.info('CIP[%s], user[%s], img_in[%s], img_out[%s], commands[%s]'
             % (request.remote_addr, request.authorization.username,
                args['img_in'], args['img_out'], args['commands']))
    try:
        J.build_job('base_img', params=args)
    except Exception as e:
        LOG.exception(e)
        return str(e), 403
    return "OK", 202


@app.route('/api/v1.0/comp_img', methods=['POST'])
@overload_protect
@auth.login_required
def comp_img():
    args = parser_comp_img.parse_args(strict=True)
    __dict_strip(args)
    LOG.info('CIP[%s], user[%s], img_in[%s], img_out[%s], git_addr[%s]'
             ', git_tag[%s]'
             % (request.remote_addr, request.authorization.username,
                args['img_in'], args['img_out'],
                args['git_addr'], args['git_tag']))
    try:
        J.build_job('comp_img', params=args)
    except Exception as e:
        LOG.exception(e)
        return str(e), 403
    return "OK", 202


@app.route('/api/v1.0/push_img', methods=['POST'])
@auth.login_required
def push_img():
    args = parser_push_img.parse_args(strict=True)
    LOG.info('CIP[%s], user[%s], img_in[%s], img_out[%s]'
             % (request.remote_addr, request.authorization.username,
                args['img_in'], args['img_out']))
    try:
        J.build_job('push_img', params=args)
    except Exception as e:
        LOG.exception(e)
        return str(e), 403
    return "OK", 202


@app.route('/api/v1.0/console_whole', methods=['GET'])
@auth.login_required
def console_whole():
    args = parser_console.parse_args(strict=True)
    try:
        j = J.get_job(args['job'])
        b = j.get_build(args['build_num'])
        ret = b.get_console()
    except Exception as e:
        LOG.exception(e)
        return str(e), 403
    return ret, 200


@app.route('/api/v1.0/console', methods=['GET'])
@auth.login_required
def console_incremental():
    args = parser_console.parse_args(strict=True)
    try:
        url = (constant.JENKINS_CONSOLE_URL
               % (jenkins_url, args['job'], args['build_num'], args['start']))
        req = urllib2.Request(url)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
        response = opener.open(req, "", timeout=10)
    except Exception as e:
        LOG.exception(e)
        return str(e), 403 
    resp = make_response(response.read())
    resp.headers = response.headers.dict
    return resp


@app.route('/api/v1.0/stop_build', methods=['GET'])
@auth.login_required
def stop_build():
    args = parser_job_stop.parse_args(strict=True)
    try:
        j = J.get_job(args['job'])
        b = j.get_build(args['build_num'])
        ret = b.stop()
    except Exception as e:
        LOG.exception(e)
        return str(e), 403
    return "OK" if ret else "Fail", 200


def start_ws():
    app.run(host=CONF.get('common', 'host'),
            port=CONF.getint('common', 'port'),
            debug=True, use_reloader=False,
            threaded=True)


if __name__ == '__main__':
    sys.path.append('../..')
    if len(sys.argv) != 2:
        print "Usag: %s jenkins_addr" % sys.argv[0]
        print "e.g : %s http://ap10.idevopscloud.com:28080" % sys.argv[0]
        sys.exit(0)

    jenkins_url = sys.argv[1]
    global J
    J = Jenkins(jenkins_url)
    app.run(host=CONF.get('common', 'host'),
            port=CONF.getint('common', 'port'),
            debug=False, threaded=True)
