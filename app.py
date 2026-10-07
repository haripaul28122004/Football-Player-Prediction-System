import hashlib
import hmac
import os
import re
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database.db"
FOOTBALL_DATA_URL = "https://api.football-data.org/v4/competitions"

load_dotenv(BASE_DIR / ".env")
app = Flask(__name__)
secret_key = os.getenv("FLASK_SECRET_KEY")
if not secret_key:
    raise RuntimeError("Set FLASK_SECRET_KEY in your local .env file before starting Flask.")
app.config["SECRET_KEY"] = secret_key
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

PASSWORD_HASH_ITERATIONS = 600_000


@contextmanager
def get_db_connection():
    """Open a SQLite connection and return rows as dictionaries."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    except Exception:
        connection.rollback()
        raise
    else:
        connection.commit()
    finally:
        connection.close()


def initialize_database():
    """Create the user-account and prediction tables if they do not exist."""
    with get_db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL UNIQUE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                age INTEGER NOT NULL,
                matches INTEGER NOT NULL,
                goals INTEGER NOT NULL,
                assists INTEGER NOT NULL,
                shots INTEGER NOT NULL,
                pass_accuracy REAL NOT NULL,
                performance_score INTEGER NOT NULL,
                performance_level TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def hash_password(password, salt):
    """Derive a PBKDF2-HMAC-SHA256 password hash from a password and salt."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_HASH_ITERATIONS,
    )


def password_validation_error(password):
    """Require a reasonably long password containing letters and numbers."""
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if len(password) > 128:
        return "Password must be no more than 128 characters long."
    if not any(character.isalpha() for character in password):
        return "Password must include at least one letter."
    if not any(character.isdigit() for character in password):
        return "Password must include at least one number."
    return None


def valid_csrf_token():
    """Check the form token before handling account-changing requests."""
    submitted_token = request.form.get("csrf_token", "")
    session_token = session.get("csrf_token", "")
    return bool(session_token) and hmac.compare_digest(submitted_token, session_token)


