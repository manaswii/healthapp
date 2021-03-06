from dotenv import load_dotenv
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
from pytz import timezone, all_timezones

from helpers import convertToUserTZ, numExtraction, toLitres, calculateSleep, cmToFeet, KgToPounds, getTimeZone, login_required

load_dotenv()


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
db = SQL(os.environ.get("DATABASE_URL"))


@app.route("/", methods = ["GET", "POST"])
@login_required
def index():
    #POST request- when a user adds new information to track from the tracker column
    if request.method == "POST":
        glassesOfWater = 0
        hoursOfSleep = 0
        calories = 0

        #getting values they submitted
        try:
            glassesOfWater += int(request.form.get("glassesOfWater"))
        except:
            pass
        try:
            hoursOfSleep += int(request.form.get("hoursOfSleep"))
            if hoursOfSleep > 24:
                hoursOfSleep = 0
        except:
            pass
        try:
            calories += int(float(request.form.get("calories")))
        except:
            pass
        
        #if they added nothing and submitted, don't enter the blank information in the database.
        if glassesOfWater == 0 and hoursOfSleep == 0 and calories == 0:
            return redirect("/")

        #entering data in the database.
        db.execute("INSERT INTO history (user_id, glasses, sleep, calories) VALUES (?, ?, ?, ?);", session["user_id"], glassesOfWater, hoursOfSleep, calories)
        flash("Added info", "alert")
        return redirect("/")

    #GET request- to get user deatils to display how much user should sleep etc and also display how many calories etc user should consume
    rows = db.execute("SELECT * FROM users JOIN information ON users.id = information.user_id WHERE users.id = ?;", session["user_id"])
    weight = rows[0]["weight"]
    height = rows[0]["height"]
    age = rows[0]["age"]
    gender = rows[0]["gender"]

    #calculate water user should drink everyday
    try: 
        info = {"waterToDrink" : int(int(weight) * 2.205 * 2 / 3) }
        info["glassesToDrink"] = int( info["waterToDrink"] / 8)
    except:
        info = {"waterToDrink" : ""}
    
    #calculate sleep user should get everyday
    try:
        info["sleepToGet"] = calculateSleep(age)
    except:
        info["sleepToGet"] = ""
    
    #calculate calories user should consume everyday, to maintain weight, for a sedentary life style.
    try:
        if gender == "Male":
            info["caloriesToConsume"] = 1.2 * (10 * weight + 6.25 * height - 5 * age + 5)
        elif gender == "Female":
            info["caloriesToConsume"] = 1.2 * (10 * weight + 6.25 * height - 5 * age - 161)
    except:
        info["sleepToGet"] = ""
    
    #calculate how much information user has inputted so far today
    rows = db.execute(f"Select * from history where date_trunc('day', TRANSACTED AT TIME ZONE '{session['time_zone_3']}') = date(timezone('{session['time_zone_3']}', now())) AND user_id = {session['user_id']}")

    glassesOfWater = 0
    hoursOfSleep = 0
    caloriesConsumed = 0
    for row in rows:
        glassesOfWater += row["glasses"]
        hoursOfSleep +=  row["sleep"]
        caloriesConsumed += row["calories"]

    return render_template("index.html", info = info, glassesOfWater = glassesOfWater, hoursOfSleep = hoursOfSleep, caloriesConsumed = caloriesConsumed)


@app.route("/login", methods = ["POST", "GET"])
def login():
    if session.get("user_id"):
        return redirect("/")

    if request.method == "POST":
        user = request.form.get("username")
        password = request.form.get("password")
        timeZone = request.form.get("timeZone")
        usernames = db.execute("SELECT * FROM users WHERE username = ?;", user)

        if timeZone not in all_timezones:
            return "time Zone error"

        if len(usernames) != 1:
            flash("Username does not exist", "error")
            return render_template("login.html")

        if check_password_hash(usernames[0]["hash"], password) == False:
             flash("Invalid password", "error")
             return render_template("login.html")
        else:
            session["user_id"] = usernames[0]["id"]
            #session[time_zone_3] will be of the form -> 'IST'
            session["time_zone_3"] = timeZone
            print(session["time_zone_3"])
            return redirect ("/")

    return render_template("login.html")
        



@app.route("/register", methods = ["POST", "GET"])
def register():
    if request.method == "POST":
        user = request.form.get("username")
        password = request.form.get("password")
        confirmPassword = request.form.get("confirmation")
        
        usernames = db.execute("SELECT username FROM users WHERE username = ?;", user)

        if not user or len(user) < 5:
            flash("Enter a valid username", "error")
            return render_template("register.html")

        elif not password or len(password) < 5:
            flash("Enter a valid password", "error")
            return render_template("register.html")
            
        elif len(usernames) != 0:
            flash("Username already exists", "error")
            return render_template("register.html")

        elif password != confirmPassword:
            flash("Passwords don't match", "error")
            return render_template("register.html")

        hash = generate_password_hash(password)

        #registering(inserting information into the database)
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?);", user, hash)

        #get new user's id
        roww = db.execute("SELECT id FROM users WHERE username = ?", user)
        id = roww[0]["id"]

        #create empty entry for the user in information table
        db.execute("INSERT INTO information (user_id) VALUES (?);", id)
        flash("Account created successfully", "success")
        return redirect("/")

    return render_template("register.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/changePassword", methods = ["GET", "POST"])
