import os
import io
import base64
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from cs50 import SQL
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///momentum.db")


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

    # User reached route via POST
    if request.method == "POST":

        try:
            username = request.form.get("username")
            password = request.form.get("password")
            confirmation = request.form.get("confirmation")

            # Ensure username and password submitted
            if not username or not password or not confirmation:
                return render_template("register.html", message="Empty textbox")

            # Ensure password confirmation matches intial password entry
            elif password != confirmation:
                return render_template("register.html", message="Passwords do not match")

            # Try to insert information into database. UNIQUE INDEX on users.username
            db.execute(
                "INSERT INTO users (username, hash) VALUES (?, ?)", username, generate_password_hash(password)
            )

            # Log in with session
            user_id = db.execute(
                "SELECT id FROM users WHERE username = ?", username
            )

            # Session
            session["user_id"] = user_id[0]["id"]
            return redirect("/")

        except Exception:
            return render_template("register.html", message="Username already exists")
    
    # User reached route via GET
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        # Ensure username and password submitted
        if not username or not password:
            return render_template("login.html", message="Empty textbox")

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", username
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], password
        ):
            return render_template("login.html", message="Invalid username and password combination")

        try:
            # Remember which user has logged in
            session["user_id"] = rows[0]["id"]

        except TypeError as e:
            return render_template("login.html", message=f"ERROR: {e}")

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Landing page"""

    # Set user for current session
    user = session["user_id"]

    # Get the username
    username = db.execute(
        "SELECT username FROM users WHERE id = (?)", user
    )[0]["username"]
    
    return render_template("index.html", username=username)
    

@app.route("/post", methods=["GET", "POST"])
@login_required
def post():
    """Post a new workout"""

    # Current user
    user = session["user_id"]

    # User reached route via POST
    if request.method == "POST":

        # Get user input
        date = request.form.get("date")
        year, month, day = date.split("-")
        title = request.form.get("title")
        description = request.form.get("description")
        file = request.files['image']
        
        # If an image was uploaded
        if file.filename != '':
            file_path = os.path.join('static', 'uploads', file.filename)
            if not os.path.exists(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))
            file.save(file_path)
        
        # If no image was uploaded    
        else:
            file_path = ''
            
        # Insert data into the workouts table
        db.execute(
            "INSERT INTO workouts (user_id, date, year, month, day, title, description, image) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", user, date, year, month, day, title, description, file_path
        )            

        return redirect("/progress")
    
    # User reached route via GET
    return render_template("post.html")


@app.route("/team", methods=["GET", "POST"])
@login_required
def team():
    """Team"""

    # set user for current session
    user = session["user_id"] 

    # If a user is on a team:
    team_query = db.execute(
        "SELECT memberships.team_id, teams.name FROM memberships JOIN teams ON teams.id = memberships.team_id  WHERE memberships.user_id = (?)", user
    )

    if len(team_query) == 1:

        team_name = team_query[0]["name"]

        team_id = team_query[0]["team_id"]
        # retrieve team workouts
        workouts = db.execute(
            "SELECT * FROM workouts JOIN users ON workouts.user_id = users.id WHERE users.id IN (SELECT user_id FROM memberships WHERE team_id = ?) ORDER BY workouts.date DESC, workouts.id DESC", team_id)
        # render team page
        return render_template("team.html", workouts=workouts, team_name=team_name)
    
    else:
        # allow a user to Join a team through a form 
        return render_template("no_team.html")
    

@app.route("/no_team", methods=["GET", "POST"])
@login_required
def no_team():
    """no team"""

    return render_template("no_team.html")


@app.route("/join", methods=["GET", "POST"])
@login_required
def join():
    """join"""

    # Current user
    user = session["user_id"] 

    # User reached route via POST
    if request.method == "POST":

        try: 
            team_name = request.form.get("team name")
            join_code = request.form.get("join code")

            team_query = db.execute(
                "SELECT id, join_code FROM teams WHERE name = ?", team_name
            )

            # Team and join code combination doesn't exist
            if len(team_query) == 0:
                return render_template("join.html", message="Invalid team name and join code combination")

            query_join_code = team_query[0]["join_code"]
            query_team_id = team_query[0]["id"]
            
            print(f"Inserting team_id: {query_team_id}, user_id: {user}")

            # if join code valid, add membership
            if query_join_code == join_code:    
                db.execute(
                    "INSERT INTO memberships (team_id, user_id) VALUES (?, ?)", query_team_id, user
                )

            else:
                return render_template("join.html", message="Invalid join code")
            
            return redirect("/team")
        
        except Exception as e: 
            print(f"Error: {e}")
            return render_template("error.html")
    # User reached route via GET
    return render_template("join.html")



@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    """create"""
    # User reached route via POST
    if request.method == "POST":
        try:
            team_name = request.form.get("team name")
            join_code = request.form.get("join code")
            confirm_code = request.form.get("confirm") 

            if team_name is None or join_code is None:
                return render_template("create.html", message="Empty textbox")

            if join_code == confirm_code:
                db.execute(
                    "INSERT INTO teams (name, join_code) VALUES (?, ?)", team_name, join_code
                )
            
            else:
                return render_template("create.html", message="Join codes do not match")

            return redirect("/join")

        except ValueError as e:
            print(f"Error: {e}")
            return render_template("create.html", message="Team name already exists")
    # User reached route via GET
    return render_template("create.html")



@app.route("/progress", methods=["GET", "POST"])
@login_required
def progress():
    """progress"""

    # set user for current session
    user = session["user_id"]

    # retrieve user's username for header
    username = db.execute(
        "SELECT username FROM users WHERE id = (?)", user
    )[0]["username"]

    # Prepare data
    month_counts = db.execute("SELECT month, count(id) AS count FROM workouts WHERE user_id = (?) AND year = 2025 GROUP BY user_id, month", user)
    month_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    data = {month: 0 for month in month_list}

    for count in month_counts:
        abbrev = month_list[int(count["month"]) - 1]
        data[abbrev] = count["count"]
    
    # table
    workouts = db.execute(
        "SELECT * FROM workouts WHERE user_id = (?) ORDER BY date DESC, id DESC", user
    )

    # Send data to frontend
    return render_template("progress.html", data=data, username=username, workouts=workouts, month_list=month_list)