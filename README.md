# Money Manager App

A comprehensive personal finance management application that integrates with [Salt Edge API](https://docs.saltedge.com/v6/api_reference#ais-callbacks-success) to fetch banking data and creates financial dashboards in Google Docs.

## Features

- 🏦 **Bank Integration**: Connect to 3000+ banks worldwide via Salt Edge API
- 💰 **Account Management**: Track multiple bank accounts and their balances  
- 📊 **Transaction Analysis**: Categorize and analyze spending patterns
- 🔄 **Automatic Sync**: Keep data synchronized with your banks
- 📝 **Google Docs Dashboards**: Generate beautiful financial reports
- 🗄️ **SQLite Storage**: Local database for fast data access
- 🚀 **REST API**: Full API for integration with other applications

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│                 │    │                  │    │                 │
│   Salt Edge     │◄───┤  Money Manager   │───►│  Google Docs    │
│   API           │    │  Application     │    │  Integration    │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                               │
                               ▼
                       ┌──────────────────┐
                       │                  │
                       │  SQLite Database │
                       │                  │
                       └──────────────────┘
```

## Quick Start

### 1. Prerequisites

- Python 3.8+
- Salt Edge API credentials (get them at [Salt Edge Dashboard](https://www.saltedge.com/dashboard))
- Google Cloud Console project with Docs API enabled (optional, for dashboard features)

### 2. Installation

#### Quick Setup with UV (Recommended)
```bash
# Clone the repository
git clone <repository-url>
cd money_manager

# Setup development environment (installs UV if needed)
chmod +x setup-dev.sh
./setup-dev.sh

# Edit environment variables
nano .env
```

#### Alternative: Manual Setup
```bash
# Install UV package manager (much faster than pip)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e ".[dev]"

# Set up environment variables
cp env.production.template .env
# Edit .env with your actual credentials
```

#### Legacy: pip installation
```bash
# Traditional pip installation (slower)
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the root directory:

```bash
# Salt Edge API Configuration
SALTEDGE_BASE_URL=https://www.saltedge.com/api/v6
SALTEDGE_APP_ID=your_salt_edge_app_id
SALTEDGE_SECRET_KEY=your_salt_edge_secret_key
SALTEDGE_CLIENT_ID=your_salt_edge_client_id

# Database Configuration
DATABASE_URL=sqlite:///./money_manager.db

# Google API Configuration (optional)
GOOGLE_CREDENTIALS_FILE=path/to/your/credentials.json
GOOGLE_TOKEN_FILE=path/to/your/token.json

# Application Configuration
DEBUG=True
API_HOST=0.0.0.0
API_PORT=8000
```

### 4. Run the Application

#### With UV (Recommended)
```bash
# Start development server with hot reload
uv run uvicorn main:app --reload --port 8000

# Or run directly
uv run python main.py
```

#### Legacy Method
```bash
# Traditional approach
python main.py
# Or: uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Visit `http://localhost:8000/docs` for the interactive API documentation.

## Usage Guide

### 1. Create a Customer

```bash
curl -X POST "http://localhost:8000/api/v1/customers/" \
     -H "Content-Type: application/json" \
     -d '{
       "identifier": "john_doe_123",
       "email": "john@example.com",
       "first_name": "John",
       "last_name": "Doe",
       "phone": "+1234567890"
     }'
```

### 2. List Available Banks

```bash
# Get supported countries
curl "http://localhost:8000/api/v1/sync/countries"

# Get banks for a specific country (e.g., GB for United Kingdom)
curl "http://localhost:8000/api/v1/sync/providers?country_code=GB"
```

### 3. Connect to a Bank

```bash
curl -X POST "http://localhost:8000/api/v1/connections/customer/1" \
     -H "Content-Type: application/json" \
     -d '{
       "country_code": "GB",
       "provider_code": "lloyds_gb",
       "consent": {
         "scopes": ["account_details", "transactions_details"],
         "period_days": 90
       }
     }'
```

This returns a `connect_url` that the user must visit to complete the bank connection.

### 4. Sync Bank Data

```bash
# Sync data for a customer
curl -X POST "http://localhost:8000/api/v1/sync/customer" \
     -H "Content-Type: application/json" \
     -d '{"customer_identifier": "john_doe_123"}'
```

### 5. View Financial Data

```bash
# Get customer accounts
curl "http://localhost:8000/api/v1/accounts/customer/1"

# Get customer transactions
curl "http://localhost:8000/api/v1/transactions/customer/1"

# Get financial summary
curl "http://localhost:8000/api/v1/transactions/customer/1/summary"
```

### 6. Set Up Callbacks (Important for Real-time Updates)

For development, you'll need ngrok to expose your local server to Salt Edge:

```bash
# Install and set up ngrok (one-time setup)
python setup_ngrok.py

# This will give you a public URL like: https://abc123.ngrok.io
# Use this URL in your Salt Edge Dashboard callback configuration
```

Configure in Salt Edge Dashboard (AIS - Account Information):
- Success URL: `https://abc123.ngrok.io/api/v1/callbacks/ais/success`
- Failure URL: `https://abc123.ngrok.io/api/v1/callbacks/ais/failure`
- Notify URL: `https://abc123.ngrok.io/api/v1/callbacks/ais/notify`
- Destroy URL: `https://abc123.ngrok.io/api/v1/callbacks/ais/destroy`
- Provider Changes URL: `https://abc123.ngrok.io/api/v1/callbacks/ais/provider-changes`

Configure in Salt Edge Dashboard (PIS - Payment Initiation, if using payments):
- Success URL: `https://abc123.ngrok.io/api/v1/callbacks/pis/success`
- Failure URL: `https://abc123.ngrok.io/api/v1/callbacks/pis/failure`
- Notify URL: `https://abc123.ngrok.io/api/v1/callbacks/pis/notify`

**Alternative**: Use single endpoint for all types (legacy):
- All Types: `https://abc123.ngrok.io/api/v1/callbacks/salt-edge`

### 7. Generate Google Docs Dashboard

```bash
curl -X POST "http://localhost:8000/api/v1/dashboards/customer/1" \
     -H "Content-Type: application/json" \
     -d '{"period_months": 6}'
```

## API Endpoints

### Customers
- `POST /api/v1/customers/` - Create customer
- `GET /api/v1/customers/` - List customers
- `GET /api/v1/customers/{id}` - Get customer
- `DELETE /api/v1/customers/{id}` - Delete customer

### Connections
- `GET /api/v1/connections/customer/{id}` - List customer connections
- `POST /api/v1/connections/customer/{id}` - Create connection
- `PUT /api/v1/connections/{id}/refresh` - Refresh connection
- `DELETE /api/v1/connections/{id}` - Delete connection

### Accounts
- `GET /api/v1/accounts/customer/{id}` - List customer accounts
- `GET /api/v1/accounts/connection/{id}` - List connection accounts
- `GET /api/v1/accounts/{id}` - Get account details
- `GET /api/v1/accounts/customer/{id}/summary` - Get accounts summary

### Transactions
- `GET /api/v1/transactions/customer/{id}` - List customer transactions
- `GET /api/v1/transactions/account/{id}` - List account transactions
- `GET /api/v1/transactions/{id}` - Get transaction details
- `GET /api/v1/transactions/customer/{id}/summary` - Get spending analysis

### Data Synchronization
- `POST /api/v1/sync/customer` - Sync customer data
- `GET /api/v1/sync/providers` - List available banks
- `GET /api/v1/sync/countries` - List supported countries

### Dashboards
- `POST /api/v1/dashboards/customer/{id}` - Create financial dashboard
- `POST /api/v1/dashboards/customer/{id}/monthly-report` - Create monthly report

### Callbacks
**AIS (Account Information) Callbacks:**
- `POST /api/v1/callbacks/ais/success` - Connection success and data updates
- `POST /api/v1/callbacks/ais/failure` - Connection failures and errors  
- `POST /api/v1/callbacks/ais/notify` - General notifications and status updates
- `POST /api/v1/callbacks/ais/destroy` - Connection removal and cleanup
- `POST /api/v1/callbacks/ais/provider-changes` - Provider API changes

**PIS (Payment Initiation) Callbacks:**
- `POST /api/v1/callbacks/pis/success` - Payment success notifications
- `POST /api/v1/callbacks/pis/failure` - Payment failure notifications
- `POST /api/v1/callbacks/pis/notify` - Payment status updates

**Utility Endpoints:**
- `POST /api/v1/callbacks/salt-edge` - Legacy single endpoint (all types)
- `GET /api/v1/callbacks/test` - Test callback accessibility
- `GET /api/v1/callbacks/setup-instructions` - Detailed setup instructions

### Status & Diagnostics
- `GET /api/v1/status/saltedge-account` - Check Salt Edge account status
- `GET /api/v1/status/test-providers` - List fake providers for testing
- `GET /api/v1/status/next-steps` - Get personalized next steps

## Google Docs Integration Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Docs API and Google Drive API
4. Create credentials (OAuth 2.0 Client IDs) for desktop application
5. Download the credentials JSON file
6. Set `GOOGLE_CREDENTIALS_FILE` in your `.env` file
7. Run the application - you'll be prompted to authenticate on first use

## Database Schema

The application uses SQLite with the following main entities:

- **Customers**: Your application users
- **Connections**: Bank connections via Salt Edge
- **Accounts**: Bank accounts from connected institutions
- **Transactions**: Individual transactions from accounts

## Docker Deployment 🐳

### Quick Production Deployment

```bash
# Clone and setup
git clone <your-repo> money-manager
cd money-manager
chmod +x deploy.sh

# Deploy with automatic SSL (uses UV for faster builds)
./deploy.sh deploy
./deploy.sh ssl

# Check status
./deploy.sh status
```

### Environment Configuration

```bash
# Copy and edit environment file
cp env.production.template .env
nano .env

# Required settings:
DOMAIN=your-domain.com
SSL_EMAIL=your-email@example.com
SALTEDGE_APP_ID=your_app_id
SALTEDGE_SECRET_KEY=your_secret_key
```

### Docker Build Troubleshooting

If you encounter UV installation issues during Docker build:

```bash
docker-compose -f docker-compose.prod.yml build --no-cache
```

### Production URLs

After deployment, your Salt Edge callbacks will be:
- **Success**: `https://your-domain.com/api/v1/callbacks/ais/success`
- **Failure**: `https://your-domain.com/api/v1/callbacks/ais/failure`
- **Notify**: `https://your-domain.com/api/v1/callbacks/ais/notify`
- **Destroy**: `https://your-domain.com/api/v1/callbacks/ais/destroy`
- **Provider Changes**: `https://your-domain.com/api/v1/callbacks/ais/provider-changes`

### Development with Docker

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f
```

📖 **[Complete Deployment Guide](DEPLOYMENT.md)** - Detailed production deployment instructions

## 🔒 Security & Git

### Git Ignore
The `.gitignore` file is configured to protect sensitive data:

```bash
# Never committed to Git:
.env                    # Environment variables with secrets
ssl/                    # SSL certificates and private keys  
credentials/            # Google API credentials
data/                   # SQLite database files
logs/                   # Application logs
backups/                # Database backups
```

**Before first commit:**
```bash
# Copy and configure environment
cp env.production.template .env
nano .env  # Add your actual API keys

# The .env file is automatically ignored by Git
git add .
git commit -m "Initial commit - sensitive files protected"
```

## Development with UV ⚡

### Why UV?
- **🚀 10-100x faster** than pip for installs
- **🔒 Deterministic builds** with lockfiles
- **⚡ Better caching** and dependency resolution
- **🏗️ Modern Python toolchain** (like npm/yarn for Node.js)

### Development Commands

```bash
# Setup development environment
./setup-dev.sh

# Add new dependencies
uv add requests beautifulsoup4
uv add pytest --dev  # Development dependency

# Remove dependencies  
uv remove package-name

# Install from lockfile (production)
uv pip install --locked

# Update dependencies
uv lock --upgrade

# Run commands in environment
uv run pytest tests/
uv run black .
uv run mypy .
uv run ruff check .
```

### Development Workflow

```bash
# 1. Start development server with hot reload
uv run uvicorn main:app --reload

# 2. Run tests (with coverage)
uv run pytest tests/ --cov=. --cov-report=html

# 3. Format and lint code
./setup-dev.sh format

# 4. Type checking
./setup-dev.sh type-check

# 5. Run all quality checks
uv run pre-commit run --all-files
```

### Legacy Development (pip)

For teams not ready for UV:

```bash
# Traditional testing
pytest tests/

# Legacy installation  
pip install -r requirements.txt
```

### Code Structure

```
├── api/                 # FastAPI routes
│   ├── customers.py
│   ├── connections.py
│   ├── accounts.py
│   ├── transactions.py
│   ├── sync.py
│   └── dashboards.py
├── models/              # SQLAlchemy models
│   ├── customer.py
│   ├── connection.py
│   ├── account.py
│   └── transaction.py
├── services/            # Business logic
│   ├── saltedge_client.py
│   ├── sync_service.py
│   └── google_docs_service.py
├── config.py           # Configuration
├── main.py             # FastAPI application
└── requirements.txt    # Dependencies
```

### Adding New Features

1. Add new models in `models/`
2. Create services in `services/`
3. Add API endpoints in `api/`
4. Update the main application in `main.py`

## Salt Edge Integration

This app uses Salt Edge Account Information Services (AIS) API v6. Key features:

- **Customer Management**: Create customers in Salt Edge
- **Connection Flow**: Secure bank authentication
- **Data Fetching**: Accounts, transactions, balances
- **Webhooks**: Real-time data updates (future enhancement)
- **Consent Management**: PSD2 compliant consent handling

### Supported Regions

Salt Edge supports banks in 50+ countries including:
- 🇬🇧 United Kingdom
- 🇪🇺 European Union
- 🇺🇸 United States  
- 🇨🇦 Canada
- 🇦🇺 Australia
- And many more...

## Troubleshooting

### Common Issues

1. **Salt Edge API Errors**
   - Check your API credentials
   - Ensure your Salt Edge account is active
   - Verify the provider code is correct

2. **Database Issues**
   - Delete `money_manager.db` to reset the database
   - Check file permissions

3. **Google Docs Authentication**
   - Ensure APIs are enabled in Google Cloud Console
   - Check credentials file path
   - Re-authenticate if tokens expire

### Logging

The application logs to console by default. For production, configure proper logging:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Deployment

### Using Docker (Future Enhancement)

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables for Production

```bash
DEBUG=False
DATABASE_URL=postgresql://user:password@localhost/money_manager
API_HOST=0.0.0.0
API_PORT=8000
```

## Security Considerations

- Store Salt Edge credentials securely
- Use HTTPS in production
- Implement proper authentication for your API
- Regular security updates
- Monitor API usage and logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For support with:
- **Salt Edge API**: [Salt Edge Documentation](https://docs.saltedge.com/)
- **Google APIs**: [Google Docs API Documentation](https://developers.google.com/docs/api)
- **This Application**: Open an issue in the repository

---

**Note**: This application is for educational/personal use. For production use, implement proper authentication, error handling, and security measures.
