# Football Player Performance Prediction System

A beginner-friendly Flask application that scores a player's season statistics, saves predictions and user accounts in SQLite, and displays competition data retrieved from football-data.org. GitHub Actions runs the automated tests on pushes and pull requests.

## Project files

- `app.py` — Flask routes, validation, scoring formula, API request, and SQLite setup.
- `templates/` — the homepage, prediction form, result page, API data page, and account pages.
- `static/css/style.css` — responsive football-themed design.
- `static/js/script.js` — small client-side form check.
- `database.db` — created automatically when the app starts; local database files are ignored by Git.
- `.env` — local API token and Flask session-secret configuration. Create this file for local use, keep it private, and never commit it.
- `.github/workflows/ci.yml` — CI workflow that installs dependencies and runs pytest.

## Requirements and installation

Use Python 3.10 or newer. In the VS Code terminal, change into this project directory, create and activate a virtual environment, then install the listed packages:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a local `.env` file in the project root before starting Flask. Set `API_TOKEN` to your football-data.org token and `FLASK_SECRET_KEY` to a long, random secret value. Do not commit or share `.env`. The application will not start without `FLASK_SECRET_KEY`; automated tests use a temporary test-only key and do not require a live API token.

If PowerShell blocks environment activation, run this once in that terminal and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Configure football-data.org

1. Create a free account at https://www.football-data.org/client/register and copy your API token.
2. Open `.env` and replace `YOUR_API_TOKEN` with the token. Do not add quotes and do not share or commit the file.
3. Stop and restart Flask after changing `.env`.

The football data page uses the token in the `X-Auth-Token` HTTP header. If you do not have a token yet, the prediction calculator still works; the API page explains the missing configuration.

## Run in VS Code

1. Open this project folder in VS Code.
2. Open **Terminal → New Terminal**.
3. Create/activate the environment and install requirements using the commands above.
4. Start the app with `python app.py` (or `py app.py`).
5. Open http://127.0.0.1:5000 in a browser. Leave the terminal running while using the site.

Flask creates `database.db` and its `predictions` table automatically at startup. Do not run the built-in debug server as a public production server.

## Try it

- **Prediction:** Open **Prediction**, enter a name and stats, and click **PREDICT PERFORMANCE**. The result page shows the score and performance level. Each valid result is saved to SQLite.
- **API:** Open **Football data** or visit http://127.0.0.1:5000/football-data. With a valid token, the page displays competitions returned by football-data.org. A 401 usually means the token is missing/incorrect; a 403 may mean the endpoint is not included in the token's access.
- **Accounts:** Open `/register` to create an account, then `/login` to sign in. Account links are available from the prediction, result, and football-data pages. Login establishes a Flask session; logout clears it. Existing prediction and API pages remain usable without signing in.

## Account security (Module 3)

- Usernames are 3–30 letters, numbers, or underscores.
- Passwords must be 8–128 characters and contain at least one letter and one number.
- Registration creates a random 16-byte salt for the user and derives a PBKDF2-HMAC-SHA256 hash using 600,000 iterations. SQLite stores only the username, hexadecimal password hash, and salt in the `users` table; it never stores the entered password.
- Login retrieves the stored salt, derives a fresh hash from the entered password using the same settings, and compares the hashes with a constant-time comparison.
- The Flask session signing key is loaded from `.env`, not written into the Python source. Keep `.env` private and use a long, random value for the session key. Account forms include a session-bound CSRF token.

## Scoring formula

All match-based stats are divided by matches played, then capped at their maximum point contribution:

- Goals per match: up to 30 points (full points at 0.5 goals per match).
- Assists per match: up to 20 points (full points at 0.5 assists per match).
- Shots per match: up to 15 points (full points at 4 shots per match).
- Pass accuracy: up to 35 points (the entered percentage is multiplied by 0.35).

Score levels: Excellent 80–100, Good 60–79, Average 40–59, Poor 0–39. This is a simple demonstration formula, not a professional scouting metric or machine-learning model.

## Common problems

- **`ModuleNotFoundError`:** Activate `.venv` and run `pip install -r requirements.txt` again.
- **`python`/`py` not found:** Install Python 3 from python.org and select it as the VS Code interpreter.
- **PowerShell will not activate `.venv`:** Use the process-only execution policy command above, or run `.venv\Scripts\activate.bat` in Command Prompt.
- **API page says token is missing:** Replace the placeholder in `.env`, save it, and restart Flask.
- **API returns 401/403:** Check the token and account access; do not put the token in HTML or JavaScript.
- **Port 5000 is busy:** Close the other app using it or change the port in the `app.run` line at the bottom of `app.py`.
- **Ronaldo photo does not load:** Check the internet connection. The home page uses an externally hosted Wikimedia Commons photo.
