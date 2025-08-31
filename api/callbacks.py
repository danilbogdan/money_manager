from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
import json
import hashlib
import hmac
import base64
from datetime import datetime

from models.base import get_db
from models import Customer, Connection, Account, Transaction
from services import SyncService
from config import settings

router = APIRouter(prefix="/callbacks", tags=["callbacks"])

def verify_salt_edge_signature(request_body: bytes, signature: str, expires_at: str) -> bool:
    """
    Verify Salt Edge callback signature for security.
    This ensures the callback is actually from Salt Edge.
    """
    if not settings.SALTEDGE_SECRET_KEY:
        # In development, you might skip signature verification
        return True
    
    try:
        # Reconstruct the signature
        string_to_sign = f"{expires_at}|POST|/api/v1/callbacks/salt-edge|{request_body.decode('utf-8')}"
        expected_signature = hmac.new(
            settings.SALTEDGE_SECRET_KEY.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).digest()
        expected_signature = base64.b64encode(expected_signature).decode('utf-8')
        
        return hmac.compare_digest(expected_signature, signature)
    except Exception as e:
        print(f"Signature verification error: {e}")
        return False

@router.post("/ais/success")
async def ais_success_callback(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    AIS Success callback endpoint.
    
    Configure this URL in your Salt Edge Dashboard (AIS Success URL):
    https://your-domain.com/api/v1/callbacks/ais/success
    
    Called when:
    - Connection is successfully established
    - New data is fetched from bank
    - Account balances are updated
    """
    try:
        # Get request body
        body = await request.body()
        
        # Get headers for signature verification
        signature = request.headers.get('Signature', '')
        expires_at = request.headers.get('Expires-at', '')
        
        # Verify signature (optional but recommended)
        if signature and not verify_salt_edge_signature(body, signature, expires_at):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse callback data
        try:
            callback_data = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        # Log the callback for debugging
        print(f"Received Salt Edge callback: {callback_data}")
        
        # Process success callback in background
        background_tasks.add_task(process_success_callback, callback_data, db)
        
        # Return success response (Salt Edge expects 200)
        return {"status": "success_received", "timestamp": datetime.utcnow().isoformat()}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"AIS Success callback processing error: {e}")
        raise HTTPException(status_code=500, detail="Success callback processing failed")

@router.post("/ais/failure")
async def ais_failure_callback(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    AIS Failure callback endpoint.
    
    Configure this URL in your Salt Edge Dashboard (AIS Failure URL):
    https://your-domain.com/api/v1/callbacks/ais/failure
    
    Called when:
    - Connection fails to establish
    - Authentication errors occur
    - Bank temporarily unavailable
    """
    try:
        body = await request.body()
        signature = request.headers.get('Signature', '')
        expires_at = request.headers.get('Expires-at', '')
        
        if signature and not verify_salt_edge_signature(body, signature, expires_at):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        callback_data = json.loads(body.decode('utf-8'))
        print(f"Received AIS Failure callback: {callback_data}")
        
        background_tasks.add_task(process_failure_callback, callback_data, db)
        
        return {"status": "failure_received", "timestamp": datetime.utcnow().isoformat()}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"AIS Failure callback processing error: {e}")
        raise HTTPException(status_code=500, detail="Failure callback processing failed")

