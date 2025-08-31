from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List

from models.base import get_db
from models import Customer, Connection, Account
from .schemas import AccountResponse

router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.get("/customer/{customer_id}", response_model=List[AccountResponse])
async def list_customer_accounts(customer_id: int, db: Session = Depends(get_db)):
    """List all accounts for a customer across all connections."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    accounts = (
        db.query(Account)
        .join(Connection)
        .filter(Connection.customer_id == customer_id)
        .all()
    )
    return accounts

@router.get("/connection/{connection_id}", response_model=List[AccountResponse])
async def list_connection_accounts(connection_id: int, db: Session = Depends(get_db)):
    """List all accounts for a specific connection."""
    connection = db.query(Connection).filter(Connection.id == connection_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    accounts = db.query(Account).filter(Account.connection_id == connection_id).all()
    return accounts

@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(account_id: int, db: Session = Depends(get_db)):
    """Get account by ID."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@router.get("/by-saltedge-id/{saltedge_account_id}", response_model=AccountResponse)
async def get_account_by_saltedge_id(saltedge_account_id: str, db: Session = Depends(get_db)):
    """Get account by Salt Edge account ID."""
    account = db.query(Account).filter(Account.saltedge_account_id == saltedge_account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@router.get("/customer/{customer_id}/summary")
async def get_customer_accounts_summary(customer_id: int, db: Session = Depends(get_db)):
    """Get summary of all accounts for a customer including total balances by currency."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    accounts = (
        db.query(Account)
        .join(Connection)
        .filter(Connection.customer_id == customer_id)
        .all()
    )
    
    # Calculate balances by currency
    balances_by_currency = {}
    total_accounts = 0
    accounts_by_nature = {}
    
    for account in accounts:
        total_accounts += 1
        
        # Group by currency
        currency = account.currency_code or 'Unknown'
        if currency not in balances_by_currency:
            balances_by_currency[currency] = 0
        if account.balance:
            balances_by_currency[currency] += float(account.balance)
        
        # Group by nature
        nature = account.nature or 'unknown'
        if nature not in accounts_by_nature:
            accounts_by_nature[nature] = 0
        accounts_by_nature[nature] += 1
    
    return {
        "customer_id": customer_id,
        "total_accounts": total_accounts,
        "balances_by_currency": balances_by_currency,
        "accounts_by_nature": accounts_by_nature,
        "accounts": [AccountResponse.model_validate(account) for account in accounts]
    }
