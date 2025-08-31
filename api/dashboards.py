from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from models.base import get_db
from models import Customer
from services import GoogleDocsService

router = APIRouter(prefix="/dashboards", tags=["dashboards"])

class DashboardRequest(BaseModel):
    period_months: int = 6

class MonthlyReportRequest(BaseModel):
    year: int
    month: int

@router.post("/customer/{customer_id}")
async def create_customer_dashboard(
    customer_id: int,
    dashboard_request: DashboardRequest,
    db: Session = Depends(get_db)
):
    """Create a financial dashboard for a customer in Google Docs."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    try:
        google_docs_service = GoogleDocsService()
        doc_url = google_docs_service.create_financial_dashboard(
            customer_id=customer_id,
            period_months=dashboard_request.period_months
        )
        
        return {
            "customer_id": customer_id,
            "dashboard_url": doc_url,
            "message": "Dashboard created successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create dashboard: {str(e)}")

@router.post("/customer/{customer_id}/monthly-report")
async def create_monthly_report(
    customer_id: int,
    report_request: MonthlyReportRequest,
    db: Session = Depends(get_db)
):
    """Create a monthly financial report for a customer."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    try:
        google_docs_service = GoogleDocsService()
        doc_url = google_docs_service.create_monthly_report(
            customer_id=customer_id,
            year=report_request.year,
            month=report_request.month
        )
        
        return {
            "customer_id": customer_id,
            "report_url": doc_url,
            "period": f"{report_request.year}-{report_request.month:02d}",
            "message": "Monthly report created successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create report: {str(e)}")

@router.post("/customer/{customer_id}/background")
async def create_dashboard_background(
    customer_id: int,
    dashboard_request: DashboardRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create dashboard in the background."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Add background task
    background_tasks.add_task(
        create_dashboard_background_task,
        customer_id,
        dashboard_request.period_months
    )
    
    return {"message": f"Dashboard creation initiated in background for customer {customer_id}"}

async def create_dashboard_background_task(customer_id: int, period_months: int):
    """Background task for creating dashboard."""
    try:
        google_docs_service = GoogleDocsService()
        doc_url = google_docs_service.create_financial_dashboard(
            customer_id=customer_id,
            period_months=period_months
        )
        print(f"Dashboard created in background for customer {customer_id}: {doc_url}")
    except Exception as e:
        print(f"Background dashboard creation failed for customer {customer_id}: {str(e)}")