@router.post("/ais/notify")
async def ais_notify_callback(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    AIS Notify callback endpoint.
    
    Configure this URL in your Salt Edge Dashboard (AIS Notify URL):
    https://your-domain.com/api/v1/callbacks/ais/notify
    
    Called when:
    - Provider changes occur
    - Additional user action required
    - Connection status updates
    """
    try:
        body = await request.body()
        signature = request.headers.get('Signature', '')
        expires_at = request.headers.get('Expires-at', '')
        
        if signature and not verify_salt_edge_signature(body, signature, expires_at):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        callback_data = json.loads(body.decode('utf-8'))
        print(f"Received AIS Notify callback: {callback_data}")
        
        background_tasks.add_task(process_notify_callback, callback_data, db)
        
        return {"status": "notify_received", "timestamp": datetime.utcnow().isoformat()}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"AIS Notify callback processing error: {e}")
        raise HTTPException(status_code=500, detail="Notify callback processing failed")

@router.post("/ais/destroy")
async def ais_destroy_callback(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    AIS Destroy callback endpoint.
    
    Configure this URL in your Salt Edge Dashboard (AIS Destroy URL):
    https://your-domain.com/api/v1/callbacks/ais/destroy
    
    Called when:
    - Connection is permanently removed
    - User revokes consent
    - Connection cleanup needed
    """
    try:
        body = await request.body()
        signature = request.headers.get('Signature', '')
        expires_at = request.headers.get('Expires-at', '')
        
        if signature and not verify_salt_edge_signature(body, signature, expires_at):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        callback_data = json.loads(body.decode('utf-8'))
        print(f"Received AIS Destroy callback: {callback_data}")
        
        background_tasks.add_task(process_destroy_callback, callback_data, db)
        
        return {"status": "destroy_received", "timestamp": datetime.utcnow().isoformat()}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"AIS Destroy callback processing error: {e}")
        raise HTTPException(status_code=500, detail="Destroy callback processing failed")

@router.post("/ais/provider-changes")
async def ais_provider_changes_callback(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    AIS Provider Changes callback endpoint.
    
    Configure this URL in your Salt Edge Dashboard (AIS Provider Changes URL):
    https://your-domain.com/api/v1/callbacks/ais/provider-changes
    
    Called when:
    - Provider updates their API
    - New fields become available
    - Provider requirements change
    """
    try:
        body = await request.body()
        signature = request.headers.get('Signature', '')
        expires_at = request.headers.get('Expires-at', '')
        
        if signature and not verify_salt_edge_signature(body, signature, expires_at):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        callback_data = json.loads(body.decode('utf-8'))
        print(f"Received AIS Provider Changes callback: {callback_data}")
        
        background_tasks.add_task(process_provider_changes_callback, callback_data, db)
        
        return {"status": "provider_changes_received", "timestamp": datetime.utcnow().isoformat()}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"AIS Provider Changes callback processing error: {e}")
        raise HTTPException(status_code=500, detail="Provider changes callback processing failed")

# PIS (Payment Initiation Services) Callbacks

@router.post("/pis/success")
async def pis_success_callback(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    PIS Success callback endpoint.
    
    Configure this URL in your Salt Edge Dashboard (PIS Success URL):
    https://your-domain.com/api/v1/callbacks/pis/success
    
    Called when:
    - Payment is successfully initiated
    - Payment status changes to completed
    """
    try:
        body = await request.body()
        signature = request.headers.get('Signature', '')
        expires_at = request.headers.get('Expires-at', '')
        
        if signature and not verify_salt_edge_signature(body, signature, expires_at):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        callback_data = json.loads(body.decode('utf-8'))
        print(f"Received PIS Success callback: {callback_data}")
        
        # For future payment functionality
        background_tasks.add_task(process_payment_success_callback, callback_data, db)
        
        return {"status": "payment_success_received", "timestamp": datetime.utcnow().isoformat()}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"PIS Success callback processing error: {e}")
        raise HTTPException(status_code=500, detail="Payment success callback processing failed")

@router.post("/pis/failure")
async def pis_failure_callback(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    PIS Failure callback endpoint.
    
    Configure this URL in your Salt Edge Dashboard (PIS Failure URL):
    https://your-domain.com/api/v1/callbacks/pis/failure
    
    Called when:
    - Payment fails to process
    - Insufficient funds
    - Payment rejected by bank
    """
    try:
        body = await request.body()
        signature = request.headers.get('Signature', '')
        expires_at = request.headers.get('Expires-at', '')
        
        if signature and not verify_salt_edge_signature(body, signature, expires_at):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        callback_data = json.loads(body.decode('utf-8'))
        print(f"Received PIS Failure callback: {callback_data}")
        
        background_tasks.add_task(process_payment_failure_callback, callback_data, db)
        
        return {"status": "payment_failure_received", "timestamp": datetime.utcnow().isoformat()}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"PIS Failure callback processing error: {e}")
        raise HTTPException(status_code=500, detail="Payment failure callback processing failed")

@router.post("/pis/notify")
async def pis_notify_callback(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    PIS Notify callback endpoint.
    
    Configure this URL in your Salt Edge Dashboard (PIS Notify URL):
    https://your-domain.com/api/v1/callbacks/pis/notify
    
    Called when:
    - Payment status updates
    - Additional authorization required
    """
    try:
        body = await request.body()
        signature = request.headers.get('Signature', '')
        expires_at = request.headers.get('Expires-at', '')
        
        if signature and not verify_salt_edge_signature(body, signature, expires_at):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        callback_data = json.loads(body.decode('utf-8'))
        print(f"Received PIS Notify callback: {callback_data}")
        
        background_tasks.add_task(process_payment_notify_callback, callback_data, db)
        
        return {"status": "payment_notify_received", "timestamp": datetime.utcnow().isoformat()}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"PIS Notify callback processing error: {e}")
        raise HTTPException(status_code=500, detail="Payment notify callback processing failed")

