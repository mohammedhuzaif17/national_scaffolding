#!/usr/bin/env python3
"""Get full password details for both admins"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

cur.execute("""
    SELECT id, username, panel_type, password_hash 
    FROM admins 
    ORDER BY panel_type
""")

rows = cur.fetchall()

print("\n" + "="*70)
print("ADMIN PASSWORD ANALYSIS")
print("="*70)

for admin_id, username, panel_type, pwd_hash in rows:
    print(f"\n{panel_type.upper()} ADMIN (ID: {admin_id})")
    print(f"  Username: {username}")
    print(f"  Full Password Hash:")
    print(f"  {pwd_hash}")

print("\n" + "="*70)
print("KEY FINDING:")
print("="*70)

if rows[0][3] != rows[1][3]:
    print("\n⚠️  DIFFERENT PASSWORDS DETECTED!")
    print(f"\nFabrication admin has ONE password")
    print(f"Scaffolding admin has a DIFFERENT password")
    print("\nYou need to:")
    print("1. Try a different password for scaffolding admin")
    print("2. Or reset the scaffolding admin password in Neon database")
else:
    print("\n✓ Both admins have the SAME password")

cur.close()
conn.close()
