import json
import time
import base64
import hashlib
import hmac
from typing import Dict, List, Optional, Any
import requests
from config import settings

class SaltEdgeClient:
    """
    Salt Edge API client for Account Information Services (AIS).
    Handles authentication and provides methods for all major endpoints.
    """
    
    def __init__(self):
        self.base_url = settings.SALTEDGE_BASE_URL
        self.app_id = settings.SALTEDGE_APP_ID
        self.secret_key = settings.SALTEDGE_SECRET_KEY
        self.client_id = settings.SALTEDGE_CLIENT_ID
        
        if not all([self.app_id, self.secret_key]):
            raise ValueError("SALTEDGE_APP_ID and SALTEDGE_SECRET_KEY must be set")
    
    def _generate_signature(self, method: str, url: str, expires_at: int, body: str = "") -> str:
        """Generate the signature for Salt Edge API authentication."""
        string_to_sign = f"{expires_at}|{method}|{url}|{body}"
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode('utf-8')
    
    def _get_headers(self, method: str, url: str, body: str = "") -> Dict[str, str]:
        """Generate headers with authentication for Salt Edge API requests."""
        expires_at = int(time.time()) + 60  # 60 seconds from now
        signature = self._generate_signature(method, url, expires_at, body)
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'App-id': self.app_id,
            'Secret': self.secret_key,
            'Signature': signature,
            'Expires-at': str(expires_at)
        }
        
        if self.client_id:
            headers['Client-id'] = self.client_id
            
        return headers
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to Salt Edge API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        body = json.dumps(data) if data else ""
        headers = self._get_headers(method, url, body)
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=body if body else None,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Salt Edge API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"Error details: {error_data}")
                except:
                    print(f"Response text: {e.response.text}")
            raise
    
    # Customer endpoints
    def create_customer(self, identifier: str, **kwargs) -> Dict[str, Any]:
        """Create a new customer."""
        data = {
            "data": {
                "identifier": identifier,
                **kwargs
            }
        }
        return self._make_request("POST", "/customers", data)
    
    def list_customers(self, from_id: Optional[str] = None) -> Dict[str, Any]:
        """List customers."""
        endpoint = "/customers"
        if from_id:
            endpoint += f"?from_id={from_id}"
        return self._make_request("GET", endpoint)
    
    def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """Get customer by ID."""
        return self._make_request("GET", f"/customers/{customer_id}")
    
    def remove_customer(self, customer_id: str) -> Dict[str, Any]:
        """Remove customer."""
        return self._make_request("DELETE", f"/customers/{customer_id}")
    
    # Connection endpoints
    def list_connections(self, customer_id: str, from_id: Optional[str] = None) -> Dict[str, Any]:
        """List connections for a customer."""
        endpoint = f"/connections?customer_id={customer_id}"
        if from_id:
            endpoint += f"&from_id={from_id}"
        return self._make_request("GET", endpoint)
    
    def get_connection(self, connection_id: str) -> Dict[str, Any]:
        """Get connection by ID."""
        return self._make_request("GET", f"/connections/{connection_id}")
    
    def create_connection(self, customer_id: str, country_code: str, provider_code: str, 
                         consent: Optional[Dict] = None, credentials: Optional[Dict] = None,
                         **kwargs) -> Dict[str, Any]:
        """Create a new connection."""
        data = {
            "data": {
                "customer_id": customer_id,
                "country_code": country_code,
                "provider_code": provider_code,
            }
        }
        
        if consent:
            data["data"]["consent"] = consent
        if credentials:
            data["data"]["credentials"] = credentials
        if kwargs:
            data["data"].update(kwargs)
            
        return self._make_request("POST", "/connections", data)
    
    def refresh_connection(self, connection_id: str, **kwargs) -> Dict[str, Any]:
        """Refresh connection data."""
        data = {"data": kwargs} if kwargs else None
        return self._make_request("PUT", f"/connections/{connection_id}/refresh", data)
    
    def remove_connection(self, connection_id: str) -> Dict[str, Any]:
        """Remove connection."""
        return self._make_request("DELETE", f"/connections/{connection_id}")
    
    # Account endpoints
    def list_accounts(self, connection_id: str, from_id: Optional[str] = None) -> Dict[str, Any]:
        """List accounts for a connection."""
        endpoint = f"/accounts?connection_id={connection_id}"
        if from_id:
            endpoint += f"&from_id={from_id}"
        return self._make_request("GET", endpoint)
    
    # Transaction endpoints
    def list_transactions(self, connection_id: str, account_id: Optional[str] = None, 
                         from_id: Optional[str] = None, from_date: Optional[str] = None,
                         to_date: Optional[str] = None) -> Dict[str, Any]:
        """List transactions for a connection or specific account."""
        endpoint = f"/transactions?connection_id={connection_id}"
        
        params = []
        if account_id:
            params.append(f"account_id={account_id}")
        if from_id:
            params.append(f"from_id={from_id}")
        if from_date:
            params.append(f"from_date={from_date}")
        if to_date:
            params.append(f"to_date={to_date}")
            
        if params:
            endpoint += "&" + "&".join(params)
            
        return self._make_request("GET", endpoint)
    
    # Provider endpoints
    def list_countries(self) -> Dict[str, Any]:
        """List supported countries."""
        return self._make_request("GET", "/countries")
    
    def list_providers(self, country_code: Optional[str] = None, mode: Optional[str] = None) -> Dict[str, Any]:
        """List providers."""
        endpoint = "/providers"
        params = []
        if country_code:
            params.append(f"country_code={country_code}")
        if mode:
            params.append(f"mode={mode}")
            
        if params:
            endpoint += "?" + "&".join(params)
            
        return self._make_request("GET", endpoint)
    
    def get_provider(self, provider_code: str) -> Dict[str, Any]:
        """Get provider by code."""
        return self._make_request("GET", f"/providers/{provider_code}")
    
    # Category endpoints  
    def list_categories(self) -> Dict[str, Any]:
        """List transaction categories."""
        return self._make_request("GET", "/categories")