@login_required
def changePassword():
    if request.method == "POST":
        currentPass = request.form.get("currentPass")
        newPassword = request.form.get("newPassword")
        confirmNewPassword = request.form.get("confirmNewPassword")

        if newPassword != confirmNewPassword:
            flash("New passwords don't match", "error")
            return render_template("changePassword.html")
        elif len(newPassword) < 5:
            flash("New password must at least be 5 characters long", "error")
            return render_template("changePassword.html")

        rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

        if check_password_hash(rows[0]["hash"], currentPass) == True:
            db.execute("UPDATE users SET hash = ? WHERE id = ?", generate_password_hash(newPassword), session["user_id"])
            flash("Password changed successfully", "success")
            return redirect("/accountsettings")
        else:
            flash("Incorrect current password", "error")
            return render_template("changePassword.html")

    return render_template("changePassword.html")

@app.route("/history")
@login_required
def history():
    #get details for today only
    today = db.execute(f"Select *, to_char(TRANSACTED, 'DD-MM-YYYY HH24:MI') as date from history where date_trunc('day', TRANSACTED AT TIME ZONE '{session['time_zone_3']}') = date(timezone('{session['time_zone_3']}', now())) AND user_id = {session['user_id']} ORDER BY TRANSACTED DESC")
    
    #older details(not including today), grouped by date
    older = db.execute(f"SELECT to_char(date , 'DD-MM-YYYY') AS date, glasses, sleep, calories FROM (SELECT date_trunc('day', TRANSACTED AT TIME ZONE '{session['time_zone_3']}') as date, SUM(glasses) AS glasses, SUM(sleep) AS sleep, SUM(calories) AS calories FROM history WHERE user_id = {session['user_id']} AND date_trunc('day', TRANSACTED AT TIME ZONE '{session['time_zone_3']}') != date(timezone('{session['time_zone_3']}', now())) GROUP BY date) as hist ORDER BY hist.date DESC")
    return render_template("history.html", today = today, older=older)
 

# Contact API to display search results in the website index
#documentation- https://docs.google.com/document/d/1_q-K-ObMTZvO0qUEAxROrN3bwMujwAN25sLHwJzliK0/edit#
@app.route("/searchFood")
@login_required
def searchFood():
    try:
        api_key = os.environ.get("API_KEY")
        api_id = os.environ.get("API_ID")
        user_id = str(session['user_id'])
        name = request.args.get("q")
        url = f"https://trackapi.nutritionix.com/v2/search/instant?query={name}"
        headers = {'x-app-id': api_id, 'x-app-key': api_key, 'x-remote-user-id' : user_id}
        response = requests.get(url, headers=headers)
        response = response.json()
    except requests.RequestException:
        return None

    # Parse response
    try:
        return {
            "common": response["common"],
            "branded" : response["branded"]
        }
    except (KeyError, TypeError, ValueError):
        return None


@app.route("/nutritionInfo") #contact api to get the amount of calories in selected option in index
@login_required
def nutritionInfo():
    try:
        api_key = os.environ.get("API_KEY")
        api_id = os.environ.get("API_ID")
        user_id = str(session['user_id'])
        name = request.args.get("q")
        body = {"query": name}
        url = f"https://trackapi.nutritionix.com/v2/natural/nutrients"
        headers = {'Content-Type': 'application/x-www-form-urlencoded', 'x-app-id': api_id, 'x-app-key': api_key, 'x-remote-user-id' : user_id }
        response = requests.post(url,  headers=headers, data = body)
        response = response.json()
        return {
            "calories" : response["foods"][0]["nf_calories"]
        } 
            
    except requests.RequestException:
        return None


@app.route("/moreinfo") #route to get history of a particular day
@login_required
def moreInfo():
    date = request.args.get("index")

    #checking if it's a valid date.
    list = [0, 0]
    for i in date:
        if i.isdigit():
            list[0] += 1
        elif i == '-':
            list[1] += 1
    if len(date) != 10 or list[1] != 2 or list[0] != 8:
        return "grr"
    

    rows = db.execute(f"SELECT *, to_char(TRANSACTED, 'DD-MM-YYYY HH24:MI') as date1 FROM history WHERE user_id = {session['user_id']} AND to_char(TRANSACTED AT TIME ZONE '{session['time_zone_3']}', 'DD-MM-YYYY') = '{date}'")
    return render_template("moreinfo.html", rows = rows, date = date)


@app.route("/accountsettings", methods = ["GET", "POST"])
@login_required
def accountSettings():
    #POST request- to add information to the account
    if request.method == "POST":
        gender = request.form.get("gender")
        genders = ["Male", "Female", ""]

        #checking if user entered a valid gender.
        if gender not in genders:
            return "grr"

        age = request.form.get("age")
        try:
            weight = float(request.form.get("weight"))
            weight = round(float(weight), 2)
            
            #if weight was entered in pounds, it will be converted to kgs here
            if request.form.get("options") == "pounds":
                weight = round(float(weight / 2.205), 2)
        except:
            weight = 0
        
        if request.form.get("options2") == "feetAndInches":
            #this executes if height is entered in feet and inches and converts the height to cm
            inches = (12 * int(request.form.get("height"))) + int(request.form.get("inches"))
            height = inches * 2.54
        else:
            #this executes if height is entered in cms
            height = request.form.get("height")

        db.execute("UPDATE information SET age = ?, height = ?, weight = ?, gender = ? WHERE user_id = ?;", age, height, weight, gender, session["user_id"])
        flash("Info added successfully", "success")
        return redirect("/accountsettings")

    #GET request- to display account's current information
    fields = ["gender", "age", "weight", "height"]    
    rows = db.execute("SELECT * FROM information WHERE user_id = ?;", session["user_id"])
    return render_template("accountSettings.html", user = rows[0], fields = fields)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
