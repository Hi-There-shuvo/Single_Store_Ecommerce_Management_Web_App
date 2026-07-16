#!/usr/bin/env bash
# =============================================================
# build.sh — Render Build Script
# This runs automatically on every deploy on Render.
# =============================================================

set -o errexit  # Exit immediately on any error

# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Collect static files (WhiteNoise will serve them)
python manage.py collectstatic --no-input

# 3. Run database migrations (applies to Neon PostgreSQL)
python manage.py migrate
