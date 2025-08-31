from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc, func
from typing import List, Optional
from datetime import datetime, date

from models.base import get_db
from models import Customer, Connection, Account, Transaction
from .schemas import TransactionResponse

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.get("/customer/{customer_id}", response_model=List[TransactionResponse])
async def list_customer_transactions(
    customer_id: int,
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    category_code: Optional[str] = Query(None)
):
    """List transactions for a customer across all accounts."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    query = (
        db.query(Transaction)
        .join(Account)
        .join(Connection)
        .filter(Connection.customer_id == customer_id)
    )
    
    # Apply filters
    if from_date:
        query = query.filter(Transaction.made_on >= from_date)
    if to_date:
        query = query.filter(Transaction.made_on <= to_date)
    if category_code:
        query = query.filter(Transaction.category_code == category_code)
    
    # Order by date descending and apply pagination
    transactions = (
        query.order_by(desc(Transaction.made_on))
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    return transactions

@router.get("/account/{account_id}", response_model=List[TransactionResponse])
async def list_account_transactions(
    account_id: int,
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None)
):
    """List transactions for a specific account."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    query = db.query(Transaction).filter(Transaction.account_id == account_id)
    
    # Apply date filters
    if from_date:
        query = query.filter(Transaction.made_on >= from_date)
    if to_date:
        query = query.filter(Transaction.made_on <= to_date)
    
    # Order by date descending and apply pagination
    transactions = (
        query.order_by(desc(Transaction.made_on))
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    return transactions

@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Get transaction by ID."""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@router.get("/customer/{customer_id}/summary")
async def get_customer_transactions_summary(
    customer_id: int,
    db: Session = Depends(get_db),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None)
):
    """Get transaction summary for a customer including spending by category."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    query = (
        db.query(Transaction)
        .join(Account)
        .join(Connection)
        .filter(Connection.customer_id == customer_id)
    )
    
    # Apply date filters
    if from_date:
        query = query.filter(Transaction.made_on >= from_date)
    if to_date:
        query = query.filter(Transaction.made_on <= to_date)
    
    transactions = query.all()
    
    # Calculate summaries
    total_transactions = len(transactions)
    total_income = sum(float(t.amount) for t in transactions if t.amount > 0)
    total_expenses = sum(float(t.amount) for t in transactions if t.amount < 0)
    
    # Group by category
    categories_summary = {}
    currencies = set()
    
    for transaction in transactions:
        currencies.add(transaction.currency_code)
        
        category = transaction.category or 'Uncategorized'
        if category not in categories_summary:
            categories_summary[category] = {
                'count': 0,
                'total_amount': 0,
                'income': 0,
                'expenses': 0
            }
        
        categories_summary[category]['count'] += 1
        categories_summary[category]['total_amount'] += float(transaction.amount)
        
        if transaction.amount > 0:
            categories_summary[category]['income'] += float(transaction.amount)
        else:
            categories_summary[category]['expenses'] += float(transaction.amount)
    
    # Group by month (if date range is large)
    monthly_summary = {}
    for transaction in transactions:
        month_key = transaction.made_on.strftime('%Y-%m')
        if month_key not in monthly_summary:
            monthly_summary[month_key] = {
                'income': 0,
                'expenses': 0,
                'net': 0,
                'transactions_count': 0
            }
        
        monthly_summary[month_key]['transactions_count'] += 1
        if transaction.amount > 0:
            monthly_summary[month_key]['income'] += float(transaction.amount)
        else:
            monthly_summary[month_key]['expenses'] += float(transaction.amount)
        monthly_summary[month_key]['net'] = (
            monthly_summary[month_key]['income'] + monthly_summary[month_key]['expenses']
        )
    
    return {
        "customer_id": customer_id,
        "period": {
            "from_date": from_date.isoformat() if from_date else None,
            "to_date": to_date.isoformat() if to_date else None
        },
        "summary": {
            "total_transactions": total_transactions,
            "total_income": round(total_income, 2),
            "total_expenses": round(total_expenses, 2),
            "net_amount": round(total_income + total_expenses, 2),
            "currencies": list(currencies)
        },
        "categories": categories_summary,
        "monthly_breakdown": monthly_summary
    }

@router.get("/categories/list")
async def list_transaction_categories(db: Session = Depends(get_db)):
    """Get all unique transaction categories from the database."""
    categories = (
        db.query(Transaction.category, Transaction.category_code)
        .distinct()
        .filter(Transaction.category.isnot(None))
        .all()
    )
    
    return [
        {"category": cat[0], "category_code": cat[1]}
        for cat in categories
    ]
