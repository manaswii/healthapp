import os
from re import X
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
import requests
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash, check_password_hash


from datetime import datetime
from pytz import timezone

from helpers import convertToUserTZ, numExtraction, toLitres, calculateSleep, cmToFeet, KgToPounds, getTimeZone

#api_key ***REMOVED***	id ***REMOVED***

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

#custom filters
app.jinja_env.filters["toLitres"] = toLitres
app.jinja_env.filters["cmToFeet"] = cmToFeet
app.jinja_env.filters["KgToPounds"] = KgToPounds
app.jinja_env.filters["numExtraction"] = numExtraction
app.jinja_env.filters["convertToUserTZ"] = convertToUserTZ

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
db = SQL("sqlite:///health.db")

#test


@app.route("/", methods = ["GET", "POST"])
def index():
    if session.get("user_id") == None:
        return redirect("/login")

    if request.method == "POST":
        glassesOfWater = 0
        hoursOfSleep = 0
        calories = 0

        try:
            glassesOfWater += int(request.form.get("glassesOfWater"))
        except:
            pass
        try:
            hoursOfSleep += int(request.form.get("hoursOfSleep"))
        except:
            pass
        try:
            calories += int(float(request.form.get("calories")))
            print(calories)
        except:
            pass
        
        if glassesOfWater == 0 and hoursOfSleep == 0 and calories == 0:
            print("everything is 0??")
            #print(int(request.form.get("calories")))
            return redirect("/")

        db.execute("INSERT INTO history (user_id, glasses, sleep, calories) VALUES (?, ?, ?, ?);", session["user_id"], glassesOfWater, hoursOfSleep, calories)
        return redirect("/")

    rows = db.execute("SELECT * FROM users JOIN information ON users.id = information.user_id WHERE users.id = ?;", session["user_id"])
    weight = rows[0]["weight"]
    height = rows[0]["height"]
    age = rows[0]["age"]
    gender = rows[0]["gender"]

    try: 
        info = {"waterToDrink" : int(int(weight) * 2.205 * 2 / 3) }
        info["glassesToDrink"] = int( info["waterToDrink"] / 8)
    except:
        info = {"waterToDrink" : ""}
    
    try:
        info["sleepToGet"] = calculateSleep(age)
    except:
        info["sleepToGet"] = ""
    
    try:
        if gender == "Male":
            info["caloriesToConsume"] = 1.2 * (10 * weight + 6.25 * height - 5 * age + 5)
        elif gender == "Female":
            info["caloriesToConsume"] = 1.2 * (10 * weight + 6.25 * height - 5 * age - 161)
    except:
        info["sleepToGet"] = ""
    
    rows = db.execute("Select * from history where TRANSACTED between date('now', 'start of day') and date('now', 'start of day', '+1 day') AND user_id = ?", session["user_id"])
    glassesOfWater = 0
    hoursOfSleep = 0
    for row in rows:
        glassesOfWater += row["glasses"]
        hoursOfSleep +=  row["sleep"]

    return render_template("index.html", info = info, glassesOfWater = glassesOfWater, hoursOfSleep = hoursOfSleep)


@app.route("/login", methods = ["POST", "GET"])
def login():
    if request.method == "POST":
        user = request.form.get("username")
        password = request.form.get("password")

        usernames = db.execute("SELECT * FROM users WHERE username = ?;", user)

        if len(usernames) != 1:
            return "username does not exist"
        
        if check_password_hash(usernames[0]["hash"], password) == False:
            return "incorrect password"
        else:
            session["user_id"] = usernames[0]["id"]
            tmp = getTimeZone(request.environ.get('HTTP_X_REAL_IP', request.remote_addr))
            session["time_zone"] = tmp["timezone"]
            session["time_zone_2"] = tmp["timezone"]
            format = "%z"
            session["time_zone"] = datetime.now(timezone(session["time_zone"])).strftime(format)
            session["time_zone"] = session["time_zone"][:-2] + ":" + session["time_zone"][-2:]
            if session["time_zone"][0] == '-':
                session["time_zone"] = '+' + session["time_zone"][1:]
            elif session["time_zone"][0] == '+':
                session["time_zone"] = '-' + session["time_zone"][1:]            
            print(session["time_zone"])
            return redirect ("/")

    return render_template("login.html")
        



