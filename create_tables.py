from app import app
from models import db
import models  # ensures models load

with app.app_context():
    db.create_all()
    print("✅ MySQL tables created successfully")
