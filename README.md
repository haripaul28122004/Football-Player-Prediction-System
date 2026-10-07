# Football Player Prediction System

## Project

This is a simple Flask application created to demonstrate GitHub CI/CD for a college assignment. It includes a home endpoint and a health-check endpoint, with automated tests run through GitHub Actions.

## Technologies

- Python
- Flask
- Pytest
- Git
- GitHub
- GitHub Actions

## CI/CD

Continuous Integration (CI) automatically checks changes to a project. In this assignment, GitHub Actions installs the Python dependencies and runs pytest whenever code is pushed or a pull request is created. The test result is shown with the GitHub Actions workflow run.

## GitHub Actions Workflow

```text
Developer changes code
↓
Git push / Pull Request
↓
GitHub Actions starts
↓
Python environment setup
↓
Dependencies installed
↓
Pytest runs
↓
Build/CI result shown
```

## Run Locally

Create a virtual environment:

```bash
python -m venv .venv
```

Windows (PowerShell):

```powershell
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
python app.py
```

Open:

http://127.0.0.1:5000

## Testing

Run the tests locally:

```bash
python -m pytest -v
```

Make sure all tests pass before pushing.

## Git

Initialize Git and create the first commit:

```bash
git init
git branch -M main
git add .
git commit -m "Initial Flask CI/CD assignment"
```

## GitHub CLI

Check that GitHub CLI is installed and authenticated:

```bash
gh --version
gh auth status
```

## GitHub Repository

The intended public repository name is `Football-Player-Prediction-System`. If GitHub CLI is authenticated, create and push the public repository from this directory:

```bash
gh repo create Football-Player-Prediction-System --public --source=. --remote=origin --push
```

If that repository already exists, do not recreate or delete it. Safely connect this local project to the existing repository and push without force.
