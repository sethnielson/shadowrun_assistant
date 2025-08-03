#!/bin/bash

# Deployment script for ShadowNexus
set -e

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Go into source directory
cd src

# Run migrations
python manage.py migrate

# Create superuser prompt
echo "Run 'python manage.py createsuperuser' if needed."

# Start server
echo "Starting development server on http://127.0.0.1:8000"
python manage.py runserver
