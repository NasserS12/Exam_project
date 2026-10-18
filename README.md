# Quiz Platform

A cybersecurity course quiz platform built from scratch with Flask, used to learn secure web development and a full DevSecOps workflow.

Students can create an account, take chapter quizzes, see their score, and track their past results.

> **Status:** The application is feature-complete for its first version. Containerization and deployment are in progress.

## Security

Each protection below was tested by attempting the attack first, then fixing it and adding a test that proves it holds.

| Threat | Protection |
|---|---|
| SQL injection | Parameterized queries everywhere |
| Damage after a compromised app | App connects with a least-privilege database user (read and insert only); schema changes run in a separate one-shot migrate container |
| Cross-site scripting (XSS) | Jinja auto-escaping, strict username pattern |
| Cross-site request forgery (CSRF) | Flask-WTF tokens on every form, SameSite cookies |
| Accessing other users' data | User identity taken from the signed session only, never from the request |
| Password theft | Passwords stored as salted scrypt hashes |
| User enumeration | One generic error message for failed logins |
| Leaked secrets | Secrets in `.env` (ignored), Gitleaks before every commit and in CI |
| Bad data | Input allow-lists in the app, plus `NOT NULL`, `UNIQUE`, `CHECK`, and foreign keys in the database |

## Engineering workflow

- **Git Flow:** feature branches merged into `dev` through pull requests; `main` for releases.
- **Protected branches:** no merge without passing checks.
- **CI on every pull request:**
  - Quality: Ruff, pytest
  - Security: Bandit, pip-audit, Gitleaks (full history)
- **Pre-commit hooks:** Ruff and Gitleaks run locally before every commit.
- **Isolated tests:** each test runs on a freshly reset PostgreSQL database, in a local container and as a CI service container.
- **Agile:** weekly sprints on a GitHub Projects board, each task linked to its pull request.

## Tech stack

Python, Flask, Jinja, PostgreSQL, pytest, GitHub Actions, Docker, Docker Compose, gunicorn

## Getting started

```bash
git clone https://github.com/NasserS12/Exam_project.git
cd Exam_project
cp .env.example .env
python3 -c "import secrets; print(secrets.token_hex(32))"
# Paste the generated key into SECRET_KEY in .env
```

### Run with Docker Compose

Fill in `.env` with two different strong passwords: one for the database admin (`POSTGRES_PASSWORD`) and one for the app user (`APP_DB_PASSWORD`). Then:
```bash
docker compose up -d --build
```

Open http://127.0.0.1:8000

## Running checks locally

Start a disposable PostgreSQL container for the tests:

```bash
docker run -d --name quiz-test-db -e POSTGRES_USER=test -e POSTGRES_PASSWORD=test -e POSTGRES_DB=test -p 127.0.0.1:5433:5432 postgres:17-alpine
```

Then set up the environment and run the checks:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt pytest ruff bandit pip-audit pre-commit
pre-commit install

python -m pytest tests/ -v
ruff check .
bandit -r . -c pyproject.toml
pip-audit -r requirements.txt
```


## Roadmap

- [x] Quiz by chapter, scoring, accounts, results history
- [x] Protection against SQL injection, XSS, CSRF, and access to other users' data
- [x] Pre-commit hooks
- [x] Docker and Docker Compose with secrets management
- [x] PostgreSQL with persistent storage
- [ ] Container image scanning in CI
- [ ] Hardened cloud server with automatic deployment
- [ ] Dynamic security testing with OWASP ZAP
- [ ] Monitoring with Grafana
