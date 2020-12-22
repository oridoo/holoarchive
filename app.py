from holoarchive import app, routes
from holoarchive.core import ctrl

@app.before_first_request
def init():
    ctrl.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0")
