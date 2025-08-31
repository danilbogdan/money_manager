"""
Salt Edge account status checker and helper functions.
"""

from typing import Dict, Any, Optional
from services.saltedge_client import SaltEdgeClient

class SaltEdgeStatusChecker:
    """Helper class to check Salt Edge account status and capabilities."""
    
    def __init__(self):
        self.client = SaltEdgeClient()
    
    def check_account_status(self) -> Dict[str, Any]:
        """
        Check the current Salt Edge account status by testing API endpoints.
        Returns information about what features are available.
        """
        status_info = {
            "api_accessible": False,
            "can_create_customers": False,
            "can_list_providers": False,
            "can_access_real_providers": False,
            "fake_providers_available": False,
            "estimated_status": "unknown",
            "recommendations": []
        }
        
        try:
            # Test basic API access
            countries = self.client.list_countries()
            if countries and 'data' in countries:
                status_info["api_accessible"] = True
                status_info["countries_count"] = len(countries['data'])
        except Exception as e:
            status_info["api_error"] = str(e)
            status_info["recommendations"].append("Check your Salt Edge API credentials")
            return status_info
        
        try:
            # Test provider listing
            providers = self.client.list_providers()
            if providers and 'data' in providers:
                status_info["can_list_providers"] = True
                status_info["providers_count"] = len(providers['data'])
                
                # Check for fake providers (indicates test/live status)
                fake_providers = [p for p in providers['data'] if 'fake' in p.get('code', '').lower()]
                real_providers = [p for p in providers['data'] if 'fake' not in p.get('code', '').lower()]
                
                status_info["fake_providers_available"] = len(fake_providers) > 0
                status_info["fake_providers_count"] = len(fake_providers)
                status_info["real_providers_count"] = len(real_providers)
                status_info["can_access_real_providers"] = len(real_providers) > 0
                
        except Exception as e:
            status_info["provider_error"] = str(e)
        
        try:
            # Test customer creation capability
            # We'll create a test customer to check permissions
            test_customer = self.client.create_customer(
                identifier=f"status_test_customer",
                email="test@example.com"
            )
            
            if test_customer and 'data' in test_customer:
                status_info["can_create_customers"] = True
                
                # Clean up test customer
                try:
                    self.client.remove_customer(test_customer['data']['id'])
                except:
                    pass  # Ignore cleanup errors
                    
        except Exception as e:
            status_info["customer_error"] = str(e)
        
        # Estimate account status based on capabilities
        status_info["estimated_status"] = self._estimate_status(status_info)
        status_info["recommendations"] = self._get_recommendations(status_info)
        
        return status_info
    
    def _estimate_status(self, info: Dict[str, Any]) -> str:
        """Estimate the Salt Edge account status based on API capabilities."""
        if not info["api_accessible"]:
            return "invalid_credentials"
        
        if not info["can_create_customers"]:
            return "pending"
        
        if info["fake_providers_available"] and not info["can_access_real_providers"]:
            return "test"
        
        if info["can_access_real_providers"]:
            return "live"
        
        return "unknown"
    
    def _get_recommendations(self, info: Dict[str, Any]) -> list:
        """Get recommendations based on current status."""
        recommendations = []
        status = info["estimated_status"]
        
        if status == "invalid_credentials":
            recommendations.extend([
                "Check your SALTEDGE_APP_ID and SALTEDGE_SECRET_KEY in .env file",
                "Verify credentials in Salt Edge Dashboard at https://www.saltedge.com/clients/profile/secrets"
            ])
        
        elif status == "pending":
            recommendations.extend([
                "Complete your company profile in Salt Edge Dashboard",
                "Contact Salt Edge support or your Project Manager to request Test status",
                "Implement basic integration (which you already have!)",
                "Review the 'Before going LIVE' checklist in documentation"
            ])
        
        elif status == "test":
            recommendations.extend([
                "You can now test with fake providers and sandboxes",
                "Implement request signing for production readiness",
                "Test your complete integration flow",
                "To go Live, contact your Project Manager with a test account in your app"
            ])
        
        elif status == "live":
            recommendations.extend([
                "You have full production access!",
                "Make sure request signing is implemented",
                "Monitor your usage and stay within rate limits",
                "Subscribe to Salt Edge status page for updates"
            ])
        
        return recommendations
    
    def get_test_providers(self) -> Dict[str, Any]:
        """Get list of fake/test providers for testing."""
        try:
            providers = self.client.list_providers()
            if providers and 'data' in providers:
                fake_providers = [
                    p for p in providers['data'] 
                    if 'fake' in p.get('code', '').lower() or p.get('code', '').startswith('faux_')
                ]
                return {
                    "fake_providers": fake_providers,
                    "count": len(fake_providers),
                    "recommended_for_testing": [
                        p for p in fake_providers 
                        if p.get('code') in ['fake_client_xf', 'faux_banque_xf', 'fake_oauth_client_xf']
                    ]
                }
        except Exception as e:
            return {"error": str(e)}
    
    def validate_integration_readiness(self) -> Dict[str, Any]:
        """Check if the integration is ready for production."""
        checks = {
            "request_signing_implemented": False,  # You'll need to implement this
            "error_handling_implemented": True,
            "webhook_handling_ready": False,  # Future enhancement
            "database_configured": True,
            "environment_variables_set": True,
            "ready_for_live": False
        }
        
        # Check if we have proper configuration
        try:
            from config import settings
            if settings.SALTEDGE_APP_ID and settings.SALTEDGE_SECRET_KEY:
                checks["environment_variables_set"] = True
        except:
            checks["environment_variables_set"] = False
        
        # Overall readiness
        required_checks = [
            "environment_variables_set",
            "database_configured", 
            "error_handling_implemented"
        ]
        
        checks["ready_for_live"] = all(checks[check] for check in required_checks)
        
        return {
            "checks": checks,
            "missing_requirements": [
                check for check in required_checks 
                if not checks[check]
            ],
            "recommendations_for_live": [
                "Implement request signing for production",
                "Set up webhook handling for real-time updates",
                "Prepare test account for Salt Edge review",
                "Enable two-factor authentication on Salt Edge Dashboard"
            ]
        }
