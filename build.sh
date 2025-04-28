#!/bin/bash

# Exit on error
set -e

# Install Python dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Apply database migrations
python manage.py migrate

# Create necessary directories
mkdir -p media
mkdir -p logs
mkdir -p detector/models

# Set proper permissions
chmod -R 755 media
chmod -R 755 logs
chmod -R 755 detector/models