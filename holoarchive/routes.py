from holoarchive import app, db, api
from flask import render_template, request, redirect, jsonify, make_response


@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/channels")
def channels():
    return render_template("channels.html",
                           channels=db.select_all_channels())

@app.route("/channels/add-channel", methods=["POST"])
def add_channel():
    req = request.get_json()
    print(req)
    if api.add_channel(req):
        res = make_response(jsonify({"message": "Channel added"}), 200)
    else:
        res = make_response(jsonify({"message": "Not able to add channel"}), 500)
    return res

