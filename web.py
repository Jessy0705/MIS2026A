import requests
from bs4 import BeautifulSoup

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

from google.cloud.firestore_v1.base_query import FieldFilter
# 判斷是在 Vercel 還是本地
if os.path.exists('serviceAccountKey.json'):
    # 本地環境：讀取檔案
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    # 雲端環境：從環境變數讀取 JSON 字串
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred)

from flask import Flask, render_template,request, make_response, jsonify

from datetime import datetime
import random
app = Flask(__name__)

@app.route("/")
def index():
    link = "<h1>歡迎進入施富傑的網站網頁</h1>"
    link += "<a href=/mis>課程</a><hr>"
    link += "<a href=/today>今天日期</a><hr>"
    link += "<a href=/about>關於富傑</a><hr>"
    link += "<a href=/welcome?u=富傑&dep=靜宜資管>GET傳</a><hr>"
    link += "<a href=/account>POST傳直(帳號密碼)</a><hr>"
    link += "<a href=/math>數學運算</a><hr>" 
    link += "<a href=/cup>擲茭</a><hr>"
    link += "<br><a href=/read>讀取Firestore資料(根據lab遞減排序取前4)</a><br>"
    link += "<a href=/search>查詢老師研究室</a><hr>"
    link += "<a href=/movie>即將上映電影</a><hr>"
    link += "<br><a href=/movie2>讀取開眼電影即將上映影片，寫入Firestore</a><br>"
    link += "<a href=/movie3>電影搜尋</a><hr>"
    link += "<a href=/traffic>易肇事路口查詢</a><hr>"
    link += "<a href=/weather>氣象預報查詢</a><hr>"
    link += "<a href=/rate>本週新片進DB</a><hr>"
    return link

@app.route("/webhook", methods=["POST"])
def webhook():
    # build a request object
    req = request.get_json(force=True)
    # fetch queryResult from json
    action =  req.get("queryResult").get("action")
    msg =  req.get("queryResult").get("queryText")
    info = "動作：" + action + "； 查詢內容：" + msg
    return make_response(jsonify({"fulfillmentText": info}))


@app.route("/rate")
def rate():
    #本週新片
    url = "https://www.atmovies.com.tw/movie/new/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text[5:]
    print(lastUpdate)
    print()

    result=sp.select(".filmList")

    for x in result:
        title = x.find("a").text
        introduce = x.find("p").text

        movie_id = x.find("a").get("href").replace("/", "").replace("movie", "")
        hyperlink = "http://www.atmovies.com.tw/movie/" + movie_id
        picture = "https://www.atmovies.com.tw/photo101/" + movie_id + "/pm_" + movie_id + ".jpg"

        r = x.find(class_="runtime").find("img")
        rate = ""
        if r != None:
            rr = r.get("src").replace("/images/cer_", "").replace(".gif", "")
            if rr == "G":
                rate = "普遍級"
            elif rr == "P":
                rate = "保護級"
            elif rr == "F2":
                rate = "輔12級"
            elif rr == "F5":
                rate = "輔15級"
            else:
                rate = "限制級"

        t = x.find(class_="runtime").text

        t1 = t.find("片長")
        t2 = t.find("分")
        showLength = t[t1+3:t2]

        t1 = t.find("上映日期")
        t2 = t.find("上映廳數")
        showDate = t[t1+5:t2-8]

        doc = {
            "title": title,
            "introduce": introduce,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "showLength": int(showLength),
            "rate": rate,
            "lastUpdate": lastUpdate
        }

        db = firestore.client()
        doc_ref = db.collection("本週新片含分級").document(movie_id)
        doc_ref.set(doc)
    return "本週新片已爬蟲及存檔完畢，網站最近更新日期為：" + lastUpdate

