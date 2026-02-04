from database import SessionLocal
from models import User
from routes.auth import get_password_hash

db = SessionLocal()

existing = db.query(User).filter(User.username == "admin").first()

if not existing:
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("admin"),
        role="admin",
        is_active=True
    )

    db.add(user)
    db.commit()
    print("Admin user created!")
else:
    print("Admin user already exists!")

db.close()
