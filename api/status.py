from fastapi import APIRouter, HTTPException
from services import SaltEdgeStatusChecker

router = APIRouter(prefix="/status", tags=["status"])

@router.get("/saltedge-account")
async def check_saltedge_account_status():
    """
    Check the current Salt Edge account status and capabilities.
    This helps determine if you're in Pending, Test, or Live status.
    """
    try:
        checker = SaltEdgeStatusChecker()
        status_info = checker.check_account_status()
        return status_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.get("/test-providers")
async def get_test_providers():
    """
    Get list of fake/test providers available for testing.
    These are available in Test and Live statuses.
    """
    try:
        checker = SaltEdgeStatusChecker()
        test_providers = checker.get_test_providers()
        return test_providers
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch test providers: {str(e)}")

@router.get("/integration-readiness")
async def check_integration_readiness():
    """
    Check if the integration is ready for production (Live status).
    """
    try:
        checker = SaltEdgeStatusChecker()
        readiness = checker.validate_integration_readiness()
        return readiness
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Readiness check failed: {str(e)}")

@router.get("/next-steps")
async def get_next_steps():
    """
    Get personalized next steps based on current Salt Edge account status.
    """
    try:
        checker = SaltEdgeStatusChecker()
        status_info = checker.check_account_status()
        
        return {
            "current_status": status_info["estimated_status"],
            "next_steps": _get_detailed_next_steps(status_info["estimated_status"]),
            "recommendations": status_info["recommendations"],
            "helpful_links": _get_helpful_links(status_info["estimated_status"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get next steps: {str(e)}")

def _get_detailed_next_steps(status: str) -> list:
    """Get detailed next steps based on current status."""
    steps = {
        "pending": [
            "1. Complete your Salt Edge Dashboard profile at https://www.saltedge.com/clients/profile",
            "2. Add team members and configure company information", 
            "3. Contact Salt Edge support or your Project Manager to request Test status",
            "4. While waiting, test the API endpoints with your current credentials",
            "5. Review the integration checklist for Test status requirements"
        ],
        "test": [
            "1. Test your integration using fake providers (check /api/v1/status/test-providers)",
            "2. Create test customers and connections using fake banks",
            "3. Implement request signing for production readiness",
            "4. Test error handling scenarios",
            "5. Prepare a test account in your app for Salt Edge review",
            "6. Contact your Project Manager when ready to go Live"
        ],
        "live": [
            "1. Monitor your production usage and stay within rate limits",
            "2. Implement webhook callbacks for real-time updates",
            "3. Set up monitoring and alerting for your integration",
            "4. Subscribe to Salt Edge status page for service updates",
            "5. Scale your infrastructure as needed"
        ],
        "invalid_credentials": [
            "1. Verify your Salt Edge credentials in the Dashboard",
            "2. Check your .env file has correct SALTEDGE_APP_ID and SALTEDGE_SECRET_KEY",
            "3. Ensure you're using the correct API base URL",
            "4. Contact Salt Edge support if credentials are correct but still not working"
        ]
    }
    
    return steps.get(status, ["Contact Salt Edge support for assistance"])

def _get_helpful_links(status: str) -> dict:
    """Get helpful links based on current status."""
    base_links = {
        "dashboard": "https://www.saltedge.com/clients/profile",
        "documentation": "https://docs.saltedge.com/v6/",
        "support": "https://www.saltedge.com/support",
        "status_page": "https://status.saltedge.com/"
    }
    
    status_specific = {
        "pending": {
            "profile_setup": "https://www.saltedge.com/clients/profile",
            "quick_start": "https://docs.saltedge.com/v6/#quick-start-guide"
        },
        "test": {
            "test_guide": "https://docs.saltedge.com/v6/#quick-start-guide",
            "fake_providers": "https://docs.saltedge.com/v6/#providers-fake",
            "signature_guide": "https://docs.saltedge.com/v6/#signature"
        },
        "live": {
            "production_checklist": "https://docs.saltedge.com/v6/#before-going-live",
            "webhooks": "https://docs.saltedge.com/v6/#callbacks",
            "rate_limits": "https://docs.saltedge.com/v6/#rate-limits"
        }
    }
    
    return {**base_links, **status_specific.get(status, {})}