@app.route("/weather", methods=["GET", "POST"])
def weather():
    if request.method == "POST":
        city = request.form["city"]
        city = city.replace("台", "臺")

        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        token = "rdec-key-123-45678-011121314"

        url = (
            "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
            + "?Authorization=" + token
            + "&format=JSON"
            + "&locationName=" + city
        )

        data = requests.get(url, verify=False)
        jsonData = json.loads(data.text)

        locations = jsonData.get("records", {}).get("location", [])

        if len(locations) == 0:
            return "查無此縣市資料<br><a href='/weather'>返回</a>"

        weather = locations[0]["weatherElement"][0]["time"][0]["parameter"]["parameterName"]
        rain = locations[0]["weatherElement"][1]["time"][0]["parameter"]["parameterName"]

        result = f"""
        <h2>{city} 天氣查詢結果</h2>
        天氣狀況：{weather}<br>
        降雨機率：{rain}%<br><br>
        <a href='/weather'>返回</a>
        """

        return result

    return """
    <h2>氣象預報查詢</h2>
    <form method="post">
        請輸入縣市：
        <input type="text" name="city">
        <input type="submit" value="查詢">
    </form>
    <a href="/">回首頁</a>
    """

@app.route("/traffic", methods=["GET", "POST"])
def traffic():
    if request.method == "POST":
        road = request.form["road"]
        road = road.replace("台", "臺")

        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        url = "https://newdatacenter.taichung.gov.tw/api/v1/no-auth/resource.download?rid=a1b899c0-511f-4e3d-b22b-814982a97e41"

        data = requests.get(url, verify=False)
        jsonData = json.loads(data.text)

        result = f"<h2>{road} 查詢結果</h2>"
        found = False

        for item in jsonData:
            if road in item["路口名稱"]:
                found = True
                result += (
                    f"路口：{item['路口名稱']}<br>"
                    f"發生：{item['總件數']} 件<br>"
                    f"主要肇因：{item['主要肇因']}<br><hr>"
                )

        if not found:
            result += "抱歉，查無相關資料！"

        result += "<br><a href='/traffic'>返回查詢</a>"
        return result

    return """
    <h2>易肇事路口查詢系統</h2>
    <form method="post">
        請輸入路名：
        <input type="text" name="road">
        <input type="submit" value="查詢">
    </form>
    <a href="/">回首頁</a>
    """

@app.route("/movie3", methods=["GET", "POST"])
def movie3():
    if request.method == "POST":
        keyword = request.form["keyword"]

        url = "https://www.atmovies.com.tw/movie/next/"
        data = requests.get(url)
        data.encoding = "utf-8"

        sp = BeautifulSoup(data.text, "html.parser")
        result = sp.select(".filmListAllX li")

        output = f"<h2>搜尋結果：{keyword}</h2>"

        found = False

        for item in result:
            title = item.find("img").get("alt")
            link = item.find("a").get("href")
            full_link = "https://www.atmovies.com.tw" + link

            # 🔍 關鍵字比對
            if keyword in title:
                found = True
                output += f"{title}<br>"
                output += f"<a href='{full_link}' target='_blank'>查看電影</a><br><br>"

        if not found:
            output += "查無相關電影 😢<br>"

        output += "<a href='/movie3'>返回</a>"
        return output

    return """
    <h2>電影關鍵字搜尋</h2>
    <form method="post">
        請輸入電影名稱關鍵字：
        <input type="text" name="keyword">
        <input type="submit" value="搜尋">
    </form>
    <a href="/">回首頁</a>
    """

@app.route("/movie2")
def movie2():
  url = "http://www.atmovies.com.tw/movie/next/"
  Data = requests.get(url)
  Data.encoding = "utf-8"
  sp = BeautifulSoup(Data.text, "html.parser")
  result=sp.select(".filmListAllX li")
  lastUpdate = sp.find("div", class_="smaller09").text[5:]

  for item in result:
    picture = item.find("img").get("src").replace(" ", "")
    title = item.find("div", class_="filmtitle").text
    movie_id = item.find("div", class_="filmtitle").find("a").get("href").replace("/", "").replace("movie", "")
    hyperlink = "http://www.atmovies.com.tw" + item.find("div", class_="filmtitle").find("a").get("href")
    show = item.find("div", class_="runtime").text.replace("上映日期：", "")
    show = show.replace("片長：", "")
    show = show.replace("分", "")
    showDate = show[0:10]
    showLength = show[13:]

    doc = {
        "title": title,
        "picture": picture,
        "hyperlink": hyperlink,
        "showDate": showDate,
        "showLength": showLength,
        "lastUpdate": lastUpdate
      }

    db = firestore.client()
    doc_ref = db.collection("電影").document(movie_id)
    doc_ref.set(doc)    
  return "近期上映電影已爬蟲及存檔完畢，網站最近更新日期為：" + lastUpdate


