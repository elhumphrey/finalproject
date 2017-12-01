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

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.route("/")
@login_required
def index():
    # get all data from table
    stocks = db.execute("SELECT symbol, shares FROM history WHERE id = :id", id=session['user_id'])
    actualtotal = 0
    for stock in stocks:
        symbol = stock["symbol"]
        shares = stock["shares"]
        info = lookup(symbol)
        total = shares * info["price"]
        actualtotal += total
        # update table data for correct index format
        db.execute("UPDATE history SET price=:price, total=:total WHERE id=:id AND symbol=:symbol",
                   price=usd(info["price"]), total=usd(total), id=session["user_id"], symbol=symbol)
    # get users cash to calculate current monetary totals
    cash = db.execute("SELECT cash FROM users WHERE id = :id", id=session['user_id'])
    actualtotal += cash[0]["cash"]
    # pass table data to html file
    history = db.execute("SELECT * FROM history WHERE id=:id", id=session["user_id"])
    return render_template("index.html", stocks=history, cash=usd(cash[0]["cash"]), actual_total=usd(actualtotal))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    now = datetime.now()
    if request.method == "GET":
        return render_template("buy.html")
    if request.method == "POST":
        # check for valid input
        try:
            symbol = request.form.get("symbol")
            shares = int(request.form.get("shares"))
        except:
            return apology("please enter values", 400)

        if not symbol:
            return apology("must provide symbol of share desired", 403)

        if not shares or shares <= 0:
            return apology("must provide number of shares", 400)

        quote = lookup(request.form.get("symbol"))
        if not quote:
            return apology("not a valid stock symbol :(")

        cash = (db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"]))

        # make sure user has enough money to make desired purchase
        if not cash[0]["cash"]:
            return apology("not enough", 403)
        elif cash[0]["cash"] <= quote['price'] * shares:
            return apology("not enough money", 403)
        # if they do have enough money, update database
        else:
            db.execute("UPDATE users SET cash = cash - :spent where id = :id",
                       spent=quote["price"] * shares, id=session['user_id'])
            db.execute("INSERT INTO history ('id', 'symbol', 'shares', 'price', 'transacted', 'total') VALUES (:id, :symbol, :number, :price, :transacted, :total)",
                       id=session["user_id"], symbol=request.form.get('symbol'), number=request.form.get('shares'), price=quote['price'], transacted=now.strftime("%Y %m %d %H:%M:%S"), total=int(quote["price"]) * shares)

            return redirect("/")


@app.route("/history")
@login_required
def history():
    # get database values to use in html jinja
    histories = db.execute("SELECT * FROM history where id= :id", id=session['user_id'])
    for history in histories:
        quote = lookup(history["symbol"])
        symbol = history["symbol"]
        shares = history["shares"]
        price = quote["price"]
        transacted = history["transacted"]
    # pass database info into html file
    return render_template("history.html", histories=histories)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "POST":
        # check for valid input, get info about that stock
        quote = lookup(request.form.get("symbol"))
        if not quote:
            return apology("not a valid stock symbol :(")
        # if valid, send to display quote page and show quote info
        return render_template("displayquote.html", name=quote["name"], price=quote["price"])
    # if not valid, send back to quote page
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        password = request.form.get("password")

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        elif not request.form.get("confirmation"):
            return apology("must provide password twice", 400)

        # personal touch! Make sure password contains at least one number
        elif not any(i.isdigit() for i in password):
            return apology("password must contain at least one number!", 400)

        # if registration is valid, add user to database
        if request.form.get("password") == request.form.get("confirmation"):
            result = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)",
                                username=request.form.get("username"), hash=generate_password_hash(request.form.get("password")))
            if not result:
                return apology("Sorry, username is already taken")
        else:
            return apology("Sorry, passwords must match", 400)

        # create unique session id by which to identify this user as they move through the site
        session["user_id"] = result
        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """sell shares of stock"""
    now = datetime.now()
    # get stock information to pass into html so sell page can have a dropdown menu for all stocks owned
    stocks = db.execute("SELECT * from history WHERE id = :id", id=session["user_id"])
    if request.method == "GET":
        return render_template("sell.html", stocks=stocks)
    # check for valid inputs
    if not request.form.get("symbol"):
        return apology("must provide symbol of share desired", 400)

    stock = lookup(request.form.get("symbol"))
    shares = int(request.form.get("shares"))
    # ensure user has enough shares to sell
    currentshares = db.execute("SELECT shares FROM history WHERE id = :id AND symbol = :symbol",
                               id=session["user_id"], symbol=stock["symbol"])

    if int(currentshares[0]["shares"]) < shares:
        return apology("must provide number of shares", 400)

    # if sell is valid, update databases
    else:
        if not currentshares:
            db.execute("INSERT INTO history (id, symbol, shares, price, transacted, total) VALUES (:id, :symbol, :shares, :price, :transacted, :total)",
                       id=session["user_id"], symbol=stock['symbol'], shares=shares, price=stock['price'], transacted=now.strftime("%Y %m %d %H:%M:%S"), total=usd(int(stock["price"]) * shares))
        else:
            totalshares = currentshares[0]["shares"] - shares
            db.execute("UPDATE history SET shares = :shares WHERE id = :id AND symbol = :symbol",
                       shares=totalshares, id=session["user_id"], symbol=stock["symbol"])

    db.execute("UPDATE users SET cash = cash + :earned where id = :id",
               earned=stock["price"] * shares, id=session['user_id'])
    if totalshares == 0:
        db.execute("DELETE FROM history WHERE id = :id AND symbol = :symbol",
                   id=session["user_id"], symbol=stock["symbol"])
    else:
        db.execute("UPDATE history SET shares=:shares WHERE id = :id AND symbol = :symbol",
                   shares=totalshares, id=session["user_id"], symbol=stock["symbol"])

    return redirect("/")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
