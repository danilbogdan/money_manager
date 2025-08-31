from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Transaction(Base):
    """Transaction model based on Salt Edge API transaction structure."""
    
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    saltedge_transaction_id = Column(String, unique=True, index=True, nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    
    # Transaction core data
    mode = Column(String)  # normal, fee, transfer
    status = Column(String)  # posted, pending
    made_on = Column(DateTime, nullable=False)
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    currency_code = Column(String(3), nullable=False)
    description = Column(String)
    
    # Transaction categorization
    category = Column(String)
    category_code = Column(String)
    duplicated = Column(Boolean, default=False)
    
    # Additional transaction data
    extra = Column(JSON)  # Store additional fields like payee_information, tags, etc.
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, amount={self.amount} {self.currency_code}, description='{self.description[:30]}...')>"
