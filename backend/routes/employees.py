from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from math import ceil
from database import get_db
from models import Employee, User
from schemas import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    PaginatedEmployeeResponse
)
from .auth import get_current_user  # <-- fixed import


router = APIRouter(prefix="/employees", tags=["Employees"])

@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    employee_data: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new employee"""
    # Check if email already exists
    if db.query(Employee).filter(Employee.email == employee_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee with this email already exists"
        )
    
    # Create new employee
    db_employee = Employee(**employee_data.model_dump())
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    
    return db_employee

@router.get("", response_model=PaginatedEmployeeResponse)
def get_employees(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all employees with pagination and search"""
    # Base query
    query = db.query(Employee)
    
    # Apply search filter
    if search:
        search_filter = or_(
            Employee.name.ilike(f"%{search}%"),
            Employee.email.ilike(f"%{search}%"),
            Employee.designation.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # Apply active status filter
    if is_active is not None:
        query = query.filter(Employee.is_active == is_active)
    
    # Get total count
    total = query.count()
    
    # Calculate pagination
    total_pages = ceil(total / page_size)
    skip = (page - 1) * page_size
    
    # Get paginated results
    employees = query.offset(skip).limit(page_size).all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "employees": employees
    }

@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific employee by ID"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    return employee

@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an employee"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Check if new email already exists (if email is being updated)
    if employee_data.email and employee_data.email != employee.email:
        existing = db.query(Employee).filter(Employee.email == employee_data.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee with this email already exists"
            )
    
    # Update employee fields
    update_data = employee_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(employee, field, value)
    
    db.commit()
    db.refresh(employee)
    
    return employee

@router.delete("/{employee_id}", status_code=status.HTTP_200_OK)
def delete_employee(
    employee_id: int,
    hard_delete: bool = Query(False, description="Permanently delete employee"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an employee (soft delete by default)"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    if hard_delete:
        # Hard delete - permanently remove from database
        db.delete(employee)
        db.commit()
        return {"message": "Employee permanently deleted"}
    else:
        # Soft delete - mark as inactive
        employee.is_active = False
        db.commit()
        return {"message": "Employee deactivated successfully"}