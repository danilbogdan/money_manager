"""
Configuration settings for the Money Manager application.

Create a .env file in the root directory with the following variables:

# Salt Edge API Configuration
SALTEDGE_BASE_URL=https://www.saltedge.com/api/v6
SALTEDGE_APP_ID=your_app_id
SALTEDGE_SECRET_KEY=your_secret_key
SALTEDGE_CLIENT_ID=your_client_id

# Database Configuration
DATABASE_URL=sqlite:///./money_manager.db

# Google API Configuration
GOOGLE_CREDENTIALS_FILE=path/to/credentials.json
GOOGLE_TOKEN_FILE=path/to/token.json

# Application Configuration
DEBUG=True
API_HOST=0.0.0.0
API_PORT=8000
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Salt Edge API Configuration
    SALTEDGE_BASE_URL = os.getenv("SALTEDGE_BASE_URL", "https://www.saltedge.com/api/v6")
    SALTEDGE_APP_ID = os.getenv("SALTEDGE_APP_ID")
    SALTEDGE_SECRET_KEY = os.getenv("SALTEDGE_SECRET_KEY")
    SALTEDGE_CLIENT_ID = os.getenv("SALTEDGE_CLIENT_ID")
    
    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./money_manager.db")
    
    # Google API Configuration
    GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE")
    GOOGLE_TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE")
    
    # Application Configuration
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))

settings = Settings()
