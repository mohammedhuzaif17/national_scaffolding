#!/usr/bin/env python3
"""Check admin passwords in Neon database"""

import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

db_url = os.getenv('DATABASE_URL')

if not db_url:
    print("[ERROR] DATABASE_URL not found")
    exit(1)

try:
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("CHECKING ADMIN ACCOUNTS IN NEON DATABASE")
    print("="*70)
    
    # Get all admin accounts
    cursor.execute("""
        SELECT id, username, panel_type, password_hash 
        FROM admins 
        ORDER BY panel_type;
    """)
    
    rows = cursor.fetchall()
    
    print(f"\nTotal admin accounts: {len(rows)}\n")
    
    for admin_id, username, panel_type, pwd_hash in rows:
        print(f"Admin ID: {admin_id}")
        print(f"  Username: {username}")
        print(f"  Panel: {panel_type}")
        print(f"  Password Hash: {pwd_hash[:60]}...")
        print(f"  Hash length: {len(pwd_hash)}")
        print()
    
    # Compare hashes
    if len(rows) >= 2:
        hash1 = rows[0][3]
        hash2 = rows[1][3]
        
        print("="*70)
        print("PASSWORD HASH COMPARISON")
        print("="*70)
        print(f"\nAre the hashes the same? {hash1 == hash2}")
        
        if hash1 != hash2:
            print("\n[ISSUE FOUND] The two admin accounts have DIFFERENT password hashes!")
            print("This means they have different passwords.")
            print("\nYou need to:")
            print("1. Set the same password for both scaffolding and fabrication admins")
            print("2. OR set different passwords and remember which one for each panel")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"[ERROR] {str(e)}")
    exit(1)
