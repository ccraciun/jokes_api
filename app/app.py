from gevent import monkey
monkey.patch_all()

import hashlib
import os
import random
import redis
import time

from collections import defaultdict
from functools import wraps

from flask import Flask, request, render_template, render_template_string, make_response, json, jsonify, abort

app = Flask('jokes')
r = redis.StrictRedis(host="localhost", port=6379, db=0)
jokes = json.load(open('jokes.json'))['value']
jokes = {joke['id']: joke for joke in jokes if 'explicit' not in joke['categories']}

APPNAME = "chitter"

THROTTLE_HNAME           = "{}_thr".format(APPNAME)
THROTTLE_OPTION_REQUESTS = "{}_throttle_requests".format(APPNAME)
THROTTLE_OPTION_INTERVAL = "{}_throttle_interval".format(APPNAME)
THROTTLE_EXEMPT_HEADER   = "x-full-throttle"

CRASH_OPTION        = "{}_crash_thresh".format(APPNAME)
CRASH_EXEMPT_HEADER = "x-wedding-crashers"

OVERLOAD_OPTION        = "{}_overload_thresh".format(APPNAME)
OVERLOAD_EXEMPT_HEADER = "x-overload"

SLOWDOWN_OPTION        = "{}_slowdown_thresh".format(APPNAME)
SLOWDOWN_EXEMPT_HEADER = "x-ludicrous-speed"
SLOWDOWN_TIME          = "{}_slowdown_max_time".format(APPNAME)
SLOWDOWN_BASE_TIME     = "{}_slowdown_base_time".format(APPNAME)


@app.route('/')
@app.route('/api/help')
def help():
    """ Print available api functions """
    func_list = defaultdict(dict)
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            func_list[rule.endpoint][rule.rule] = {
                    'doc': app.view_functions[rule.endpoint].__doc__.strip(),
                    'methods': list(rule.methods - {'HEAD', 'OPTIONS'}),
                    }
    return render_template("help.html", data=func_list)


@app.route('/api/joke/<id>')
@app.route('/api/joke')
def joke(id=None):
    """
    Get a joke from the db with the given id. If no id is given, get a random joke.
    The returned json will be of the format:
        {"message":"", "status": 200, value: {"categories": categories, "id": id, "author": id, "joke": "text", "pic": "pic_url"}}
    """
    if not id:
        id = random.choice(jokes.keys())
    try:
        id = int(id)
    except ValueError:
        abort(400)
    if id not in jokes:
        abort(404)
    return jsonify(message="",
            status=200,
            value={'categories': jokes[id]['categories'], 'joke': jokes[id]['joke'], 'id': id, 'author': 'Chuck Norris'})


@app.after_request
def add_header(resp):
    resp.headers['Access-Control-Allow-Origin'] = resp.headers.get('Access-Control-Allow-Origin', '*')
    return resp


@app.errorhandler(429)
def too_many_requests(err):
    resp = jsonify(
            message="Slow your roll, homie",
            status=429,
            data={}
            )
    resp.headers['Retry-After'] = r.get(THROTTLE_OPTION_INTERVAL) or 30
    return resp, 429


@app.errorhandler(400)
def bad_request(err):
    return jsonify(
            message=str(err),
            status=400,
            data={}
            ), 400


@app.before_request
def before_request():
    def exempt():
        return request.endpoint in {'help'}

    @unless_header(THROTTLE_EXEMPT_HEADER)
    def throttle():
        throttle_reqs = float(r.get(THROTTLE_OPTION_REQUESTS) or 5)
        throttle_interval = int(r.get(THROTTLE_OPTION_INTERVAL) or 30)
        throttle_key = "{}_{}_{}".format(request.remote_addr,
                throttle_interval,
                int(time.time() / throttle_interval))
        if r.hincrby(THROTTLE_HNAME, throttle_key, 1) > throttle_reqs:
            abort(429)

    @unless_header(SLOWDOWN_EXEMPT_HEADER)
    def random_slowdown():
        base_wait = float(r.get(SLOWDOWN_BASE_TIME) or 0.25)
        time.sleep(base_wait)

        thresh = float(r.get(SLOWDOWN_OPTION) or 0.4)
        if random.random() < thresh:
            max_wait = float(r.get(SLOWDOWN_TIME))
            time.sleep(random.random() * max_wait - base_wait)

    @unless_header(OVERLOAD_EXEMPT_HEADER)
    def random_overload():
        thresh = float(r.get(OVERLOAD_OPTION) or 0.1)
        if random.random() < thresh:
            abort(503)

    @unless_header(CRASH_EXEMPT_HEADER)
    def random_crash():
        thresh = float(r.get(CRASH_OPTION) or 0.1)
        if random.random() < float(thresh):
            abort(500)

    if not exempt():
        random_crash()
        random_overload()
        throttle()
        random_slowdown()


def unless_header(*header_names):
    def decorator(f):
        @wraps(f)
        def decorated_func(*args, **kwargs):
            if any(request.headers.get(header_name) for header_name in header_names):
                return
            return f(*args, **kwargs)
        return decorated_func
    return decorator


def main():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
