from flask import Flask, request
from deta import Deta
from urllib.parse import urlencode
import hashlib, requests, re

app = Flask(__name__)
deta = Deta()

user_base = deta.Base("user")
img_base = deta.Base("images")
cookie_base = deta.Base("Cookie")


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
        id = request_data["id"]
        if request_data["prompt"]:
            prompt = request_data["prompt"]
        else:
            prompt = ""
        if hashlib.sha256(id.encode("utf_8")).hexdigest() == user_base.get(request_data["user"])["id"]:
           img_base.put({"url": request_data["url"], "likes": 0, "tags": request_data["tags"], "user": request_data["user"], "prompt": prompt})
           return "success!"
        else:
            return "error: wrong user or id!"
    else:
        return "error: no data!"

@app.route("/getimg/<val>", methods=["GET"])
def get_image(val):
    data = img_base.fetch()
    res = ""
    for item in data.items[int(val)*10-10:int(val)*10]:
        res += str(item["url"]) + "," + str(item["likes"]) + ";"
    res = res[:-1]
    return res

@app.route("/like", methods=["POST"])
def like():
    request_data = request.get_json()
    if request_data:
        id = request_data["id"]
        if hashlib.sha256(id.encode("utf_8")).hexdigest() == user_base.get(request_data["user"])["id"]:
            data = img_base.fetch({"url": request_data["url"]})
            likes = int(data.items[0]["likes"])
            key = data.items[0]["key"]
            likes += 1
            img_base.update({"likes": likes}, key)
            return "success!"
        else:
            return "error: wrong user or id!"
    else:
        return "error: no data!"

@app.route("/unlike", methods=["POST"])
def unlike():
    request_data = request.get_json()
    if request_data:
        id = request_data["id"]
        if hashlib.sha256(id.encode("utf_8")).hexdigest() == user_base.get(request_data["user"])["id"]:
            data = img_base.fetch({"url": request_data["url"]})
            likes = int(data.items[0]["likes"])
            key = data.items[0]["key"]
            if likes > 0:
                likes -= 1
                img_base.update({"likes": likes}, key)
            return "success!"
        else:
            return "error: wrong user or id!"
    else:
        return "error: no data!"
        
@app.route("/generateimg/<query>", methods=["GET"])
def generate_img(query):
    auth_cookie = cookie_base.get("_U")["value"]
    srchhpgusr_cookie = cookie_base.get("srchhpgusr")["value"]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1474.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Referer': 'https://www.bing.com/images/create',
        'Accept-Language': 'en-US;q=0.6,en;q=0.5',
        'Cookie': f'_U={auth_cookie};SRCHHPGUSR={srchhpgusr_cookie}'
    }
    
    data = {
        'q': query,
        'qs': 'ds'
    }
    encoded_query = urlencode({'q': query})
    with requests.Session() as session:
        session.headers.update(headers)

        r = session.get('https://www.bing.com/images/create')

        try:
            coins = int(r.text.split('bal" aria-label="')[1].split(' ')[0])
        except IndexError:
            return "error: authentication failed"

    url = f'https://www.bing.com/images/create?{encoded_query}&rt='
    rt = '4' if coins > 0 else '3'
    esttime = '15sec' if coins > 0 else '5min'
    url += rt
    url += '&FORM=GENCRE'

    with requests.Session() as session:
        session.headers = headers
        r = session.post(url, data=data)

        try:
            ID = r.text.split(';id=')[1].split('"')[0]
        except IndexError:
            return "error: prompt has been rejected"

        IG = r.text.split('IG:"')[1].split('"')[0]
    return ID.replace('&amp;nfy=1', '') + "," + encoded_query + "," + IG + "; " + esttime
        
@app.route("/getgeneratedimg/<str>", methods=["GET"])
def getgeneratedimg(str):
    auth_cookie = cookie_base.get("_U")["value"]
    srchhpgusr_cookie = cookie_base.get("srchhpgusr")["value"]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1474.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Referer': 'https://www.bing.com/images/create',
        'Accept-Language': 'en-US;q=0.6,en;q=0.5',
        'Cookie': f'_U={auth_cookie};SRCHHPGUSR={srchhpgusr_cookie}'
    }
    
    with requests.Session() as session:
        session.headers = headers

        r = session.get(f'https://www.bing.com/images/create/async/results/{str.split(",")[0]}?{str.split(",")[1]}&IG={str.split(",")[2]}&IID=images.as')
        if not 'text/css' in r.text:
            return "error: please wait"
                
        
        src_urls = re.findall(r'src="([^"]+)"', r.text)
        src_urls = [url for url in src_urls if '?' in url]

        for i, src_url in enumerate(src_urls):
            new_url = src_url.replace(src_url.split('?')[1], 'pid=ImgGn')
            src_urls[i] = new_url
        return {'images': [{'url': src_url} for src_url in src_urls]}
