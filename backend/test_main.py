
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from database import get_db, Base
from models import User, Employee
from auth import get_password_hash

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

class TestAuthentication:
    def test_register_user(self, test_db):
        """Test user registration"""
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpass123"
            }
        )
        assert response.status_code == 201
        assert response.json()["username"] == "testuser"
        assert response.json()["email"] == "test@example.com"
    
    def test_register_duplicate_user(self, test_db):
        """Test registering duplicate user"""
        # First registration
        client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpass123"
            }
        )
        # Duplicate registration
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test2@example.com",
                "password": "testpass123"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_login_success(self, test_db):
        """Test successful login"""
        # Register user
        client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpass123"
            }
        )
        # Login
        response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "testpass123"
            }
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
    
    def test_login_wrong_password(self, test_db):
        """Test login with wrong password"""
        # Register user
        client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpass123"
            }
        )
        # Login with wrong password
        response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401

class TestEmployees:
    @pytest.fixture
    def auth_token(self, test_db):
        """Create user and return auth token"""
        client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpass123"
            }
        )
        response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "testpass123"
            }
        )
        return response.json()["access_token"]
    
    def test_create_employee(self, test_db, auth_token):
        """Test creating an employee"""
        response = client.post(
            "/employees",
            json={
                "name": "John Doe",
                "email": "john@example.com",
                "designation": "Software Engineer",
                "salary": 75000.00
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 201
        assert response.json()["name"] == "John Doe"
        assert response.json()["email"] == "john@example.com"
    
    def test_get_employees(self, test_db, auth_token):
        """Test getting employees list"""
        # Create employee
        client.post(
            "/employees",
            json={
                "name": "John Doe",
                "email": "john@example.com",
                "designation": "Software Engineer",
                "salary": 75000.00
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Get employees
        response = client.get(
            "/employees",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert response.json()["total"] >= 1
        assert len(response.json()["employees"]) >= 1
    
    def test_get_employee_by_id(self, test_db, auth_token):
        """Test getting employee by ID"""
        # Create employee
        create_response = client.post(
            "/employees",
            json={
                "name": "John Doe",
                "email": "john@example.com",
                "designation": "Software Engineer",
                "salary": 75000.00
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        employee_id = create_response.json()["id"]
        
        # Get employee
        response = client.get(
            f"/employees/{employee_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert response.json()["id"] == employee_id
    
    def test_update_employee(self, test_db, auth_token):
        """Test updating an employee"""
        # Create employee
        create_response = client.post(
            "/employees",
            json={
                "name": "John Doe",
                "email": "john@example.com",
                "designation": "Software Engineer",
                "salary": 75000.00
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        employee_id = create_response.json()["id"]
        
        # Update employee
        response = client.put(
            f"/employees/{employee_id}",
            json={
                "name": "John Updated",
                "salary": 85000.00
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "John Updated"
        assert response.json()["salary"] == 85000.00
    
    def test_delete_employee_soft(self, test_db, auth_token):
        """Test soft deleting an employee"""
        # Create employee
        create_response = client.post(
            "/employees",
            json={
                "name": "John Doe",
                "email": "john@example.com",
                "designation": "Software Engineer",
                "salary": 75000.00
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        employee_id = create_response.json()["id"]
        
        # Delete employee (soft)
        response = client.delete(
            f"/employees/{employee_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert "deactivated" in response.json()["message"]
    
    def test_unauthorized_access(self, test_db):
        """Test accessing protected route without token"""
        response = client.get("/employees")
        assert response.status_code == 403