@app.context_processor
def inject_csrf_token():
    """Make one session-bound CSRF token available to HTML forms."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return {"csrf_token": session["csrf_token"]}


def calculate_performance(matches, goals, assists, shots, pass_accuracy):
    """Return a simple 0-100 score and level from per-match statistics."""
    goals_points = min((goals / matches) / 0.5, 1) * 30
    assists_points = min((assists / matches) / 0.5, 1) * 20
    shots_points = min((shots / matches) / 4, 1) * 15
    passing_points = (pass_accuracy / 100) * 35

    score = round(goals_points + assists_points + shots_points + passing_points)
    if score >= 80:
        level = "Excellent"
    elif score >= 60:
        level = "Good"
    elif score >= 40:
        level = "Average"
    else:
        level = "Poor"

    return score, level


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if not valid_csrf_token():
            flash("Your form session expired. Please try again.", "danger")
            return redirect(url_for("register"))

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirmation = request.form.get("confirm_password", "")

        if not re.fullmatch(r"[A-Za-z0-9_]{3,30}", username):
            flash("Username must be 3–30 characters using letters, numbers, or underscores.", "danger")
        elif error := password_validation_error(password):
            flash(error, "danger")
        elif password != confirmation:
            flash("The passwords do not match.", "danger")
        else:
            # Check the database as well as using random bytes so salts stay unique.
            with get_db_connection() as connection:
                existing_salts = {
                    row["salt"]
                    for row in connection.execute("SELECT salt FROM users").fetchall()
                }
            salt = os.urandom(16)
            while salt.hex() in existing_salts:
                salt = os.urandom(16)
            password_hash = hash_password(password, salt).hex()
            try:
                with get_db_connection() as connection:
                    connection.execute(
                        "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
                        (username, password_hash, salt.hex()),
                    )
                flash("Account created. You can now log in.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("That username is already registered.", "danger")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if not valid_csrf_token():
            flash("Your form session expired. Please try again.", "danger")
            return redirect(url_for("login"))

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        with get_db_connection() as connection:
            user = connection.execute(
                "SELECT username, password_hash, salt FROM users WHERE username = ?",
                (username,),
            ).fetchone()

        if user is None or len(password) > 128:
            flash("Username or password is incorrect.", "danger")
        else:
            salt = bytes.fromhex(user["salt"])
            entered_hash = hash_password(password, salt).hex()
            if hmac.compare_digest(entered_hash, user["password_hash"]):
                session.clear()
                session["username"] = user["username"]
                flash("You are now logged in.", "success")
                return redirect(url_for("prediction"))
            flash("Username or password is incorrect.", "danger")

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    if not valid_csrf_token():
        flash("Your form session expired. Please try again.", "danger")
        return redirect(url_for("home"))

    session.clear()
    flash("You are now logged out.", "success")
    return redirect(url_for("home"))


@app.route("/prediction")
def prediction():
    return render_template("prediction.html")


@app.route("/predict", methods=["POST"])
def predict():
    player_name = request.form.get("player_name", "").strip()

    try:
        age = int(request.form.get("age", ""))
        matches = int(request.form.get("matches", ""))
        goals = int(request.form.get("goals", ""))
        assists = int(request.form.get("assists", ""))
        shots = int(request.form.get("shots", ""))
        pass_accuracy = float(request.form.get("pass_accuracy", ""))
    except (TypeError, ValueError):
        return render_template(
            "prediction.html", error="Please enter valid numbers in every statistics field."
        ), 400

    if not player_name:
        error = "Please enter the player's name."
    elif not 15 <= age <= 60:
        error = "Age must be between 15 and 60."
    elif matches < 1:
        error = "Matches played must be at least 1."
    elif min(goals, assists, shots) < 0:
        error = "Goals, assists, and shots cannot be negative."
    elif goals > shots:
        error = "Goals cannot be greater than shots."
    elif not 0 <= pass_accuracy <= 100:
        error = "Pass accuracy must be from 0 to 100."
    else:
        error = None

    if error:
        return render_template("prediction.html", error=error), 400

    score, level = calculate_performance(matches, goals, assists, shots, pass_accuracy)
    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO predictions
                (player_name, age, matches, goals, assists, shots,
                 pass_accuracy, performance_score, performance_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (player_name, age, matches, goals, assists, shots,
             pass_accuracy, score, level),
        )

    return render_template(
        "result.html",
        player_name=player_name,
        age=age,
        matches=matches,
        goals=goals,
        assists=assists,
        shots=shots,
        pass_accuracy=pass_accuracy,
        score=score,
        level=level,
    )


@app.route("/football-data")
def football_data():
    """Fetch competition data from football-data.org using a private API token."""
    api_token = os.getenv("API_TOKEN", "").strip()
    if not api_token or api_token == "YOUR_API_TOKEN":
        return render_template(
            "football_data.html",
            error="Add your football-data.org token to the API_TOKEN value in the .env file, then restart Flask.",
        )

    try:
        response = requests.get(
            FOOTBALL_DATA_URL,
            headers={"X-Auth-Token": api_token},
            timeout=10,
        )
        if response.status_code == 401:
            error = "The API rejected this token. Check that API_TOKEN is correct."
            return render_template("football_data.html", error=error), 401
        if response.status_code == 403:
            error = "This token does not have access to the requested competitions."
            return render_template("football_data.html", error=error), 403
        response.raise_for_status()
        competitions = response.json().get("competitions", [])
        return render_template("football_data.html", competitions=competitions)
    except requests.Timeout:
        error = "The football-data.org request timed out. Please try again."
    except requests.RequestException as exc:
        error = f"Could not reach football-data.org: {exc}"
    except ValueError:
        error = "The API returned data that could not be read. Please try again."

    return render_template("football_data.html", error=error), 502


initialize_database()


if __name__ == "__main__":
    app.run(debug=True)