@app.route("/register", methods = ["POST", "GET"])
def register():
    if request.method == "POST":
        user = request.form.get("username")
        password = request.form.get("password")
        confirmPassword = request.form.get("confirmation")
        
        usernames = db.execute("SELECT username FROM users WHERE username = ?;", user)

        if not user:
            return "enter a username"
        elif not password:
            return "enter a password"
        elif len(usernames) != 0:
            return "username already exists"
        elif password != confirmPassword:
            return "passwords don't match"


        hash = generate_password_hash(password)
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?);", user, hash)
        roww = db.execute("SELECT id FROM users WHERE username = ?", user)
        id = roww[0]["id"]
        db.execute("INSERT INTO information (user_id) VALUES (?);", id)
        return redirect("/")

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/history")
def history():
    if session.get("user_id") == None:
        return redirect("/login")

    print(f"Select * from history where TRANSACTED between datetime('now', 'start of day', '{session['time_zone']}') and datetime('now', 'start of day', '+1 day', '{session['time_zone']}') AND user_id = {session['user_id']} ORDER BY TRANSACTED DESC;")
    today = db.execute(f"Select * from history where TRANSACTED between datetime('now', 'start of day', '{session['time_zone']}') and datetime('now', 'start of day', '+1 day', '{session['time_zone']}') AND user_id = {session['user_id']} ORDER BY TRANSACTED DESC")
    older = db.execute(f"SELECT strftime('%d', TRANSACTED) as date, strftime('%d-%m-%Y', TRANSACTED) as date1, SUM(glasses) as glasses, SUM(sleep) as sleep, SUM(calories) as calories FROM history WHERE user_id = ? AND TRANSACTED NOT between date('now', 'start of day', '{session['time_zone']}') and date('now', 'start of day', '+1 day', '{session['time_zone']}') GROUP BY date ORDER BY date DESC;", session["user_id"])

    return render_template("history.html", today = today, older=older)

@app.route("/searchFood")
def searchFood():
      # Contact API
    try:
        #api_key ***REMOVED***	id ***REMOVED***
        name = request.args.get("q")
        #print(name)
        url = f"https://trackapi.nutritionix.com/v2/search/instant?query={name}"
        headers = {'x-app-id': '***REMOVED***', 'x-app-key': '***REMOVED***', 'x-remote-user-id' : '0'}
        response = requests.get(url, headers=headers)
        response = response.json()
        #print(response["common"][0]["food_name"])
        #print(type(response["common"][0]["food_name"]))
        return response
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"]
        }
    except (KeyError, TypeError, ValueError):
        return None

@app.route("/nutritionInfo")
def nutritionInfo():
    try:
        #api_key ***REMOVED***	id ***REMOVED***
        name = request.args.get("q")
        body = {"query": name}
        url = f"https://trackapi.nutritionix.com/v2/natural/nutrients"
        headers = {'Content-Type': 'application/x-www-form-urlencoded', 'x-app-id': '***REMOVED***', 'x-app-key': '***REMOVED***', 'x-remote-user-id' : '0' }
        response = requests.post(url,  headers=headers, data = body)
        response = response.json()
        print(type(response))
        #for key in response.items():
        #    print(key)
        print(response["foods"][0]["nf_calories"])

        return response
    except requests.RequestException:
        return None



@app.route("/moreinfo")
def moreInfo():

    name = request.args.get("index")
    rows = db.execute("SELECT * FROM history WHERE user_id = ? AND strftime('%d-%m-%Y', TRANSACTED) = ?", session["user_id"], name)
    return render_template("moreinfo.html", rows = rows, date = name)


@app.route("/accountsettings", methods = ["GET", "POST"])
def accountSettings():
    if session.get("user_id") == None:
        return redirect("/login")

    if request.method == "POST":
        gender = request.form.get("gender")
        genders = ["Male", "Female", ""]

        if gender not in genders:
            return "grr"

        age = request.form.get("age")
        try:
            weight = float(request.form.get("weight"))
        except:
            weight = 0
        
        weight = round(float(weight), 2)
        if request.form.get("options2") == "feetAndInches":
            inches = (12 * int(request.form.get("height"))) + int(request.form.get("inches"))
            height = inches * 2.54
        else:
            height = request.form.get("height")

        #to convert pounds to kgs before entering into databases
        if request.form.get("options") == "pounds":
            weight = round(float(weight / 2.205), 2)

        db.execute("UPDATE information SET age = ?, height = ?, weight = ?, gender = ? WHERE user_id = ?;", age, height, weight, gender, session["user_id"])
        return redirect("/accountsettings")

    fields = ["gender", "age", "weight", "height"]    
    rows = db.execute("SELECT * FROM information WHERE user_id = ?;", session["user_id"])
    return render_template("accountSettings.html", user = rows[0], fields = fields)
