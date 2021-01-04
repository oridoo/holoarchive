from holoarchive import app, routes
from holoarchive.core import ctrl

ctrl.start()


if __name__ == "__main__":
    app.run(host="0.0.0.0")
