from database import SessionLocal, engine
from models import User, Base
from passlib.context import CryptContext

# CREATE TABLES FIRST (THIS IS THE KEY FIX)
Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

def get_password_hash(password: str):
    return pwd_context.hash(password)

db = SessionLocal()

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
