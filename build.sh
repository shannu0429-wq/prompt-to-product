#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "==> Upgrading pip..."
pip install --upgrade pip

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Initializing Database Schema (MySQL)..."
python -c "
import os
from app import create_app
from app.extensions import db
app = create_app(os.getenv('FLASK_ENV', 'production'))
with app.app_context():
    try:
        db.create_all()
        print('Database tables verified/created successfully.')
    except Exception as e:
        print('Warning during db.create_all:', e)
"

echo "==> Seeding Initial Content and Settings..."
python -c "
import os
from app import create_app
from scripts.seed_data import run_seed
try:
    run_seed()
except Exception as e:
    print('Warning during seed:', e)
"

echo "==> Build complete!"
