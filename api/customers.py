from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List

from models.base import get_db
from models import Customer
from services import SyncService
from .schemas import CustomerCreate, CustomerResponse

router = APIRouter(prefix="/customers", tags=["customers"])

@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(customer_data: CustomerCreate, db: Session = Depends(get_db)):
    """Create a new customer in Salt Edge and local database."""
    try:
        sync_service = SyncService()
        customer = sync_service.create_customer_in_saltedge(
            identifier=customer_data.identifier,
            email=customer_data.email,
            first_name=customer_data.first_name,
            last_name=customer_data.last_name,
            phone=customer_data.phone
        )
        return customer
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create customer: {str(e)}")

@router.get("/", response_model=List[CustomerResponse])
async def list_customers(db: Session = Depends(get_db)):
    """List all customers from local database."""
    customers = db.query(Customer).all()
    return customers

@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """Get customer by ID."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@router.get("/by-identifier/{identifier}", response_model=CustomerResponse)
async def get_customer_by_identifier(identifier: str, db: Session = Depends(get_db)):
    """Get customer by identifier."""
    customer = db.query(Customer).filter(Customer.identifier == identifier).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    """Delete customer from both Salt Edge and local database."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    try:
        # Remove from Salt Edge first
        sync_service = SyncService()
        sync_service.client.remove_customer(customer.saltedge_customer_id)
        
        # Remove from local database
        db.delete(customer)
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete customer: {str(e)}")
