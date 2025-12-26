from app import app, db
from models import Admin

def create_admin(username, password, role):
    with app.app_context():
        existing = Admin.query.filter_by(username=username).first()
        if existing:
            print("❌ Admin already exists")
            return

        admin = Admin(
            username=username,
            role=role
        )
        admin.set_password(password)

        db.session.add(admin)
        db.session.commit()
        print("✅ Admin created successfully")

if __name__ == "__main__":
    create_admin(
        username="national_admin",
        password="Scaffold@123",
        role="scaffolding"
    )
