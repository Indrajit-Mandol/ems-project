from database import SessionLocal, create_tables
from models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

# Ensure tables exist
create_tables()

db = SessionLocal()

# Remove old admin if exists
db.query(User).filter(User.username == "admin").delete()
db.commit()

# Create fresh admin
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

print("Fresh Admin user created successfully!")
