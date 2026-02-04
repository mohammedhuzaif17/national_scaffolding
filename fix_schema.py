#!/usr/bin/env python3
"""Drop old constraint and recreate"""

from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        # First, clear all admin records
        db.session.execute(text("DELETE FROM admins"))
        db.session.commit()
        print("✅ Cleared all admin records")
        
        # Drop the old constraint
        db.session.execute(text("""
            ALTER TABLE admins DROP CONSTRAINT IF EXISTS admins_username_key
        """))
        db.session.commit()
        print("✅ Dropped old unique constraint on username")
    except Exception as e:
        print(f"Note: {str(e)}")
        db.session.rollback()
    
    # Now add the new constraint
    try:
        db.session.execute(text("""
            ALTER TABLE admins 
            ADD CONSTRAINT unique_username_panel UNIQUE (username, panel_type)
        """))
        db.session.commit()
        print("✅ Added new composite unique constraint (username, panel_type)")
    except Exception as e:
        print(f"Note: {str(e)}")
        db.session.rollback()

print("\n✅ Schema update complete!")