# Legacy single endpoint (for backward compatibility)
@router.post("/salt-edge")
async def salt_edge_legacy_callback(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Legacy single callback endpoint for Salt Edge webhooks.
    
    For backward compatibility only. Use specific endpoints above for better handling.
    """
    try:
        body = await request.body()
        signature = request.headers.get('Signature', '')
        expires_at = request.headers.get('Expires-at', '')
        
        if signature and not verify_salt_edge_signature(body, signature, expires_at):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        callback_data = json.loads(body.decode('utf-8'))
        print(f"Received legacy Salt Edge callback: {callback_data}")
        
        # Route to appropriate handler based on callback content
        background_tasks.add_task(process_legacy_callback, callback_data, db)
        
        return {"status": "legacy_callback_received", "timestamp": datetime.utcnow().isoformat()}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Legacy callback processing error: {e}")
        raise HTTPException(status_code=500, detail="Legacy callback processing failed")

# Specific callback processors

async def process_success_callback(callback_data: Dict[str, Any], db: Session):
    """Process AIS success callback in the background."""
    try:
        data = callback_data.get('data', {})
        connection_id = data.get('connection_id')
        customer_id = data.get('customer_id')
        
        print(f"Processing SUCCESS callback - Connection: {connection_id}, Customer: {customer_id}")
        
        if connection_id and customer_id:
            await handle_success_callback(data, db)
        else:
            print("Missing connection_id or customer_id in success callback")
            
    except Exception as e:
        print(f"Success callback processing error: {e}")

async def process_failure_callback(callback_data: Dict[str, Any], db: Session):
    """Process AIS failure callback in the background."""
    try:
        data = callback_data.get('data', {})
        connection_id = data.get('connection_id')
        error_class = data.get('error_class', 'unknown')
        error_message = data.get('error_message', 'Unknown error')
        
        print(f"Processing FAILURE callback - Connection: {connection_id}, Error: {error_class}")
        await handle_error_callback(data, db)
            
    except Exception as e:
        print(f"Failure callback processing error: {e}")

async def process_notify_callback(callback_data: Dict[str, Any], db: Session):
    """Process AIS notify callback in the background."""
    try:
        data = callback_data.get('data', {})
        connection_id = data.get('connection_id')
        notify_type = data.get('type', 'unknown')
        
        print(f"Processing NOTIFY callback - Connection: {connection_id}, Type: {notify_type}")
        await handle_notify_callback(data, db)
            
    except Exception as e:
        print(f"Notify callback processing error: {e}")

async def process_destroy_callback(callback_data: Dict[str, Any], db: Session):
    """Process AIS destroy callback in the background."""
    try:
        data = callback_data.get('data', {})
        connection_id = data.get('connection_id')
        customer_id = data.get('customer_id')
        
        print(f"Processing DESTROY callback - Connection: {connection_id}, Customer: {customer_id}")
        await handle_destroy_callback(data, db)
            
    except Exception as e:
        print(f"Destroy callback processing error: {e}")

async def process_provider_changes_callback(callback_data: Dict[str, Any], db: Session):
    """Process AIS provider changes callback in the background."""
    try:
        data = callback_data.get('data', {})
        provider_code = data.get('provider_code', 'unknown')
        
        print(f"Processing PROVIDER CHANGES callback - Provider: {provider_code}")
        await handle_provider_changes_callback(data, db)
            
    except Exception as e:
        print(f"Provider changes callback processing error: {e}")

# PIS callback processors
async def process_payment_success_callback(callback_data: Dict[str, Any], db: Session):
    """Process PIS success callback in the background."""
    try:
        data = callback_data.get('data', {})
        payment_id = data.get('payment_id')
        customer_id = data.get('customer_id')
        
        print(f"Processing PAYMENT SUCCESS callback - Payment: {payment_id}, Customer: {customer_id}")
        # Future: implement payment handling
        
    except Exception as e:
        print(f"Payment success callback processing error: {e}")

async def process_payment_failure_callback(callback_data: Dict[str, Any], db: Session):
    """Process PIS failure callback in the background."""
    try:
        data = callback_data.get('data', {})
        payment_id = data.get('payment_id')
        error_class = data.get('error_class', 'unknown')
        
        print(f"Processing PAYMENT FAILURE callback - Payment: {payment_id}, Error: {error_class}")
        # Future: implement payment error handling
        
    except Exception as e:
        print(f"Payment failure callback processing error: {e}")

async def process_payment_notify_callback(callback_data: Dict[str, Any], db: Session):
    """Process PIS notify callback in the background."""
    try:
        data = callback_data.get('data', {})
        payment_id = data.get('payment_id')
        status = data.get('status', 'unknown')
        
        print(f"Processing PAYMENT NOTIFY callback - Payment: {payment_id}, Status: {status}")
        # Future: implement payment status updates
        
    except Exception as e:
        print(f"Payment notify callback processing error: {e}")

async def process_legacy_callback(callback_data: Dict[str, Any], db: Session):
    """Process legacy callback by routing to appropriate handler."""
    try:
        data = callback_data.get('data', {})
        stage = data.get('stage', 'unknown')
        
        print(f"Processing LEGACY callback - Stage: {stage}")
        
        # Route based on callback content
        if stage == 'finish':
            await process_success_callback(callback_data, db)
        elif stage == 'error' or 'error' in data:
            await process_failure_callback(callback_data, db)
        elif stage == 'notify':
            await process_notify_callback(callback_data, db)
        else:
            print(f"Unknown legacy callback stage: {stage}")
            
    except Exception as e:
        print(f"Legacy callback processing error: {e}")

# Callback handlers

async def handle_success_callback(data: Dict[str, Any], db: Session):
    """Handle successful connection callback."""
    try:
        connection_id = data.get('connection_id')
        customer_id = data.get('customer_id')
        
        if not connection_id or not customer_id:
            print("Missing connection_id or customer_id in success callback")
            return
        
        # Find customer by Salt Edge customer ID
        customer = db.query(Customer).filter(
            Customer.saltedge_customer_id == customer_id
        ).first()
        
        if not customer:
            print(f"Customer {customer_id} not found for callback")
            return
        
        print(f"Success callback: Connection {connection_id} for customer {customer.identifier}")
        
        # Trigger data sync for this customer
        sync_service = SyncService()
        sync_result = sync_service.sync_customer_data(customer.identifier, db)
        
        print(f"Auto-sync result: {sync_result}")
        
        # Update connection status if needed
        connection = db.query(Connection).filter(
            Connection.saltedge_connection_id == connection_id
        ).first()
        
        if connection:
            connection.status = 'active'
            connection.last_success_at = datetime.utcnow()
            db.commit()
            
    except Exception as e:
        db.rollback()
        print(f"Error handling success callback: {e}")

async def handle_error_callback(data: Dict[str, Any], db: Session):
    """Handle error callback."""
    try:
        connection_id = data.get('connection_id')
        error_class = data.get('error_class', 'unknown')
        error_message = data.get('error_message', 'Unknown error')
        
        print(f"Error callback: {error_class} - {error_message} (Connection: {connection_id})")
        
        if connection_id:
            # Update connection status
            connection = db.query(Connection).filter(
                Connection.saltedge_connection_id == connection_id
            ).first()
            
            if connection:
                connection.status = 'error'
                db.commit()
                print(f"Updated connection {connection_id} status to error")
                
    except Exception as e:
        db.rollback()
        print(f"Error handling error callback: {e}")

async def handle_notify_callback(data: Dict[str, Any], db: Session):
    """Handle notify callback."""
    try:
        connection_id = data.get('connection_id')
        notify_type = data.get('type', 'unknown')
        
        print(f"Notify callback: {notify_type} (Connection: {connection_id})")
        
        # Handle different notify types as needed
        if notify_type == 'provider_change':
            print(f"Provider change notification for connection {connection_id}")
        
    except Exception as e:
        print(f"Error handling notify callback: {e}")

async def handle_destroy_callback(data: Dict[str, Any], db: Session):
    """Handle destroy callback - connection being permanently removed."""
    try:
        connection_id = data.get('connection_id')
        customer_id = data.get('customer_id')
        
        print(f"Destroy callback: Connection {connection_id} being removed for customer {customer_id}")
        
        if connection_id:
            # Mark connection as removed/inactive
            connection = db.query(Connection).filter(
                Connection.saltedge_connection_id == connection_id
            ).first()
            
            if connection:
                connection.status = 'removed'
                db.commit()
                print(f"Marked connection {connection_id} as removed")
                
                # Note: You might want to decide whether to actually delete the connection
                # or just mark it as removed to preserve historical data
                
    except Exception as e:
        db.rollback()
        print(f"Error handling destroy callback: {e}")

async def handle_provider_changes_callback(data: Dict[str, Any], db: Session):
    """Handle provider changes callback."""
    try:
        provider_code = data.get('provider_code', 'unknown')
        change_type = data.get('change_type', 'unknown')
        
        print(f"Provider changes callback: Provider {provider_code}, Change: {change_type}")
        
        # Log provider changes for admin attention
        # You might want to store these in a separate table for tracking
        print(f"Provider {provider_code} has changes that may affect connections")
        
        # Optional: Notify admin users about provider changes
        # Optional: Trigger connection refresh for affected connections
        
    except Exception as e:
        print(f"Error handling provider changes callback: {e}")

@router.get("/test")
async def test_callback():
    """Test endpoint to verify callback URL is accessible."""
    return {
        "status": "ok",
        "message": "Callback endpoint is accessible",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoint": "/api/v1/callbacks/salt-edge"
    }

@router.post("/test-payload")
async def test_callback_payload(payload: dict):
    """Test endpoint to verify callback processing with a sample payload."""
    try:
        print(f"Test payload received: {payload}")
        
        # Process as if it's a real callback
        sample_callback = {
            "data": {
                "connection_id": "test_connection_123",
                "customer_id": "test_customer_456", 
                "stage": "finish",
                "custom_fields": payload
            },
            "meta": {
                "version": "6",
                "time": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        return {
            "status": "processed",
            "test_callback": sample_callback,
            "message": "Test payload processed successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test processing failed: {str(e)}")

@router.get("/setup-instructions")
async def callback_setup_instructions():
    """Get detailed instructions for setting up all Salt Edge callbacks."""
    base_url = "https://your-domain.com"  # Replace with your actual domain
    ngrok_example = "https://abc123.ngrok.io"  # Example ngrok URL
    
    return {
        "title": "Salt Edge Callback Setup Instructions",
        "description": "Configure separate URLs for each callback type for better handling",
        
        "callback_endpoints": {
            "ais": {
                "success": {
                    "url": f"{base_url}/api/v1/callbacks/ais/success",
                    "description": "Called when connection succeeds or new data is available",
                    "triggers": [
                        "Connection successfully established",
                        "New transactions fetched",
                        "Account balances updated"
                    ]
                },
                "failure": {
                    "url": f"{base_url}/api/v1/callbacks/ais/failure", 
                    "description": "Called when connection fails or errors occur",
                    "triggers": [
                        "Authentication failures",
                        "Bank temporarily unavailable",
                        "Invalid credentials"
                    ]
                },
                "notify": {
                    "url": f"{base_url}/api/v1/callbacks/ais/notify",
                    "description": "Called for general notifications and status updates",
                    "triggers": [
                        "Additional user action required",
                        "Connection status changes",
                        "Provider updates"
                    ]
                },
                "destroy": {
                    "url": f"{base_url}/api/v1/callbacks/ais/destroy",
                    "description": "Called when connection is permanently removed",
                    "triggers": [
                        "User revokes consent",
                        "Connection cleanup",
                        "Account closure"
                    ]
                },
                "provider_changes": {
                    "url": f"{base_url}/api/v1/callbacks/ais/provider-changes",
                    "description": "Called when providers update their APIs",
                    "triggers": [
                        "Provider API changes",
                        "New fields available",
                        "Authentication method updates"
                    ]
                }
            },
            "pis": {
                "success": {
                    "url": f"{base_url}/api/v1/callbacks/pis/success",
                    "description": "Called when payment is successful",
                    "triggers": [
                        "Payment initiated successfully",
                        "Payment completed"
                    ]
                },
                "failure": {
                    "url": f"{base_url}/api/v1/callbacks/pis/failure",
                    "description": "Called when payment fails",
                    "triggers": [
                        "Payment rejected",
                        "Insufficient funds",
                        "Payment processing error"
                    ]
                },
                "notify": {
                    "url": f"{base_url}/api/v1/callbacks/pis/notify",
                    "description": "Called for payment status updates",
                    "triggers": [
                        "Payment status changes",
                        "Additional authorization required"
                    ]
                }
            },
            "legacy": {
                "single_endpoint": {
                    "url": f"{base_url}/api/v1/callbacks/salt-edge",
                    "description": "Single endpoint handling all callback types (backward compatibility)",
                    "note": "Use specific endpoints above for better handling"
                }
            }
        },

        "setup_steps": [
            {
                "step": 1,
                "description": "Go to your Salt Edge Dashboard",
                "url": "https://www.saltedge.com/clients/profile"
            },
            {
                "step": 2,
                "description": "Navigate to 'Callbacks' section",
                "details": "Look for AIS and PIS callback configuration"
            },
            {
                "step": 3,
                "description": "Configure AIS callback URLs",
                "settings": {
                    "AIS Success URL": f"{base_url}/api/v1/callbacks/ais/success",
                    "AIS Failure URL": f"{base_url}/api/v1/callbacks/ais/failure", 
                    "AIS Notify URL": f"{base_url}/api/v1/callbacks/ais/notify",
                    "AIS Destroy URL": f"{base_url}/api/v1/callbacks/ais/destroy",
                    "AIS Provider Changes URL": f"{base_url}/api/v1/callbacks/ais/provider-changes"
                }
            },
            {
                "step": 4,
                "description": "Configure PIS callback URLs (if using payments)",
                "settings": {
                    "PIS Success URL": f"{base_url}/api/v1/callbacks/pis/success",
                    "PIS Failure URL": f"{base_url}/api/v1/callbacks/pis/failure",
                    "PIS Notify URL": f"{base_url}/api/v1/callbacks/pis/notify"
                }
            },
            {
                "step": 5,
                "description": "Test callback accessibility",
                "test_url": f"{base_url}/api/v1/callbacks/test"
            }
        ],

        "local_development": {
            "ngrok_setup": {
                "install": "Download from https://ngrok.com/",
                "start": "ngrok http 8000",
                "helper_script": "python setup_ngrok.py"
            },
            "example_urls": {
                "AIS Success": f"{ngrok_example}/api/v1/callbacks/ais/success",
                "AIS Failure": f"{ngrok_example}/api/v1/callbacks/ais/failure",
                "AIS Notify": f"{ngrok_example}/api/v1/callbacks/ais/notify",
                "AIS Destroy": f"{ngrok_example}/api/v1/callbacks/ais/destroy",
                "Provider Changes": f"{ngrok_example}/api/v1/callbacks/ais/provider-changes"
            },
            "note": "ngrok URLs change each restart with free account"
        },

        "production_requirements": [
            "HTTPS endpoints (required by Salt Edge)",
            "Valid SSL certificates", 
            "Accessible from Salt Edge servers",
            "Implement signature verification",
            "Handle high availability",
            "Monitor callback performance"
        ],

        "testing": {
            "accessibility_test": "GET /api/v1/callbacks/test",
            "payload_test": "POST /api/v1/callbacks/test-payload",
            "monitor_webhooks": "Check ngrok interface at http://localhost:4040"
        },

        "benefits_of_separate_endpoints": [
            "Better error handling for specific scenarios",
            "Easier debugging and monitoring",
            "Different processing logic per callback type",
            "More granular logging and analytics",
            "Ability to route to different services"
        ]
    }
