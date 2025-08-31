import os.path
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from decimal import Decimal

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from sqlalchemy.orm import Session
from models.base import get_db
from models import Customer, Connection, Account, Transaction
from config import settings

# If modifying these scopes, delete the token file.
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive.file'
]

class GoogleDocsService:
    """Service for creating financial dashboards in Google Docs."""
    
    def __init__(self):
        self.creds = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google APIs."""
        # The file token.json stores the user's access and refresh tokens.
        if os.path.exists(settings.GOOGLE_TOKEN_FILE):
            self.creds = Credentials.from_authorized_user_file(settings.GOOGLE_TOKEN_FILE, SCOPES)
        
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not settings.GOOGLE_CREDENTIALS_FILE:
                    raise ValueError("GOOGLE_CREDENTIALS_FILE not configured")
                    
                flow = InstalledAppFlow.from_client_secrets_file(
                    settings.GOOGLE_CREDENTIALS_FILE, SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            if settings.GOOGLE_TOKEN_FILE:
                with open(settings.GOOGLE_TOKEN_FILE, 'w') as token:
                    token.write(self.creds.to_json())
    
    def create_financial_dashboard(self, customer_id: int, period_months: int = 6) -> str:
        """
        Create a comprehensive financial dashboard for a customer.
        Returns the URL of the created Google Doc.
        """
        try:
            # Get customer data
            db = next(get_db())
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                raise ValueError(f"Customer {customer_id} not found")
            
            # Generate dashboard content
            dashboard_data = self._generate_dashboard_data(customer_id, period_months, db)
            
            # Create Google Doc
            doc_service = build('docs', 'v1', credentials=self.creds)
            drive_service = build('drive', 'v3', credentials=self.creds)
            
            # Create document
            title = f"Financial Dashboard - {customer.first_name} {customer.last_name} - {datetime.now().strftime('%Y-%m')}"
            document = {
                'title': title
            }
            
            doc = doc_service.documents().create(body=document).execute()
            doc_id = doc.get('documentId')
            
            # Add content to document
            self._populate_document(doc_service, doc_id, dashboard_data, customer)
            
            # Make document shareable (optional)
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            drive_service.permissions().create(fileId=doc_id, body=permission).execute()
            
            doc_url = f"https://docs.google.com/document/d/{doc_id}"
            print(f"Dashboard created: {doc_url}")
            
            return doc_url
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            raise
        finally:
            db.close()
    
    def _generate_dashboard_data(self, customer_id: int, period_months: int, db: Session) -> Dict[str, Any]:
        """Generate data for the financial dashboard."""
        # Get customer accounts
        accounts = (
            db.query(Account)
            .join(Connection)
            .filter(Connection.customer_id == customer_id)
            .all()
        )
        
        # Get recent transactions
        from sqlalchemy import desc
        from datetime import datetime, timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_months * 30)
        
        transactions = (
            db.query(Transaction)
            .join(Account)
            .join(Connection)
            .filter(Connection.customer_id == customer_id)
            .filter(Transaction.made_on >= start_date)
            .order_by(desc(Transaction.made_on))
            .all()
        )
        
        # Calculate summaries
        total_balance = {}
        for account in accounts:
            currency = account.currency_code or 'Unknown'
            if currency not in total_balance:
                total_balance[currency] = 0
            if account.balance:
                total_balance[currency] += float(account.balance)
        
        # Transaction summaries
        income = sum(float(t.amount) for t in transactions if t.amount > 0)
        expenses = sum(float(t.amount) for t in transactions if t.amount < 0)
        
        # Category breakdown
        categories = {}
        for transaction in transactions:
            cat = transaction.category or 'Uncategorized'
            if cat not in categories:
                categories[cat] = {'count': 0, 'amount': 0}
            categories[cat]['count'] += 1
            categories[cat]['amount'] += float(transaction.amount)
        
        # Monthly breakdown
        monthly_data = {}
        for transaction in transactions:
            month = transaction.made_on.strftime('%Y-%m')
            if month not in monthly_data:
                monthly_data[month] = {'income': 0, 'expenses': 0, 'count': 0}
            
            monthly_data[month]['count'] += 1
            if transaction.amount > 0:
                monthly_data[month]['income'] += float(transaction.amount)
            else:
                monthly_data[month]['expenses'] += float(transaction.amount)
        
        return {
            'accounts': accounts,
            'transactions': transactions,
            'total_balance': total_balance,
            'income': income,
            'expenses': expenses,
            'net_income': income + expenses,
            'categories': categories,
            'monthly_data': monthly_data,
            'period': {'start': start_date, 'end': end_date}
        }
    
    def _populate_document(self, doc_service, doc_id: str, data: Dict[str, Any], customer: Customer):
        """Populate the Google Doc with dashboard content."""
        requests = []
        
        # Title and header
        header_text = f"Financial Dashboard for {customer.first_name} {customer.last_name}\n"
        header_text += f"Generated on: {datetime.now().strftime('%B %d, %Y')}\n"
        header_text += f"Period: {data['period']['start'].strftime('%B %Y')} - {data['period']['end'].strftime('%B %Y')}\n\n"
        
        # Account Summary
        header_text += "=== ACCOUNT SUMMARY ===\n"
        for currency, balance in data['total_balance'].items():
            header_text += f"Total Balance ({currency}): {balance:,.2f}\n"
        
        header_text += f"\nTotal Accounts: {len(data['accounts'])}\n\n"
        
        # Account Details
        header_text += "=== ACCOUNT DETAILS ===\n"
        for account in data['accounts']:
            header_text += f"• {account.name} ({account.nature}): {account.balance or 0:,.2f} {account.currency_code}\n"
        
        # Financial Summary
        header_text += "\n=== FINANCIAL SUMMARY ===\n"
        header_text += f"Total Income: {data['income']:,.2f}\n"
        header_text += f"Total Expenses: {data['expenses']:,.2f}\n"
        header_text += f"Net Income: {data['net_income']:,.2f}\n"
        header_text += f"Total Transactions: {len(data['transactions'])}\n\n"
        
        # Category Breakdown
        header_text += "=== SPENDING BY CATEGORY ===\n"
        sorted_categories = sorted(data['categories'].items(), key=lambda x: abs(x[1]['amount']), reverse=True)
        for category, cat_data in sorted_categories[:10]:  # Top 10 categories
            header_text += f"• {category}: {cat_data['amount']:,.2f} ({cat_data['count']} transactions)\n"
        
        # Monthly Breakdown
        header_text += "\n=== MONTHLY BREAKDOWN ===\n"
        sorted_months = sorted(data['monthly_data'].items())
        for month, month_data in sorted_months:
            net = month_data['income'] + month_data['expenses']
            header_text += f"• {month}: Income {month_data['income']:,.2f}, Expenses {month_data['expenses']:,.2f}, Net {net:,.2f}\n"
        
        # Recent Transactions
        header_text += "\n=== RECENT TRANSACTIONS (Last 20) ===\n"
        for transaction in data['transactions'][:20]:
            date_str = transaction.made_on.strftime('%Y-%m-%d')
            header_text += f"• {date_str}: {transaction.amount:,.2f} {transaction.currency_code} - {transaction.description or 'No description'}\n"
        
        # Add all content at once
        requests.append({
            'insertText': {
                'location': {'index': 1},
                'text': header_text
            }
        })
        
        # Execute all requests
        if requests:
            doc_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()
    
    def create_monthly_report(self, customer_id: int, year: int, month: int) -> str:
        """Create a monthly financial report."""
        try:
            db = next(get_db())
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                raise ValueError(f"Customer {customer_id} not found")
            
            # Get transactions for the specific month
            from sqlalchemy import extract
            transactions = (
                db.query(Transaction)
                .join(Account)
                .join(Connection)
                .filter(Connection.customer_id == customer_id)
                .filter(extract('year', Transaction.made_on) == year)
                .filter(extract('month', Transaction.made_on) == month)
                .all()
            )
            
            # Create document
            doc_service = build('docs', 'v1', credentials=self.creds)
            drive_service = build('drive', 'v3', credentials=self.creds)
            
            title = f"Monthly Report - {customer.first_name} {customer.last_name} - {year}-{month:02d}"
            document = {'title': title}
            doc = doc_service.documents().create(body=document).execute()
            doc_id = doc.get('documentId')
            
            # Generate report content
            income = sum(float(t.amount) for t in transactions if t.amount > 0)
            expenses = sum(float(t.amount) for t in transactions if t.amount < 0)
            
            content = f"Monthly Financial Report\n"
            content += f"Customer: {customer.first_name} {customer.last_name}\n"
            content += f"Period: {year}-{month:02d}\n\n"
            content += f"Summary:\n"
            content += f"• Total Income: {income:,.2f}\n"
            content += f"• Total Expenses: {expenses:,.2f}\n"
            content += f"• Net Income: {income + expenses:,.2f}\n"
            content += f"• Total Transactions: {len(transactions)}\n\n"
            content += "All Transactions:\n"
            
            for transaction in sorted(transactions, key=lambda x: x.made_on):
                date_str = transaction.made_on.strftime('%Y-%m-%d')
                content += f"• {date_str}: {transaction.amount:,.2f} - {transaction.description or 'No description'}\n"
            
            # Add content
            doc_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': [{
                    'insertText': {
                        'location': {'index': 1},
                        'text': content
                    }
                }]}
            ).execute()
            
            # Make shareable
            drive_service.permissions().create(
                fileId=doc_id,
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()
            
            return f"https://docs.google.com/document/d/{doc_id}"
            
        except Exception as e:
            raise e
        finally:
            db.close()
