from database import SessionLocal
from models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

db = SessionLocal()

user = User(
    username="admin",
    email="admin@example.com",
    hashed_password=get_password_hash("admin"),
    role="admin",
    is_active=True
)

db.add(user)
db.commit()
db.close()

print("Admin user created!")
