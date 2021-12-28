import flask
import json
import hmac
import os
import hashlib
import base64
import logging
import flask
import config

logging.basicConfig(
    filename="app.log",
    filemode="w",
    level=logging.INFO,
)

app = flask.Flask(__name__)

consumer_secret = config.consumer_secret
port = int(os.getenv('PORT'))

@app.route("/webhook/twitter", methods=["GET", "POST"])
def callback() -> json:
    if flask.request.method == "GET" or flask.request.method == "PUT":
        hash_digest = hmac.digest(
            key=consumer_secret.encode("utf-8"),
            msg=flask.request.args.get("crc_token").encode("utf-8"),
            digest=hashlib.sha256,
        )
        return {
            "response_token": "sha256="
            + base64.b64encode(hash_digest).decode("ascii")
        }
    elif flask.request.method == "POST":
        data = flask.request.get_json()
        logging.info(data)
        return {"code": 200}
    # Once the code running on the server. 
    # You can register and subscribe to events from your local machine.