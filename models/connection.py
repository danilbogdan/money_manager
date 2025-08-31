from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Connection(Base):
    """Connection model based on Salt Edge API connection structure."""
    
    __tablename__ = "connections"
    
    id = Column(Integer, primary_key=True, index=True)
    saltedge_connection_id = Column(String, unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    
    # Connection details from Salt Edge
    provider_code = Column(String, nullable=False)
    provider_name = Column(String)
    country_code = Column(String)
    
    # Connection status and metadata
    status = Column(String)  # active, inactive, disabled, etc.
    categorization = Column(String)  # none, personal, business
    show_consent_confirmation = Column(Boolean, default=False)
    
    # Consent information
    consent_id = Column(String)
    consent_given_at = Column(DateTime)
    consent_expires_at = Column(DateTime)
    
    # Additional connection data
    custom_fields = Column(JSON)
    last_success_at = Column(DateTime)
    next_refresh_possible_at = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    customer = relationship("Customer", back_populates="connections")
    accounts = relationship("Account", back_populates="connection", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Connection(id={self.id}, provider='{self.provider_name}', status='{self.status}')>"