@app.route("/movie")
def movie():
    url = "https://www.atmovies.com.tw/movie/next/"
    data = requests.get(url)
    data.encoding = "utf-8"

    sp = BeautifulSoup(data.text, "html.parser")
    result = sp.select(".filmListAllX li")

    output = "<h2>即將上映電影</h2>"

    for item in result:
        title = item.find("img").get("alt")
        link = item.find("a").get("href")

        full_link = "https://www.atmovies.com.tw" + link

        output += f"{title}<br>"
        output += f"<a href='{full_link}' target='_blank'>{full_link}</a><br><br>"

    output += "<a href='/'>回首頁</a>"
    return output

@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        keyword = request.form["keyword"]

        db = firestore.client()
        collection_ref = db.collection("靜宜資管2026a")

        docs = collection_ref.get()

        result = ""

        for doc in docs:
            user = doc.to_dict()
            if keyword in user["name"]:
                result += f"{user['name']}老師的研究室在 {user['lab']}<br>"

        if result == "":
            result = "查無資料"

        return result + "<br><a href=/search>返回</a>"

    return """
    <h2>查詢老師研究室</h2>
    <form method="post">
        請輸入老師姓名：
        <input type="text" name="keyword">
        <input type="submit" value="查詢">
    </form>
    <a href="/">回首頁</a>
    """

@app.route("/read")
def read():
    db = firestore.client()

    collection_ref = db.collection("靜宜資管2026a")
        #docs = collection_ref.where(filter=FieldFilter("mail","==", "tcyang@pu.edu.tw")).get()
    docs = collection_ref.order_by("lab").limit(3).get()

    Temp = ""   # ✅ 一定要先初始化

    for doc in docs:
        Temp += str(doc.to_dict()) + "<br>"

    return Temp

@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>回到網站首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    year = str(now.year)
    month = str(now.month)
    day = str(now.day)
    now = year + "年" + month + "月" + day +"日"
    return render_template("today.html", datetime = str(now))

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/welcome",methods=["GET"])
def welcome():
    x = request.values.get("u")
    y = request.values.get("dep")
    # user = request.values.get("nick")
    return render_template("welcome.html", name = x, dep = y)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        result = "您輸入的帳號是：" + user + "; 密碼為：" + pwd 
        return result
    else:
        return render_template("account.html")

@app.route("/math", methods=["GET", "POST"])
def math():
    if request.method == "POST":
        try:
            x = float(request.form["x"])
            y = float(request.form["y"])
        except:
            return "請輸入數字！<a href=/math>返回</a>"

        opt = request.form["opt"]

        if opt == "+":
            result = x + y
        elif opt == "-":
            result = x - y
        elif opt == "*":
            result = x * y
        elif opt == "/":
            result = x / y if y != 0 else "除數不可為0"
        else:
            result = "運算錯誤"

        return f"<h2>結果：{result}</h2><a href=/math>再算一次</a>"

    return """
    <h2>數學運算</h2>
    <form method="post">
        x: <input type="text" name="x"><br><br>
        運算符號:
        <select name="opt">
            <option value="+">+</option>
            <option value="-">-</option>
            <option value="*">*</option>
            <option value="/">/</option>
        </select><br><br>
        y: <input type="text" name="y"><br><br>
        <input type="submit" value="計算">
    </form>
    <a href="/">回首頁</a>
    """

@app.route('/cup', methods=["GET"])
def cup():
    # 檢查網址是否有 ?action=toss
    #action = request.args.get('action')
    action = request.values.get("action")
    result = None
    
    if action == 'toss':
        # 0 代表陽面，1 代表陰面
        x1 = random.randint(0, 1)
        x2 = random.randint(0, 1)
        
        # 判斷結果文字
        if x1 != x2:
            msg = "聖筊：表示神明允許、同意，或行事會順利。"
        elif x1 == 0:
            msg = "笑筊：表示神明一笑、不解，或者考慮中，行事狀況不明。"
        else:
            msg = "陰筊：表示神明否定、憤怒，或者不宜行事。"
            
        result = {
            "cup1": "/static/" + str(x1) + ".jpg",
            "cup2": "/static/" + str(x2) + ".jpg",
            "message": msg
        }
        
    return render_template('cup.html', result=result)

if __name__ == "__main__":
    app.run()