from flask import Flask, request
from deta import Deta

app = Flask(__name__)
deta = Deta()

identity = deta.Base("user")

@app.route("/")
def index():
    return "This is the PictureNet api."
