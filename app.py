from gevent import monkey
monkey.patch_all()

import time
import redis
import random
import hashlib
from flask import Flask, request, render_template, render_template_string, make_response, json, jsonify, abort

app = Flask('pumper')
r = redis.StrictRedis(host="localhost", port=6379, db=0)
jokes = json.load(open('jokes.json'))['value']
jokes = {joke['id']: joke for joke in jokes}

APPNAME = "chitter"
THROTTLE_OPTION = "{}_throttle_thresh".format(APPNAME)
THROTTLE_HNAME = "{}_thr".format(APPNAME)
THROTTLE_RPM = 10
THROTTLE_HEADER = "x-throttle-exempt"
THROTTLE_EXEMPT = "__sekrit_key"

CRASH_OPTION = "{}_crash_thresh".format(APPNAME)
CRASH_HEADER = "x-crash-exempt"
CRASH_EXEMPT = "crash_override"

OVERLOAD_OPTION = "{}_overload_thresh".format(APPNAME)
OVERLOAD_HEADER = "x-overload-exempt"
OVERLOAD_EXEMPT = "save_me_jeebus"

CHITTER_H = "{}_chit".format(APPNAME)
CHITTER_RECENT_S = "{}_recent_chit".format(APPNAME)


@app.route('/api/u/<id>')
def user(id):
    """
    Get some data about a user.
    """
    pass


@app.route('/api/c/random')
def rand_chit():
    """
    Get a random recent chit.
    """
    pass


@app.route('/api/c/<id>')
def get_chit(id):
    """
    Get the chit with the given id.

    The returned json will be of the format:
        {"message":"", "status": 200, data: {"date": date, "id": id, "author": id, "text": "text", "pic": "pic_url"}}
    """
    try:
        id = int(id)
    except ValueError as e:
        abort(400)
    if id not in jokes:
        abort(404)
    return jsonify(message="",
            status=200,
            data={'chitID': id, 'authorID': "tester", 'text': "testtest"})


@app.route('/api/c')
def chits():
    """
    Get some recent chit ids
    """
    pass


@app.route('/api/c', methods=['POST'])
def post_chit():
    """
    Create a new chit
    """
    data = {'date': time.now(),
            'author': request.args['aid'],
            'text': request.args['text'],
            'pic': request.args.get('pic'),
            }
    id = hashlib.md5(json.dumps(data)).hexdigest()
    data['id'] = id
    r.hset(CHITTER_H, id, json.dumps(data))
    r.sadd(CHITTER_RECENT_S, json.dumps(data))
    return jsonify(
            message="Ok",
            status=200,
            data={"id": id}
            ), 200


@app.route('/')
@app.route('/api/help')
def help():
    """ Print available api functions """
    func_list = {}
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            func_list[rule.rule] = app.view_functions[rule.endpoint].__doc__.strip()
    return render_template("help.html", data=func_list)


@app.errorhandler(429)
def too_many_requests(err):
    return jsonify(
            message="Slow your roll, homie",
            status=429,
            data={}
            ), 429


@app.errorhandler(400)
def bad_request(err):
    return jsonify(
            message=str(err),
            status=400,
            data={}
            ), 400


@app.before_request
def before_request():
    def throttle():
        if request.headers.get(THROTTLE_HEADER) == THROTTLE_EXEMPT:
            return
        throttle_key = "{}_{}".format(request.remote_addr, int(time.time() / 60))
        if r.hincrby(THROTTLE_HNAME, throttle_key, 1) > THROTTLE_RPM:
            abort(429)

    def random_overload():
        thresh = r.get(OVERLOAD_OPTION)
        if not thresh or request.headers.get(OVERLOAD_HEADER) == CRASH_EXEMPT:
            return
        if random.random() < float(thresh):
            abort(503)

    def random_crash():
        thresh = r.get(CRASH_OPTION)
        if not thresh or request.headers.get(CRASH_HEADER) == CRASH_EXEMPT:
            return
        if random.random() < float(thresh):
            abort(500)

    random_crash()
    random_overload()
    throttle()


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
