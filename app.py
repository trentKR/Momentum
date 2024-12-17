import os
import sqlite3
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///momentum.db")

def query_db(query, *args):
    try:
        sqliteConnection = sqlite3.connect("momentum.db")
        cursor = sqliteConnection.cursor()
        
        cursor.execute(query, args)
        results = cursor.fetchall()
        cursor.close()
        
        return results

    except sqlite3.Error as error:
        print('Error occurred - ', error)
    
    finally:
        if sqliteConnection:
            sqliteConnection.close()
            print('SQLite Connection closed')

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        try:
            username = request.form.get("username")
            password = request.form.get("password")

            # Ensure username was submitted
            if not username:
                return render_template("error.html")

            # Ensure password was submitted
            elif not password:
                return render_template("error.html")

            # Ensure password confirmation matches intial password entry
            elif password != request.form.get("confirmation"):
                return render_template("error.html")

            # Try to insert information into database. UNIQUE INDEX on users.username
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)",
                       username, generate_password_hash(password))

            # Log in with session
            user_id = db.execute("SELECT id FROM users WHERE username = ?", username)
            session["user_id"] = user_id[0]["id"]

            return redirect("/")

        except ValueError as e:

            # Log the error
            print(f"Error: {e}")

            # Inform the user
            return render_template("error.html")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("error.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("error.html")

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return render_template("error.html")

        try:
            # Remember which user has logged in
            session["user_id"] = rows[0]["id"]
        except TypeError:
            return render_template("error.html")

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/")
@login_required
def index():
    """Landing page"""
    return render_template("index.html", methods=["GET", "POST"])


@app.route("/progress")
@login_required
def progress():
    """Progress"""
    return render_template("progress.html")


@app.route("/team", methods=["GET", "POST"])
@login_required
def team():
    """Team"""
    return render_template("team.html")


@app.route("/coach", methods=["GET", "POST"])
@login_required
def coach():
    """Coach"""
    return render_template("coach.html")


@app.route("/bio", methods=["GET", "POST"])
@login_required
def bio():
    """bio"""
    return render_template("bio.html")


@app.route("/target", methods=["GET", "POST"])
@login_required
def target():
    """Target"""
    return render_template("target.html")


@app.route("/gym", methods=["GET", "POST"])
@login_required
def gym():
    """Configure Gyms"""
    return render_template("gym.html")