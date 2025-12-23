from app import app, db, Admin

with app.app_context():
    try:
        # Find and delete dummy admin accounts
        dummy_admins = [
            'admin_scaffolding',
            'admin_fabrication'
        ]
        
        deleted_count = 0
        for username in dummy_admins:
            admin = Admin.query.filter_by(username=username).first()
            if admin:
                db.session.delete(admin)
                deleted_count += 1
                print(f"Deleted dummy admin: {username}")
        
        if deleted_count > 0:
            db.session.commit()
            print(f"Successfully deleted {deleted_count} dummy admin accounts")
        else:
            print("No dummy admin accounts found")
            
    except Exception as e:
        print(f"Error deleting dummy admins: {e}")
        db.session.rollback()