#!/usr/bin/env python3
import psycopg2
import os

# Neon database connection - read from environment like app.py does
db_url = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')
if not db_url:
    print("❌ ERROR: DATABASE_URL not set in environment!")
    exit(1)
# Ensure SSL is required
if '?' not in db_url:
    db_url += '?sslmode=require'
elif 'sslmode' not in db_url:
    db_url += '&sslmode=require'

try:
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    print("=" * 70)
    print("RESETTING SCAFFOLDING ADMIN PASSWORD")
    print("=" * 70)
    
    # Get fabrication admin password hash
    cursor.execute("""
        SELECT password_hash FROM admins WHERE username='admin' AND panel_type='fabrication'
    """)
    result = cursor.fetchone()
    if not result:
        print("❌ ERROR: Fabrication admin not found!")
        cursor.close()
        conn.close()
        exit(1)
    
    fabrication_hash = result[0]
    print(f"\n✓ Fabrication admin password hash found")
    
    # Update scaffolding admin password to match
    cursor.execute("""
        UPDATE admins 
        SET password_hash = %s 
        WHERE username='admin' AND panel_type='scaffolding'
    """, (fabrication_hash,))
    
    conn.commit()
    
    # Verify update
    cursor.execute("""
        SELECT username, panel_type, password_hash FROM admins 
        WHERE username='admin' 
        ORDER BY panel_type
    """)
    rows = cursor.fetchall()
    
    print("\n" + "=" * 70)
    print("UPDATED ADMIN ACCOUNTS:")
    print("=" * 70)
    for username, panel_type, pwd_hash in rows:
        print(f"\n{panel_type.upper()} Admin:")
        print(f"  Username: {username}")
        print(f"  Password hash: {pwd_hash[:30]}...{pwd_hash[-10:]}")
    
    # Check if passwords match now
    cursor.execute("""
        SELECT COUNT(DISTINCT password_hash) FROM admins WHERE username='admin'
    """)
    count = cursor.fetchone()[0]
    
    print("\n" + "=" * 70)
    if count == 1:
        print("✅ SUCCESS! Both admins now have the SAME password")
        print("=" * 70)
        print("\nYou can now login to BOTH panels with:")
        print("  Username: admin")
        print("  Password: [your fabrication password]")
    else:
        print("⚠️  WARNING: Passwords are still different!")
        print("=" * 70)
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    exit(1)
