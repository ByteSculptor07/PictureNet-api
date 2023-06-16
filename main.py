from flask import Flask, request
from deta import Deta

app = Flask(__name__)
deta = Deta()

user_base = deta.Base("user")

@app.route("/")
def index():
    return "This is the PictureNet api."
    
@app.route("/adduser", methods=["POST"])
def add_user():
    request_data = request.get_json()
    if request_data:
        if not user_base.get(request_data["id"]):
            user_base.put({"id": request_data["id"], "url": request_data["url"], "liked": []}, request_data["user"])
            return "success!"
        else:
            return "error: user existing!"
    else:
        return "error: no data!"
