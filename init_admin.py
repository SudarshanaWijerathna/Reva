"""
Database initialization script to create the admin user.
Run this script to initialize the admin account for the application.
"""

import sys
sys.path.insert(0, '/path/to/Reva')

from backend.database.database import SessionLocal, engine, Base
from backend.database.schemas import UserModel
from backend.auth.hashing import hashing

# Create tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Admin credentials
ADMIN_EMAIL = "admin@reva.com"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin@12345"

try:
    # Check if admin already exists
    existing_admin = db.query(UserModel).filter(UserModel.email == ADMIN_EMAIL).first()
    
    if existing_admin:
        print(f"✓ Admin user already exists: {ADMIN_EMAIL}")
    else:
        # Create admin user
        hashed_password = hashing(ADMIN_PASSWORD)
        admin_user = UserModel(
            email=ADMIN_EMAIL,
            hashed_password=hashed_password
        )
        db.add(admin_user)
        db.commit()
        print(f"✓ Admin user created successfully!")
        print(f"\n{'='*50}")
        print(f"ADMIN CREDENTIALS")
        print(f"{'='*50}")
        print(f"Email:    {ADMIN_EMAIL}")
        print(f"Username: {ADMIN_USERNAME}")
        print(f"Password: {ADMIN_PASSWORD}")
        print(f"{'='*50}\n")
        
finally:
    db.close()
