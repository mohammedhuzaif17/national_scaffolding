#!/usr/bin/env python3
"""
Hash a plain password and update admin accounts with it
"""
import os
os.environ['FLASK_ENV'] = 'development'

# Must set this BEFORE importing app
os.environ['WERKZEUG_RUN_MAIN'] = 'true'

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

# Get the database URL
db_uri = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')

if not db_uri:
    print("ERROR: DATABASE_URL not set!")
    exit(1)

# Normalize the URL
if db_uri.startswith('postgres://'):
    db_uri = db_uri.replace('postgres://', 'postgresql+psycopg2://', 1)
elif db_uri.startswith('postgresql://') and 'psycopg2' not in db_uri:
    db_uri = db_uri.replace('postgresql://', 'postgresql+psycopg2://', 1)

# Create Flask app and database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Import models
from models import Admin

with app.app_context():
    print("=" * 70)
    print("ADMIN PASSWORD HASHING AND UPDATE")
    print("=" * 70 + "\n")
    
    # Get both admins
    fab_admin = Admin.query.filter_by(panel_type='fabrication').first()
    scaf_admin = Admin.query.filter_by(panel_type='scaffolding').first()
    
    if not fab_admin or not scaf_admin:
        print("ERROR: Could not find both admin accounts!")
        exit(1)
    
    # Ask for the password
    print("What plain password do you want to use for both admins?")
    plain_password = input("Enter password: ").strip()
    
    if not plain_password:
        print("ERROR: Password cannot be empty!")
        exit(1)
    
    print(f"\nHashing password: {plain_password}")
    
    # Hash the password
    hashed = generate_password_hash(plain_password, method='pbkdf2:sha256')
    
    print(f"\nGenerated hash: {hashed[:50]}...\n")
    
    # Update both admins with the same hashed password
    fab_admin.password_hash = hashed
    scaf_admin.password_hash = hashed
    
    db.session.commit()
    
    print("=" * 70)
    print("SUCCESS! Passwords updated")
    print("=" * 70)
    print("\nBoth admin accounts now have:")
    print(f"  Username: admin")
    print(f"  Password: {plain_password}")
    print("\nYou can now login to either panel!")
