import os
import io
import base64
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
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


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Landing page"""
    return render_template("index.html")


@app.route("/post", methods=["GET", "POST"])
@login_required
def post():
    """Post a new workout"""

    # set user for current session
    user = session["user_id"]

    # if POST method
    if request.method == "POST":

        # Get user input
        date = request.form.get("date")
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
            
        # Insert data into the database
        db.execute("INSERT INTO workouts (user_id, date, title, description, image) VALUES (?, ?, ?, ?, ?)", user, date, title, description, file_path)            
        return render_template("progress.html")
    
    # If GET method
    return render_template("post.html")


@app.route("/team", methods=["GET", "POST"])
@login_required
def team():
    """Team"""

    # set user for current session
    user = session["user_id"]

    # retrieve user's workouts
    workouts = db.execute("SELECT * FROM workouts JOIN users ON users.id = workouts.user_id ORDER BY workouts.date DESC, workouts.id DESC")

    # render team page
    return render_template("team.html", workouts=workouts)


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    """Account"""
    return render_template("account.html")


@app.route("/progress", methods=["GET", "POST"])
@login_required
def progress():
    """progress"""

    # set user for current session
    user = session["user_id"]

    # retrieve user's username for header
    username = db.execute("SELECT username FROM users WHERE id = (?)", user)[0]["username"]

    # retrieve user's workouts to populate data 
    workouts = db.execute("SELECT id, date FROM workouts WHERE user_id = (?) ORDER BY date DESC", user)

    # create plot
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    data = {'Jan': 0, 'Feb': 0, 'Mar': 0, 'Apr': 0, 'May': 0, 'Jun': 0, 'Jul': 0, 'Aug': 0, 'Sep': 0, 'Oct': 0, 'Nov': 0, 'Dec': 0}
    
    # iterate over workouts table
    for workout in workouts:
        
        # get the date of workout
        date_str = workout["date"]
        
        # parse the date string
        year, month_int, day = date_str.split("-")
        
        # month abbrev
        month_abb = months[int(month_int) - 1]
        
        # populate data dictionary
        data[month_abb] += 1  

    y = [data[month] for month in months]

    plt.bar(months, y, color='blue')

    # add counts above the bars
    for i, value in enumerate(y):
        if value != 0:
            plt.text(i, value, str(value), ha='center')

    plt.xticks(ticks=range(0, 12), labels=months)
    plt.yticks(ticks=[], label=workouts)
    plt.ylim(0, 35)
    plt.title(f"Workouts in 2025")

    # save the plot to a BytesIO object so that do not have to save as an image
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri = 'data:image/png;base64,' + string.decode('utf-8')

    # render progress page
    return render_template("progress.html", username=username, uri=uri, workouts=workouts)