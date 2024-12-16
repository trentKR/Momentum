import os
import sqlite3
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/")
def index():
    """Landing page"""
    return render_template("index.html", methods=["GET", "POST"])

@app.route("/progress")
def progress():
    """Progress"""
    return render_template("progress.html")

@app.route("/team", methods=["GET", "POST"])
def team():
    """Team"""
    return render_template("team.html")

@app.route("/coach", methods=["GET", "POST"])
def coach():
    """Coach"""
    return render_template("coach.html")

@app.route("/bio", methods=["GET", "POST"])
def bio():
    """bio"""
    return render_template("bio.html")

@app.route("/target", methods=["GET", "POST"])
def target():
    """Target"""
    return render_template("target.html")

@app.route("/gym", methods=["GET", "POST"])
def gym():
    """Configure Gyms"""
    return render_template("gym.html")