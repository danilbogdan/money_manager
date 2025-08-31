#!/usr/bin/env python3
"""
Example usage script for Money Manager API.
Demonstrates how to use the application programmatically.
"""

import asyncio
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

class MoneyManagerClient:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def _url(self, endpoint):
        return f"{self.base_url}/api/v1{endpoint}"
    
    def create_customer(self, identifier, email=None, first_name=None, last_name=None):
        """Create a new customer."""
        data = {"identifier": identifier}
        if email:
            data["email"] = email
        if first_name:
            data["first_name"] = first_name
        if last_name:
            data["last_name"] = last_name
        
        response = self.session.post(self._url("/customers/"), json=data)
        response.raise_for_status()
        return response.json()
    
    def list_customers(self):
        """List all customers."""
        response = self.session.get(self._url("/customers/"))
        response.raise_for_status()
        return response.json()
    
    def list_providers(self, country_code=None):
        """List banking providers."""
        url = self._url("/sync/providers")
        if country_code:
            url += f"?country_code={country_code}"
        
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def create_connection(self, customer_id, country_code, provider_code):
        """Create bank connection for customer."""
        data = {
            "country_code": country_code,
            "provider_code": provider_code,
            "consent": {
                "scopes": ["account_details", "transactions_details"],
                "period_days": 90
            }
        }
        
        response = self.session.post(
            self._url(f"/connections/customer/{customer_id}"),
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def sync_customer(self, customer_identifier):
        """Sync customer data from banks."""
        data = {"customer_identifier": customer_identifier}
        response = self.session.post(self._url("/sync/customer"), json=data)
        response.raise_for_status()
        return response.json()
    
    def get_customer_accounts(self, customer_id):
        """Get all accounts for a customer."""
        response = self.session.get(self._url(f"/accounts/customer/{customer_id}"))
        response.raise_for_status()
        return response.json()
    
    def get_customer_transactions(self, customer_id, limit=50):
        """Get transactions for a customer."""
        response = self.session.get(
            self._url(f"/transactions/customer/{customer_id}"),
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()
    
    def get_transaction_summary(self, customer_id):
        """Get spending summary for a customer."""
        response = self.session.get(self._url(f"/transactions/customer/{customer_id}/summary"))
        response.raise_for_status()
        return response.json()
    
    def create_dashboard(self, customer_id, period_months=6):
        """Create Google Docs dashboard."""
        data = {"period_months": period_months}
        response = self.session.post(
            self._url(f"/dashboards/customer/{customer_id}"),
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def check_saltedge_status(self):
        """Check Salt Edge account status."""
        response = self.session.get(self._url("/status/saltedge-account"))
        response.raise_for_status()
        return response.json()
    
    def get_next_steps(self):
        """Get next steps based on current status."""
        response = self.session.get(self._url("/status/next-steps"))
        response.raise_for_status()
        return response.json()
    
    def test_callback(self):
        """Test callback accessibility."""
        response = self.session.get(self._url("/callbacks/test"))
        response.raise_for_status()
        return response.json()
    
    def get_callback_setup_instructions(self):
        """Get callback setup instructions."""
        response = self.session.get(self._url("/callbacks/setup-instructions"))
        response.raise_for_status()
        return response.json()

def demonstrate_workflow():
    """Demonstrate the complete Money Manager workflow."""
    client = MoneyManagerClient()
    
    print("🚀 Money Manager API Demo")
    print("=" * 40)
    
    try:
        # Check if API is running
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        print("✅ API is running")
    except:
        print("❌ API is not running. Please start it with: python main.py")
        return
    
    # Check Salt Edge account status
    print("\n🔍 Checking Salt Edge account status...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/status/saltedge-account")
        if response.status_code == 200:
            status_info = response.json()
            print(f"   📊 Status: {status_info.get('estimated_status', 'unknown')}")
            print(f"   🌍 Countries available: {status_info.get('countries_count', 0)}")
            print(f"   🏦 Providers available: {status_info.get('providers_count', 0)}")
            
            if status_info.get('recommendations'):
                print("   💡 Recommendations:")
                for rec in status_info['recommendations'][:3]:
                    print(f"      • {rec}")
        else:
            print(f"   ⚠️ Could not check status: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ Status check error: {e}")
    
    # Check callback setup
    print("\n📞 Checking callback setup...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/callbacks/test")
        if response.status_code == 200:
            print("   ✅ Callback endpoint is accessible")
        else:
            print(f"   ⚠️ Callback endpoint issue: {response.status_code}")
    except:
        print("   ⚠️ Callback endpoint not accessible")
        print("   💡 For development, run: python setup_ngrok.py")
    
    # 1. Create a customer
    print("\n1️⃣ Creating a customer...")
    customer_data = {
        "identifier": f"demo_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "email": "demo@example.com",
        "first_name": "Demo",
        "last_name": "User"
    }
    
    try:
        customer = client.create_customer(**customer_data)
        customer_id = customer["id"]
        print(f"   ✅ Customer created: {customer['first_name']} {customer['last_name']} (ID: {customer_id})")
    except Exception as e:
        print(f"   ❌ Failed to create customer: {e}")
        return
    
    # 2. List available providers
    print("\n2️⃣ Listing available banks...")
    try:
        providers = client.list_providers("GB")  # UK banks
        print(f"   ✅ Found {len(providers)} banks in UK")
        
        # Show first few providers
        for provider in providers[:3]:
            print(f"      • {provider['name']} ({provider['code']})")
        if len(providers) > 3:
            print(f"      ... and {len(providers) - 3} more")
    except Exception as e:
        print(f"   ❌ Failed to list providers: {e}")
    
    # 3. Create a connection (will need user interaction)
    print("\n3️⃣ Creating bank connection...")
    print("   ⚠️ Bank connections require user authentication on the bank's website")
    print("   This demo will create a connection request")
    
    try:
        connection_result = client.create_connection(
            customer_id=customer_id,
            country_code="GB",
            provider_code="lloyds_gb"  # Example UK bank
        )
        print(f"   ✅ Connection created: {connection_result['connection_id']}")
        if connection_result.get('connect_url'):
            print(f"   🔗 Complete connection at: {connection_result['connect_url']}")
    except Exception as e:
        print(f"   ⚠️ Connection creation info: {e}")
        print("   (This is expected without actual Salt Edge credentials)")
    
    # 4. Sync data (will work after connection is established)
    print("\n4️⃣ Syncing bank data...")
    try:
        sync_result = client.sync_customer(customer_data["identifier"])
        print(f"   ✅ Sync completed:")
        print(f"      • Connections: {sync_result.get('connections_synced', 0)}")
        print(f"      • Accounts: {sync_result.get('accounts_synced', 0)}")
        print(f"      • Transactions: {sync_result.get('transactions_synced', 0)}")
    except Exception as e:
        print(f"   ⚠️ Sync info: {e}")
        print("   (Sync requires established bank connections)")
    
    # 5. View customer data
    print("\n5️⃣ Viewing customer data...")
    try:
        accounts = client.get_customer_accounts(customer_id)
        print(f"   📊 Accounts: {len(accounts)}")
        
        transactions = client.get_customer_transactions(customer_id)
        print(f"   💳 Recent transactions: {len(transactions)}")
        
        summary = client.get_transaction_summary(customer_id)
        print(f"   📈 Financial summary available")
        
    except Exception as e:
        print(f"   ⚠️ Data viewing: {e}")
    
    # 6. Create dashboard
    print("\n6️⃣ Creating Google Docs dashboard...")
    try:
        dashboard = client.create_dashboard(customer_id)
        print(f"   ✅ Dashboard created: {dashboard.get('dashboard_url', 'URL not available')}")
    except Exception as e:
        print(f"   ⚠️ Dashboard creation: {e}")
        print("   (Requires Google Docs configuration)")
    
    print("\n🎉 Demo completed!")
    
    # Get personalized next steps
    print("\n📋 Getting personalized next steps...")
    try:
        next_steps = client.get_next_steps()
        print(f"   Current Status: {next_steps.get('current_status', 'unknown')}")
        print("   Next Steps:")
        for i, step in enumerate(next_steps.get('next_steps', [])[:3], 1):
            print(f"      {step}")
        
        if next_steps.get('helpful_links'):
            print("   Helpful Links:")
            links = next_steps.get('helpful_links', {})
            for name, url in list(links.items())[:3]:
                print(f"      • {name}: {url}")
                
    except Exception as e:
        print(f"   ⚠️ Could not get next steps: {e}")
        print("   Default next steps:")
        print("   1. Configure Salt Edge credentials in .env file")  
        print("   2. Set up callbacks with ngrok: python setup_ngrok.py")
        print("   3. Create real bank connections")
        print("   4. Start managing your finances!")
    
    print(f"\n💡 Pro tip: Check your status anytime at {BASE_URL}/api/v1/status/next-steps")

if __name__ == "__main__":
    demonstrate_workflow()
