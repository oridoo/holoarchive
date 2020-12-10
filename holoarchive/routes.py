from flask import render_template, request, jsonify, make_response

from holoarchive import app, db, api
from holoarchive.core import ctrl

@app.before_first_request()
def init():
    ctrl.start()

@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/channels")
def channels():
    return render_template("channels.html",
                           channels=db.select_all_channels())


@app.route("/api/add-channel", methods=["POST"])
def add_channel():
    req = request.get_json()
    print(req)
    if api.add_channel(req):
        res = make_response(jsonify({"message": "Channel added"}), 200)
    else:
        res = make_response(jsonify({"message": "Not able to add channel"}), 500)
    return res


@app.route("/api/remove-channel", methods=["POST"])
def remove_channel():
    req = request.get_json()
    print(req)
    if api.remove_channel(req):
        res = make_response(jsonify({"message": "Channel added"}), 200)
    else:
        res = make_response(jsonify({"message": "Not able to add channel"}), 500)
    return res


@app.route("/api/get-channels", methods=["GET"])
def get_channels():
    res = make_response(jsonify(db.select_all_channels()), 200)
    return res


@app.route("/api/get-status", methods=["GET"])
def get_status():
    res = make_response(jsonify(api.get_status()), 200)
    return res
