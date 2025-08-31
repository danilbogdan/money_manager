from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.base import get_db
from models import Customer, Connection, Account, Transaction
from .saltedge_client import SaltEdgeClient

class SyncService:
    """
    Service for synchronizing data between Salt Edge API and local database.
    """
    
    def __init__(self):
        self.client = SaltEdgeClient()
    
    def sync_customer_data(self, customer_identifier: str, db: Session = None) -> Dict[str, Any]:
        """
        Sync all data for a customer including connections, accounts, and transactions.
        """
        if db is None:
            db = next(get_db())
        
        try:
            # Get customer from database
            customer = db.query(Customer).filter(Customer.identifier == customer_identifier).first()
            if not customer:
                raise ValueError(f"Customer with identifier {customer_identifier} not found")
            
            result = {
                "customer_id": customer.id,
                "connections_synced": 0,
                "accounts_synced": 0,
                "transactions_synced": 0,
                "errors": []
            }
            
            # Sync connections
            try:
                connections_data = self.client.list_connections(customer.saltedge_customer_id)
                for connection_data in connections_data.get("data", []):
                    self._sync_connection(connection_data, customer, db)
                    result["connections_synced"] += 1
                    
                    # Sync accounts and transactions for this connection
                    try:
                        accounts_result = self._sync_accounts_for_connection(
                            connection_data["id"], customer, db
                        )
                        result["accounts_synced"] += accounts_result["accounts_synced"]
                        result["transactions_synced"] += accounts_result["transactions_synced"]
                        
                    except Exception as e:
                        result["errors"].append(f"Error syncing accounts for connection {connection_data['id']}: {str(e)}")
                        
            except Exception as e:
                result["errors"].append(f"Error syncing connections: {str(e)}")
            
            db.commit()
            return result
            
        except Exception as e:
            db.rollback()
            raise e
    
    def _sync_connection(self, connection_data: Dict[str, Any], customer: Customer, db: Session):
        """Sync a single connection to the database."""
        connection = db.query(Connection).filter(
            Connection.saltedge_connection_id == connection_data["id"]
        ).first()
        
        if not connection:
            connection = Connection(
                saltedge_connection_id=connection_data["id"],
                customer_id=customer.id,
            )
            db.add(connection)
        
        # Update connection fields
        connection.provider_code = connection_data.get("provider_code")
        connection.provider_name = connection_data.get("provider_name")
        connection.country_code = connection_data.get("country_code")
        connection.status = connection_data.get("status")
        connection.categorization = connection_data.get("categorization")
        connection.show_consent_confirmation = connection_data.get("show_consent_confirmation", False)
        connection.custom_fields = connection_data.get("custom_fields")
        
        # Handle datetime fields
        if connection_data.get("last_success_at"):
            connection.last_success_at = datetime.fromisoformat(
                connection_data["last_success_at"].replace('Z', '+00:00')
            )
        if connection_data.get("next_refresh_possible_at"):
            connection.next_refresh_possible_at = datetime.fromisoformat(
                connection_data["next_refresh_possible_at"].replace('Z', '+00:00')
            )
        
        connection.updated_at = datetime.utcnow()
    
    def _sync_accounts_for_connection(self, saltedge_connection_id: str, customer: Customer, db: Session) -> Dict[str, int]:
        """Sync accounts and transactions for a specific connection."""
        result = {"accounts_synced": 0, "transactions_synced": 0}
        
        # Get local connection
        connection = db.query(Connection).filter(
            Connection.saltedge_connection_id == saltedge_connection_id
        ).first()
        
        if not connection:
            raise ValueError(f"Connection {saltedge_connection_id} not found in database")
        
        # Fetch accounts from Salt Edge
        accounts_data = self.client.list_accounts(saltedge_connection_id)
        
        for account_data in accounts_data.get("data", []):
            self._sync_account(account_data, connection, db)
            result["accounts_synced"] += 1
            
            # Sync transactions for this account
            transactions_result = self._sync_transactions_for_account(
                saltedge_connection_id, account_data["id"], connection, db
            )
            result["transactions_synced"] += transactions_result
        
        return result
    
    def _sync_account(self, account_data: Dict[str, Any], connection: Connection, db: Session):
        """Sync a single account to the database."""
        account = db.query(Account).filter(
            Account.saltedge_account_id == account_data["id"]
        ).first()
        
        if not account:
            account = Account(
                saltedge_account_id=account_data["id"],
                connection_id=connection.id,
            )
            db.add(account)
        
        # Update account fields
        account.name = account_data.get("name")
        account.nature = account_data.get("nature")
        account.balance = account_data.get("balance")
        account.currency_code = account_data.get("currency_code")
        account.iban = account_data.get("iban")
        account.swift = account_data.get("swift")
        account.sort_code = account_data.get("sort_code")
        account.account_number = account_data.get("account_number")
        account.extra = account_data.get("extra")
        account.updated_at = datetime.utcnow()
    
    def _sync_transactions_for_account(self, saltedge_connection_id: str, saltedge_account_id: str, 
                                      connection: Connection, db: Session) -> int:
        """Sync transactions for a specific account."""
        account = db.query(Account).filter(
            and_(
                Account.saltedge_account_id == saltedge_account_id,
                Account.connection_id == connection.id
            )
        ).first()
        
        if not account:
            raise ValueError(f"Account {saltedge_account_id} not found in database")
        
        transactions_synced = 0
        
        # Fetch transactions from Salt Edge
        # Note: You might want to implement pagination here for large numbers of transactions
        transactions_data = self.client.list_transactions(
            connection_id=saltedge_connection_id,
            account_id=saltedge_account_id
        )
        
        for transaction_data in transactions_data.get("data", []):
            self._sync_transaction(transaction_data, account, db)
            transactions_synced += 1
        
        return transactions_synced
    
    def _sync_transaction(self, transaction_data: Dict[str, Any], account: Account, db: Session):
        """Sync a single transaction to the database."""
        transaction = db.query(Transaction).filter(
            Transaction.saltedge_transaction_id == transaction_data["id"]
        ).first()
        
        if not transaction:
            transaction = Transaction(
                saltedge_transaction_id=transaction_data["id"],
                account_id=account.id,
            )
            db.add(transaction)
        
        # Update transaction fields
        transaction.mode = transaction_data.get("mode")
        transaction.status = transaction_data.get("status")
        transaction.amount = transaction_data.get("amount")
        transaction.currency_code = transaction_data.get("currency_code")
        transaction.description = transaction_data.get("description")
        transaction.category = transaction_data.get("category")
        transaction.category_code = transaction_data.get("category_code")
        transaction.duplicated = transaction_data.get("duplicated", False)
        transaction.extra = transaction_data.get("extra")
        
        # Handle datetime field
        if transaction_data.get("made_on"):
            # Handle both date and datetime formats
            made_on_str = transaction_data["made_on"]
            if "T" in made_on_str:
                # Full datetime
                transaction.made_on = datetime.fromisoformat(made_on_str.replace('Z', '+00:00'))
            else:
                # Date only
                transaction.made_on = datetime.strptime(made_on_str, "%Y-%m-%d")
        
        transaction.updated_at = datetime.utcnow()
    
    def create_customer_in_saltedge(self, identifier: str, **kwargs) -> Customer:
        """Create a customer in Salt Edge and save to local database."""
        db = next(get_db())
        
        try:
            # Check if customer already exists
            existing_customer = db.query(Customer).filter(Customer.identifier == identifier).first()
            if existing_customer:
                raise ValueError(f"Customer with identifier {identifier} already exists")
            
            # Create customer in Salt Edge
            response = self.client.create_customer(identifier, **kwargs)
            saltedge_customer = response["data"]
            
            # Save to local database
            customer = Customer(
                saltedge_customer_id=saltedge_customer["id"],
                identifier=saltedge_customer["identifier"],
                secret=saltedge_customer["secret"],
                email=kwargs.get("email"),
                first_name=kwargs.get("first_name"),
                last_name=kwargs.get("last_name"),
                phone=kwargs.get("phone")
            )
            
            db.add(customer)
            db.commit()
            db.refresh(customer)
            
            return customer
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
