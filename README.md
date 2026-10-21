# Quiz Platform

**Live:** https://nasser-exam.duckdns.org

A cybersecurity course quiz platform built from scratch with Flask, used to learn secure web development and a full DevSecOps workflow.

Students can create an account, take chapter quizzes, see their score, and track their past results.

> **Status:** The application is containerized and runs on a hardened AWS server, publicly available over HTTPS, with automatic deployment.

## Security

Each protection below was tested by attempting the attack first, then fixing it and adding a test that proves it holds.

| Threat | Protection |
|---|---|
| SQL injection | Parameterized queries everywhere |
| Cross-site scripting (XSS) | Jinja auto-escaping, strict username pattern |
| Cross-site request forgery (CSRF) | Flask-WTF tokens on every form, SameSite cookies |
| Accessing other users' data | User identity taken from the signed session only, never from the request |
| Password theft | Passwords stored as salted scrypt hashes |
| User enumeration | One generic error message for failed logins |
| Leaked secrets | Secrets in `.env` (ignored), Gitleaks before every commit and in CI |
| Bad data | Input allow-lists in the app, plus `NOT NULL`, `UNIQUE`, `CHECK`, and foreign keys in the database |
| Damage after a compromised app | App connects with a least-privilege database user (read and insert only); schema changes run in a separate one-shot migrate container |
| Clickjacking and injected scripts | Security headers on every response (CSP, frame-ancestors, nosniff), verified by ZAP in CI |

## Server hardening

The app runs on an AWS EC2 instance (Ubuntu LTS, t3.micro). The server is hardened with a repeatable script in `infra/`.

| Layer | What it does |
|---|---|
| AWS security group | SSH reachable only from known IP ranges; HTTP and HTTPS open to all |
| SSH | Key-only login, no root login, single allowed user, limited auth tries and sessions |
| UFW | Deny all incoming except rate-limited SSH, HTTP and HTTPS |
| Fail2ban | Bans IPs after repeated failed SSH logins |
| Updates | Automatic security updates enabled |

Audited before and after with Lynis and [VaultCtl](https://github.com/NasserS12/Vaultctl):

| | Lynis hardening index | Warnings |
|---|---|---|
| Fresh server | 57 | 1 (vulnerable package) |
| After hardening | 70 | 0 |

**Decisions:**
- SSH stays on port 22. Changing it is security through obscurity, and the security group already blocks unknown sources.
- SSH two-factor authentication is not added yet. Deployment does not use SSH, so it can be added later without breaking anything.

To harden a new server:

```bash
scp -r infra ubuntu@SERVER_IP:~
ssh ubuntu@SERVER_IP
sudo bash ~/infra/harden-server.sh
```

## Deployment

On a hardened server:

```bash
git clone https://github.com/NasserS12/Exam_project.git
cd Exam_project
git switch dev
sudo bash infra/install-docker.sh

cp .env.example .env
# Fill .env with new secrets, different from development
chmod 600 .env

sudo docker compose up -d --build
```

### Automatic deployment

The server pulls updates itself instead of GitHub pushing to it. A systemd timer runs `infra/deploy.sh` every 2 minutes. The script checks if `dev` has new commits, and if so, pulls them and rebuilds the containers.

- No inbound access is opened for deployment, and no server credentials are stored in GitHub.
- Only tested code is deployed, since `dev` is protected and accepts merges only after all checks pass.
- The script refuses to deploy if the server has local changes (`git merge --ff-only`).

To enable it:

```bash
sudo cp infra/quiz-deploy.service infra/quiz-deploy.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now quiz-deploy.timer
```

To see deployment logs:

```bash
journalctl -u quiz-deploy.service
```

### HTTPS

Nginx sits in front of the app as a reverse proxy. The app listens on `127.0.0.1:8000` only, so it is not reachable from outside directly.

- Domain: DuckDNS
- Certificate: Let's Encrypt (certbot), renewed automatically
- HTTP requests are redirected to HTTPS
- Session cookie is sent over HTTPS only (`SESSION_COOKIE_SECURE=1` in the server `.env`)

To apply the Nginx config:

```bash
sudo cp infra/nginx-quiz.conf /etc/nginx/sites-available/quiz
sudo nginx -t
sudo systemctl reload nginx
```

## Engineering workflow

- **Git Flow:** feature branches merged into `dev` through pull requests; `main` for releases.
- **Protected branches:** no merge without passing checks.
- **CI on every pull request:**
  - Container image: Trivy (fails on fixable high and critical vulnerabilities)
  - Running app: OWASP ZAP baseline scan (fails on any new warning)
  - Quality: Ruff, pytest
  - Security: Bandit, pip-audit, Gitleaks (full history)
- **Continuous deployment:** the server deploys new commits on `dev` automatically.
- **Pre-commit hooks:** Ruff and Gitleaks run locally before every commit.
- **Isolated tests:** each test runs on a freshly reset PostgreSQL database, in a local container and as a CI service container.
- **Agile:** weekly sprints on a GitHub Projects board, each task linked to its pull request.

## Tech stack

Python, Flask, Jinja, PostgreSQL, pytest, GitHub Actions, Docker, Docker Compose, gunicorn, Trivy, AWS EC2, Nginx, Let's Encrypt, systemd

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
- [x] Hardened cloud server
- [x] HTTPS with Nginx and Let's Encrypt
- [x] Container image scanning in CI
- [x] Automatic deployment
- [x] Dynamic security testing with OWASP ZAP
- [ ] Monitoring with Grafana
