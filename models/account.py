from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Account(Base):
    """Account model based on Salt Edge API account structure."""
    
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    saltedge_account_id = Column(String, unique=True, index=True, nullable=False)
    connection_id = Column(Integer, ForeignKey("connections.id"), nullable=False)
    
    # Account identification
    name = Column(String, nullable=False)
    nature = Column(String)  # account, bonus, card, credit, debit_card, ewallet, insurance, investment, loan, mortgage, savings
    balance = Column(Numeric(precision=10, scale=2))
    currency_code = Column(String(3))
    
    # Account details
    iban = Column(String)
    swift = Column(String)
    sort_code = Column(String)
    account_number = Column(String)
    
    # Additional account information
    extra = Column(JSON)  # Store additional fields like account_name, available_amount, etc.
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    connection = relationship("Connection", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Account(id={self.id}, name='{self.name}', balance={self.balance} {self.currency_code})>"
