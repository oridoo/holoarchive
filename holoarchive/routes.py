from flask import render_template, request, jsonify, make_response

from holoarchive import app, db, api


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
        res = make_response(jsonify({"message": "Channel removed"}), 200)
    else:
        res = make_response(jsonify({"message": "Not able to remove channel"}), 500)
    return res

@app.route("/api/add-video", methods=["POST"])
def add_video():
    req = request.get_json()
    print(req)
    if api.add_video(req["vidid"], req["force"]):
        res = make_response(jsonify({"message": "Video added"}), 200)
    else:
        res = make_response(jsonify({"message": "Not able to add channel"}), 500)
    return res

@app.route("/api/remove-video", methods=["POST"])
def remove_video():
    req = request.get_json()
    print(req)
    if api.remove_video(req["vidid"]):
        res = make_response(jsonify({"message": "Video removed"}), 200)
    else:
        res = make_response(jsonify({"message": "Not able to remove video"}), 500)
    return res

@app.route("/api/check-availability", methods=["POST"])
def check_availability():
    req = request.get_json()
    print(req)
    offline = False
    online = False
    if api.check_offline(req["vidid"]):
        offline = True
    if api.check_online(req["vidid"]):
        online = True
    res = make_response(jsonify(dict(offline=offline, online=online)), 200)
    return res

@app.route("/api/get-channels", methods=["GET"])
def get_channels():
    res = make_response(jsonify(db.select_all_channels()), 200)
    return res


@app.route("/api/get-status", methods=["GET"])
def get_status():
    res = make_response(jsonify(api.get_status()), 200)
    return res
