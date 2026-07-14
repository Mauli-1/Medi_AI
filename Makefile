# ════════════════════════════════════════════════════════════════════════════
#  MSMS — Makefile
#  Usage: make <target>
# ════════════════════════════════════════════════════════════════════════════

PYTHON    ?= python3
FLASK     ?= flask
PIP       ?= pip3
APP_ENV   ?= development

.DEFAULT_GOAL := help

.PHONY: help install run db-init db-migrate db-upgrade db-downgrade db-reset seed \
        shell lint clean test

# ── Help ─────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  MSMS — Medical Store Management System"
	@echo ""
	@echo "  Available targets:"
	@echo "    install       Install Python dependencies from requirements.txt"
	@echo "    run           Start the development server (port 5000)"
	@echo "    db-init       Initialise Flask-Migrate (creates migrations/ folder)"
	@echo "    db-migrate    Auto-generate a new migration from model changes"
	@echo "    db-upgrade    Apply pending migrations to the database"
	@echo "    db-downgrade  Roll back the last migration"
	@echo "    db-reset      Drop all tables and re-run all migrations (DEV ONLY)"
	@echo "    seed          Seed the database with sample / demo data"
	@echo "    shell         Open an interactive Flask shell"
	@echo "    lint          Run flake8 linter on the app package"
	@echo "    test          Run pytest"
	@echo "    clean         Remove .pyc files and __pycache__ directories"
	@echo ""

# ── Install ───────────────────────────────────────────────────────────────────
install:
	$(PIP) install -r requirements.txt

# ── Run ───────────────────────────────────────────────────────────────────────
run:
	FLASK_ENV=$(APP_ENV) $(PYTHON) run.py

# ── Database ──────────────────────────────────────────────────────────────────
db-init:
	FLASK_ENV=$(APP_ENV) $(FLASK) db init

db-migrate:
	FLASK_ENV=$(APP_ENV) $(FLASK) db migrate -m "auto migration"

db-upgrade:
	FLASK_ENV=$(APP_ENV) $(FLASK) db upgrade

db-downgrade:
	FLASK_ENV=$(APP_ENV) $(FLASK) db downgrade

db-reset:
	@echo "WARNING: This will drop all tables. Press Ctrl-C within 5 s to cancel."
	@sleep 5
	FLASK_ENV=$(APP_ENV) $(FLASK) shell -c \
		"from app.extensions import db; db.drop_all(); db.create_all(); print('Reset complete.')"

# ── Seed ─────────────────────────────────────────────────────────────────────
seed:
	FLASK_ENV=$(APP_ENV) $(PYTHON) -c " \
from app import create_app; \
from app.extensions import db; \
from app.models.user import User; \
app = create_app('development'); \
ctx = app.app_context(); ctx.push(); \
db.create_all(); \
if not User.query.filter_by(username='admin').first(): \
    u = User(username='admin', email='admin@msms.local', \
             full_name='System Administrator', role='super_admin', \
             is_active=True, is_verified=True); \
    u.set_password('Admin@1234'); \
    db.session.add(u); db.session.commit(); \
    print('Admin user created: admin / Admin@1234'); \
else: \
    print('Admin user already exists.'); \
ctx.pop() \
"

# ── Shell ─────────────────────────────────────────────────────────────────────
shell:
	FLASK_ENV=$(APP_ENV) $(FLASK) shell

# ── Lint ─────────────────────────────────────────────────────────────────────
lint:
	flake8 app/ --max-line-length=120 --exclude=migrations/

# ── Test ─────────────────────────────────────────────────────────────────────
test:
	FLASK_ENV=testing pytest tests/ -v

# ── Clean ─────────────────────────────────────────────────────────────────────
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned."
