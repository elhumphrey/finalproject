from cs50 import SQL, eprint
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

TYPES = ["acorn", "fruits", "twigs", "unknown", "ash", "beech", "birch", "cherry", "chestnut", "hemlock", "oak", "nontreelitter", "pinecones", "rmaple", "rpine", "spruce", "strmaple", "whazel", "wpine"]
# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("postgres://beghxsknocirxj:34b23dfb10088c8d70f54d035a53e117145122bbbd8b3b80bff3f4929e546434@ec2-184-73-206-155.compute-1.amazonaws.com:5432/d5d2lm53n3gnm5")

@app.route("/timesheet")
@login_required
def home():
    final = db.execute("SELECT * FROM timesheet")
    return render_template("timesheet.html", works=final)

@app.route("/reference")
@login_required
def reference():
    return render_template("reference.html")

@app.route("/checkin", methods=["GET", "POST"])
@login_required
def checkin():
    """check in to work"""
    now = datetime.now()
    if request.method == "GET":
        return render_template("checkin.html")
    if request.method == "POST":
        # check for valid input
        checkin = request.form.get("date_time_button")
    db.execute("INSERT INTO timesheet (userid, timein, timeout, date) VALUES (:id, :timein, :timeout, :date)",
    id=session["user_id"], timein = now.strftime("%H:%M:%S"), timeout = 0, date=now.strftime("%Y %m %d"))
    return redirect("/record")

@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    """checkout of work"""
    now = datetime.now()
    if request.method == "GET":
        return render_template("checkout.html")
    if request.method == "POST":
        # check for valid input
        checkout = request.form.get("date_time_button")
        db.execute("UPDATE timesheet SET timeout = :checkout WHERE userid = :id AND date=:date",
                       checkout = now.strftime("%H:%M:%S"), id=session["user_id"], date=now.strftime("%Y %m %d"))
    return redirect("/timesheet")



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("name"):
            return apology("must provide name", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE name = :name",
                          name=request.form.get("name"))

        password = db.execute("SELECT password FROM users WHERE name = :name", name=request.form.get("name"))
        print (request.form.get("password"))
        print (password)
        # Ensure username exists and password is correct
        if len(rows) != 1 or password[0]['password'] != request.form.get("password"):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["userid"]

        # Redirect user to home page
        return redirect("/checkin")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


@app.route("/A1", methods=["GET", "POST"])
@login_required
def A1():

    if request.method == "POST":
        if request.form['action'] == 'Submit':
            params = {}
            for type in TYPES:
                try:
                    params[type+"envelope"] = float(request.form.get(type+"envelope"))
                except:
                    params[type+"envelope"]=0
                try:
                    params[type+"weight"] = float(request.form.get(type+"weight"))
                except:
                    params[type+"weight"]=0

            params["userid"] = session["user_id"]

            db.execute("INSERT INTO a1 (type, envelope,weight, userid) VALUES ('acorn', :acornenvelope, :acornweight, :userid), ('fruits', :fruitsenvelope, :fruitsweight, :userid), ('twigs', :twigsenvelope, :twigsweight, :userid), ('unknown', :unknownenvelope, :unknownweight, :userid), ('ash', :ashenvelope, :ashweight, :userid), ('beech', :beechenvelope, :beechweight, :userid), ('birch', :birchenvelope, :birchweight, :userid), ('cherry', :cherryenvelope, :cherryweight, :userid), ('chestnut', :chestnutenvelope, :chestnutweight, :userid), ('hemlock', :hemlockenvelope, :hemlockweight, :userid), ('oak', :oakenvelope, :oakweight, :userid), ('nontreelitter', :nontreelitterenvelope, :nontreelitterweight, :userid), ('pinecones', :pineconesenvelope, :pineconesweight, :userid), ('rmaple', :rmapleenvelope, :rmapleweight, :userid), ('rpine', :rpineenvelope, :rpineweight, :userid), ('spruce', :spruceenvelope, :spruceweight, :userid), ('strmaple', :strmapleenvelope, :strmapleweight, :userid), ('whazel', :whazelenvelope, :whazelweight, :userid), ('wpine', :wpineenvelope, :wpineweight, :userid) ON CONFLICT ON CONSTRAINT type DO update SET envelope=excluded.envelope, weight=excluded.weight", **params)
            return redirect("/A1")
        elif request.form['action'] == 'Update':
            params = {}
            for type in TYPES:
                try:
                    params[type+"envelope"] = float(request.form.get(type+"envelope"))
                except:
                    params[type+"envelope"]=0
                try:
                    params[type+"weight"] = float(request.form.get(type+"weight"))
                except:
                    params[type+"weight"]=0
                results = db.execute("SELECT envelope, weight FROM a1 WHERE type=:type", type = type)
                print(results[0])
                if results[0]["envelope"] == 0:
                    db.execute("UPDATE a1 SET envelope = :enveloperesults WHERE type=:type", enveloperesults=params[type+"envelope"], type=type)
                if results[0]["weight"] == 0:
                    db.execute("UPDATE a1 SET weight=:weightresults WHERE type=:type", weightresults=params[type+"weight"], type=type)
            return redirect("/A1")
    else:
        return render_template("A1.html")

