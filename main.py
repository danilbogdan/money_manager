from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from models.base import init_db
from api import (
    customers_router,
    connections_router, 
    accounts_router,
    transactions_router,
    sync_router,
    dashboards_router,
    status_router,
    callbacks_router
)
from config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Initializing database...")
    init_db()
    print("Database initialized successfully!")
    yield
    # Shutdown
    print("Shutting down...")

app = FastAPI(
    title="Money Manager API",
    description="""
    A comprehensive money management application that uses Salt Edge API to fetch banking data
    and creates financial dashboards in Google Docs.
    
    ## Features
    
    * **Customer Management**: Create and manage customers
    * **Bank Connections**: Connect to banks via Salt Edge API
    * **Account Tracking**: Monitor multiple bank accounts
    * **Transaction Analysis**: Track and categorize transactions
    * **Data Synchronization**: Sync data from banks automatically
    * **Google Docs Integration**: Create financial dashboards and reports
    
    ## Getting Started
    
    1. Create a customer
    2. Add bank connections using Salt Edge providers
    3. Sync data to fetch accounts and transactions
    4. Generate financial dashboards in Google Docs
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(customers_router, prefix="/api/v1")
app.include_router(connections_router, prefix="/api/v1")
app.include_router(accounts_router, prefix="/api/v1")
app.include_router(transactions_router, prefix="/api/v1")
app.include_router(sync_router, prefix="/api/v1")
app.include_router(dashboards_router, prefix="/api/v1")
app.include_router(status_router, prefix="/api/v1")
app.include_router(callbacks_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Money Manager API",
        "version": "1.0.0",
        "description": "Personal finance management with Salt Edge integration",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Money Manager API is running"}

@app.get("/api/v1/info")
async def api_info():
    """API configuration information (non-sensitive)."""
    return {
        "saltedge_base_url": settings.SALTEDGE_BASE_URL,
        "database_type": "SQLite" if "sqlite" in settings.DATABASE_URL else "Other",
        "google_docs_enabled": bool(settings.GOOGLE_CREDENTIALS_FILE),
        "debug_mode": settings.DEBUG
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
