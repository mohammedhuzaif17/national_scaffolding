#!/usr/bin/env python3
"""
Check admin credentials directly in Neon database
"""
import os

# Get database URL from environment (same as app.py does)
db_url = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')

if not db_url:
    print("❌ ERROR: DATABASE_URL not set in environment!")
    print("\nSet it with: $env:DATABASE_URL='your_url'")
    exit(1)

# Extract connection string without +psycopg2 for psycopg2
pg_url = db_url.replace('postgresql+psycopg2://', 'postgresql://')

try:
    import psycopg2
    
    # Add SSL mode
    if '?' not in pg_url:
        pg_url += '?sslmode=require'
    elif 'sslmode' not in pg_url:
        pg_url += '&sslmode=require'
    
    conn = psycopg2.connect(pg_url)
    cursor = conn.cursor()
    
    print("=" * 70)
    print("ADMIN CREDENTIALS IN NEON DATABASE")
    print("=" * 70 + "\n")
    
    # Query all admins
    cursor.execute("""
        SELECT id, username, panel_type, password_hash 
        FROM admins 
        ORDER BY panel_type, username
    """)
    
    rows = cursor.fetchall()
    
    if not rows:
        print("❌ No admins found in database!\n")
        cursor.close()
        conn.close()
        exit(1)
    
    print(f"Found {len(rows)} admin(s):\n")
    
    for row_id, username, panel_type, pwd_hash in rows:
        print(f"ID: {row_id}")
        print(f"  Username: {username}")
        print(f"  Panel: {panel_type}")
        print(f"  Password: {pwd_hash}")
        
        # Check if it's hashed
        if pwd_hash.startswith('pbkdf2:') or pwd_hash.startswith('bcrypt:'):
            print(f"  ✓ Status: PROPERLY HASHED")
        else:
            print(f"  ⚠️  Status: PLAIN PASSWORD (NOT HASHED!) - This is the problem!")
        print()
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    exit(1)