@app.route("/A2", methods=["GET", "POST"])
@login_required
def A2():

    if request.method == "POST":
        if request.form['action'] == 'Submit':
            params = {}
            for type in TYPES:
                try:
                    params[type+"envelope"] = float(request.form.get(type+"envelope"))
                except:
                    params[type+"envelope"]=0
                try:
                    params[type+"weight"] = float(request.form.get(type+"weight"))
                except:
                    params[type+"weight"]=0

            params["userid"] = session["user_id"]

            db.execute("INSERT INTO a2 (type, envelope,weight, userid) VALUES ('acorn', :acornenvelope, :acornweight, :userid), ('fruits', :fruitsenvelope, :fruitsweight, :userid), ('twigs', :twigsenvelope, :twigsweight, :userid), ('unknown', :unknownenvelope, :unknownweight, :userid), ('ash', :ashenvelope, :ashweight, :userid), ('beech', :beechenvelope, :beechweight, :userid), ('birch', :birchenvelope, :birchweight, :userid), ('cherry', :cherryenvelope, :cherryweight, :userid), ('chestnut', :chestnutenvelope, :chestnutweight, :userid), ('hemlock', :hemlockenvelope, :hemlockweight, :userid), ('oak', :oakenvelope, :oakweight, :userid), ('nontreelitter', :nontreelitterenvelope, :nontreelitterweight, :userid), ('pinecones', :pineconesenvelope, :pineconesweight, :userid), ('rmaple', :rmapleenvelope, :rmapleweight, :userid), ('rpine', :rpineenvelope, :rpineweight, :userid), ('spruce', :spruceenvelope, :spruceweight, :userid), ('strmaple', :strmapleenvelope, :strmapleweight, :userid), ('whazel', :whazelenvelope, :whazelweight, :userid), ('wpine', :wpineenvelope, :wpineweight, :userid) ON CONFLICT ON CONSTRAINT type DO update SET envelope=excluded.envelope, weight=excluded.weight", **params)
            return redirect("/A2")
        elif request.form['action'] == 'Update':
            params = {}
            for type in TYPES:
                try:
                    params[type+"envelope"] = float(request.form.get(type+"envelope"))
                except:
                    params[type+"envelope"]=0
                try:
                    params[type+"weight"] = float(request.form.get(type+"weight"))
                except:
                    params[type+"weight"]=0
                results = db.execute("SELECT envelope, weight FROM a2 WHERE type=:type", type = type)
                print(results[0])
                if results[0]["envelope"] == 0:
                    db.execute("UPDATE a1 SET envelope = :enveloperesults WHERE type=:type", enveloperesults=params[type+"envelope"], type=type)
                if results[0]["weight"] == 0:
                    db.execute("UPDATE a1 SET weight=:weightresults WHERE type=:type", weightresults=params[type+"weight"], type=type)
            return redirect("/A2")
    else:
        return render_template("A2.html")

