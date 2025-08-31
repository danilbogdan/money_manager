from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from models.base import get_db
from models import Customer
from services import SyncService
from .schemas import SyncRequest, SyncResponse, ProviderResponse, CountryResponse

router = APIRouter(prefix="/sync", tags=["sync"])

@router.post("/customer", response_model=SyncResponse)
async def sync_customer_data(sync_request: SyncRequest, db: Session = Depends(get_db)):
    """Sync all data for a customer from Salt Edge API."""
    try:
        sync_service = SyncService()
        result = sync_service.sync_customer_data(sync_request.customer_identifier, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@router.post("/customer/{customer_id}/background")
async def sync_customer_data_background(
    customer_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Sync customer data in the background."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Add background task
    background_tasks.add_task(sync_customer_background, customer.identifier)
    
    return {"message": f"Background sync initiated for customer {customer.identifier}"}

async def sync_customer_background(customer_identifier: str):
    """Background task for syncing customer data."""
    try:
        sync_service = SyncService()
        db = next(get_db())
        result = sync_service.sync_customer_data(customer_identifier, db)
        print(f"Background sync completed for {customer_identifier}: {result}")
    except Exception as e:
        print(f"Background sync failed for {customer_identifier}: {str(e)}")

@router.get("/providers", response_model=List[ProviderResponse])
async def list_providers(country_code: str = None):
    """List available banking providers."""
    try:
        sync_service = SyncService()
        response = sync_service.client.list_providers(country_code=country_code)
        return response.get("data", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch providers: {str(e)}")

@router.get("/providers/{provider_code}", response_model=ProviderResponse)
async def get_provider(provider_code: str):
    """Get provider details by code."""
    try:
        sync_service = SyncService()
        response = sync_service.client.get_provider(provider_code)
        return response.get("data")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch provider: {str(e)}")

@router.get("/countries", response_model=List[CountryResponse])
async def list_countries():
    """List supported countries."""
    try:
        sync_service = SyncService()
        response = sync_service.client.list_countries()
        return response.get("data", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch countries: {str(e)}")

@router.get("/categories")
async def list_saltedge_categories():
    """List transaction categories from Salt Edge."""
    try:
        sync_service = SyncService()
        response = sync_service.client.list_categories()
        return response.get("data", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch categories: {str(e)}")

@router.post("/all-customers/background")
async def sync_all_customers_background(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Sync all customers' data in the background."""
    customers = db.query(Customer).all()
    
    if not customers:
        return {"message": "No customers found"}
    
    # Add background task for each customer
    for customer in customers:
        background_tasks.add_task(sync_customer_background, customer.identifier)
    
    return {
        "message": f"Background sync initiated for {len(customers)} customers",
        "customers": [customer.identifier for customer in customers]
    }
