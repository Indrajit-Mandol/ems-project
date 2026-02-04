from database import SessionLocal
from models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str):
    password = str(password)
    if len(password) > 72:
        password = password[:72]
    return pwd_context.hash(password)

db = SessionLocal()

# Check if admin already exists
existing = db.query(User).filter(User.username == "admin").first()

if existing:
    print("Admin user already exists!")
else:
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

db.close()