@app.route("/A3", methods=["GET", "POST"])
@login_required
def A3():

    if request.method == "POST":
        if request.form['action'] == 'Submit':
            params = {}
            for type in TYPES:
                try:
                    params[type+"envelope"] = float(request.form.get(type+"envelope"))
                except:
                    params[type+"envelope"]=0
                try:
                    params[type+"weight"] = float(request.form.get(type+"weight"))
                except:
                    params[type+"weight"]=0

            params["userid"] = session["user_id"]

            db.execute("INSERT INTO a3 (type, envelope,weight, userid) VALUES ('acorn', :acornenvelope, :acornweight, :userid), ('fruits', :fruitsenvelope, :fruitsweight, :userid), ('twigs', :twigsenvelope, :twigsweight, :userid), ('unknown', :unknownenvelope, :unknownweight, :userid), ('ash', :ashenvelope, :ashweight, :userid), ('beech', :beechenvelope, :beechweight, :userid), ('birch', :birchenvelope, :birchweight, :userid), ('cherry', :cherryenvelope, :cherryweight, :userid), ('chestnut', :chestnutenvelope, :chestnutweight, :userid), ('hemlock', :hemlockenvelope, :hemlockweight, :userid), ('oak', :oakenvelope, :oakweight, :userid), ('nontreelitter', :nontreelitterenvelope, :nontreelitterweight, :userid), ('pinecones', :pineconesenvelope, :pineconesweight, :userid), ('rmaple', :rmapleenvelope, :rmapleweight, :userid), ('rpine', :rpineenvelope, :rpineweight, :userid), ('spruce', :spruceenvelope, :spruceweight, :userid), ('strmaple', :strmapleenvelope, :strmapleweight, :userid), ('whazel', :whazelenvelope, :whazelweight, :userid), ('wpine', :wpineenvelope, :wpineweight, :userid) ON CONFLICT ON CONSTRAINT type DO update SET envelope=excluded.envelope, weight=excluded.weight", **params)
            return redirect("/A3")
        elif request.form['action'] == 'Update':
            params = {}
            for type in TYPES:
                try:
                    params[type+"envelope"] = float(request.form.get(type+"envelope"))
                except:
                    params[type+"envelope"]=0
                try:
                    params[type+"weight"] = float(request.form.get(type+"weight"))
                except:
                    params[type+"weight"]=0
                results = db.execute("SELECT envelope, weight FROM a3 WHERE type=:type", type = type)
                print(results[0])
                if results[0]["envelope"] == 0:
                    db.execute("UPDATE a3 SET envelope = :enveloperesults WHERE type=:type", enveloperesults=params[type+"envelope"], type=type)
                if results[0]["weight"] == 0:
                    db.execute("UPDATE a3 SET weight=:weightresults WHERE type=:type", weightresults=params[type+"weight"], type=type)
            return redirect("/A3")
    else:
        return render_template("A3.html")

@app.route("/A4", methods=["GET", "POST"])
@login_required
def A4():


    if request.method == "POST":
        if request.form['action'] == 'Submit':
            params = {}
            for type in TYPES:
                try:
                    params[type+"envelope"] = float(request.form.get(type+"envelope"))
                except:
                    params[type+"envelope"]=0
                try:
                    params[type+"weight"] = float(request.form.get(type+"weight"))
                except:
                    params[type+"weight"]=0

            params["userid"] = session["user_id"]

            db.execute("INSERT INTO a4 (type, envelope,weight, userid) VALUES ('acorn', :acornenvelope, :acornweight, :userid), ('fruits', :fruitsenvelope, :fruitsweight, :userid), ('twigs', :twigsenvelope, :twigsweight, :userid), ('unknown', :unknownenvelope, :unknownweight, :userid), ('ash', :ashenvelope, :ashweight, :userid), ('beech', :beechenvelope, :beechweight, :userid), ('birch', :birchenvelope, :birchweight, :userid), ('cherry', :cherryenvelope, :cherryweight, :userid), ('chestnut', :chestnutenvelope, :chestnutweight, :userid), ('hemlock', :hemlockenvelope, :hemlockweight, :userid), ('oak', :oakenvelope, :oakweight, :userid), ('nontreelitter', :nontreelitterenvelope, :nontreelitterweight, :userid), ('pinecones', :pineconesenvelope, :pineconesweight, :userid), ('rmaple', :rmapleenvelope, :rmapleweight, :userid), ('rpine', :rpineenvelope, :rpineweight, :userid), ('spruce', :spruceenvelope, :spruceweight, :userid), ('strmaple', :strmapleenvelope, :strmapleweight, :userid), ('whazel', :whazelenvelope, :whazelweight, :userid), ('wpine', :wpineenvelope, :wpineweight, :userid) ON CONFLICT ON CONSTRAINT type DO update SET envelope=excluded.envelope, weight=excluded.weight", **params)
            return redirect("/A4")
        elif request.form['action'] == 'Update':
            params = {}
            for type in TYPES:
                try:
                    params[type+"envelope"] = float(request.form.get(type+"envelope"))
                except:
                    params[type+"envelope"]=0
                try:
                    params[type+"weight"] = float(request.form.get(type+"weight"))
                except:
                    params[type+"weight"]=0
                results = db.execute("SELECT envelope, weight FROM a4 WHERE type=:type", type = type)
                print(results[0])
                if results[0]["envelope"] == 0:
                    db.execute("UPDATE a4 SET envelope = :enveloperesults WHERE type=:type", enveloperesults=params[type+"envelope"], type=type)
                if results[0]["weight"] == 0:
                    db.execute("UPDATE a4 SET weight=:weightresults WHERE type=:type", weightresults=params[type+"weight"], type=type)
            return redirect("/A4")
    else:
        return render_template("A4.html")

@app.route("/record", methods=["GET", "POST"])
@login_required
def timesheet():
    return render_template("display.html")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
