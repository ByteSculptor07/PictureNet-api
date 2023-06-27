from flask import Flask, request
from deta import Deta

app = Flask(__name__)
deta = Deta()

user_base = deta.Base("user")
img_base = deta.Base("images")

@app.route("/")
def index():
    return "This is the PictureNet api."
    
@app.route("/adduser", methods=["POST"])
def add_user():
    request_data = request.get_json()
    if request_data:
        if not user_base.get(request_data["user"]):
            user_base.put({"id": request_data["id"], "url": request_data["url"], "liked": []}, request_data["user"])
            return "success!"
        else:
            return "error: user existing!"
    else:
        return "error: no data!"


@app.route("/addimg", methods=["POST"])
def add_image():
    request_data = request.get_json()
    if request_data:
        user_base.put({"url": request_data["url"], "likes": 0, "tags": request_data["tags"], "user": request_data["user"]})
        return "success!"
    else:
        return "error: no data!"
