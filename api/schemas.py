from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

# Customer schemas
class CustomerCreate(BaseModel):
    identifier: str
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None

class CustomerResponse(BaseModel):
    id: int
    saltedge_customer_id: str
    identifier: str
    email: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Connection schemas
class ConnectionResponse(BaseModel):
    id: int
    saltedge_connection_id: str
    provider_code: Optional[str]
    provider_name: Optional[str]
    country_code: Optional[str]
    status: Optional[str]
    categorization: Optional[str]
    show_consent_confirmation: bool
    consent_id: Optional[str]
    consent_given_at: Optional[datetime]
    consent_expires_at: Optional[datetime]
    custom_fields: Optional[Dict[str, Any]]
    last_success_at: Optional[datetime]
    next_refresh_possible_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ConnectionCreate(BaseModel):
    country_code: str
    provider_code: str
    consent: Optional[Dict[str, Any]] = None
    credentials: Optional[Dict[str, Any]] = None
    custom_fields: Optional[Dict[str, Any]] = None

# Account schemas
class AccountResponse(BaseModel):
    id: int
    saltedge_account_id: str
    name: str
    nature: Optional[str]
    balance: Optional[Decimal]
    currency_code: Optional[str]
    iban: Optional[str]
    swift: Optional[str]
    sort_code: Optional[str]
    account_number: Optional[str]
    extra: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Transaction schemas
class TransactionResponse(BaseModel):
    id: int
    saltedge_transaction_id: str
    mode: Optional[str]
    status: Optional[str]
    made_on: datetime
    amount: Decimal
    currency_code: str
    description: Optional[str]
    category: Optional[str]
    category_code: Optional[str]
    duplicated: bool
    extra: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Sync schemas
class SyncRequest(BaseModel):
    customer_identifier: str

class SyncResponse(BaseModel):
    customer_id: int
    connections_synced: int
    accounts_synced: int
    transactions_synced: int
    errors: List[str]

# Provider schemas
class ProviderResponse(BaseModel):
    code: str
    name: str
    country_code: str
    mode: List[str]
    status: str
    interactive: bool
    instruction: str
    home_url: str
    login_url: str
    logo_url: str
    country_name: str
    created_at: str
    updated_at: str

class CountryResponse(BaseModel):
    code: str
    name: str
    refresh_start_time: int
    refresh_end_time: int
