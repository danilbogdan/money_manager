from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List

from models.base import get_db
from models import Customer, Connection
from services import SyncService
from .schemas import ConnectionResponse, ConnectionCreate

router = APIRouter(prefix="/connections", tags=["connections"])

@router.get("/customer/{customer_id}", response_model=List[ConnectionResponse])
async def list_customer_connections(customer_id: int, db: Session = Depends(get_db)):
    """List all connections for a customer."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    connections = db.query(Connection).filter(Connection.customer_id == customer_id).all()
    return connections

@router.get("/{connection_id}", response_model=ConnectionResponse)
async def get_connection(connection_id: int, db: Session = Depends(get_db)):
    """Get connection by ID."""
    connection = db.query(Connection).filter(Connection.id == connection_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    return connection

@router.post("/customer/{customer_id}", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_connection(
    customer_id: int, 
    connection_data: ConnectionCreate,
    db: Session = Depends(get_db)
):
    """Create a new connection for a customer."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    try:
        sync_service = SyncService()
        
        # Create connection in Salt Edge
        response = sync_service.client.create_connection(
            customer_id=customer.saltedge_customer_id,
            country_code=connection_data.country_code,
            provider_code=connection_data.provider_code,
            consent=connection_data.consent,
            credentials=connection_data.credentials,
            custom_fields=connection_data.custom_fields
        )
        
        return {
            "connection_id": response["data"]["id"],
            "connect_url": response["data"].get("connect_url"),
            "message": "Connection created successfully. Use connect_url to complete the connection."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create connection: {str(e)}")

@router.put("/{connection_id}/refresh", response_model=dict)
async def refresh_connection(connection_id: int, db: Session = Depends(get_db)):
    """Refresh connection data from the bank."""
    connection = db.query(Connection).filter(Connection.id == connection_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    try:
        sync_service = SyncService()
        
        # Refresh connection in Salt Edge
        response = sync_service.client.refresh_connection(connection.saltedge_connection_id)
        
        return {
            "connection_id": response["data"]["id"],
            "status": response["data"]["status"],
            "message": "Connection refresh initiated successfully."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh connection: {str(e)}")

@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(connection_id: int, db: Session = Depends(get_db)):
    """Delete connection from both Salt Edge and local database."""
    connection = db.query(Connection).filter(Connection.id == connection_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    try:
        sync_service = SyncService()
        
        # Remove from Salt Edge first
        sync_service.client.remove_connection(connection.saltedge_connection_id)
        
        # Remove from local database (cascade will handle accounts and transactions)
        db.delete(connection)
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete connection: {str(e)}")
