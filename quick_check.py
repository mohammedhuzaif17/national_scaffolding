#!/usr/bin/env python3
"""Quick check of admin accounts"""
import os
os.environ['FLASK_ENV'] = 'production'  # Disable reloader

from app import app, db
from models import Admin

with app.app_context():
    scaff = Admin.query.filter_by(username='admin', panel_type='scaffolding').first()
    fab = Admin.query.filter_by(username='admin', panel_type='fabrication').first()
    
    print(f"Scaffolding admin password check: {scaff.check_password('admin123') if scaff else 'NOT FOUND'}")
    print(f"Fabrication admin password check: {fab.check_password('admin123') if fab else 'NOT FOUND'}")
