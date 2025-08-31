# Money Manager - Production Deployment Guide

This guide will help you deploy the Money Manager application to your server using Docker and Docker Compose with HTTPS support for Salt Edge webhooks.

## 📋 Prerequisites

- **Server**: Linux server with Docker and Docker Compose installed
- **Domain**: A domain name pointing to your server's IP address
- **Salt Edge**: Account with API credentials
- **SSL**: Domain validation for Let's Encrypt certificates
- **Ports**: 80 and 443 open on your server

## 🚀 Quick Deployment

### 1. Clone and Setup

```bash
# Clone your repository
git clone <your-repo> money-manager
cd money-manager

# Make deployment script executable
chmod +x deploy.sh

# Run the deployment script
./deploy.sh deploy
```

### 2. Configure Environment

The script will create a `.env` file from the template. Update it with your values:

```bash
# Edit the environment file
nano .env
```

**Required Configuration:**
```env
# Your domain and email for SSL
DOMAIN=your-domain.com
SSL_EMAIL=your-email@example.com

# Salt Edge API credentials (from https://www.saltedge.com/clients/profile/secrets)
SALTEDGE_APP_ID=your_production_app_id
SALTEDGE_SECRET_KEY=your_production_secret_key
SALTEDGE_CLIENT_ID=your_production_client_id
```

### 3. Setup SSL Certificates

```bash
./deploy.sh ssl
```

This will:
- Obtain Let's Encrypt certificates for your domain
- Configure nginx with HTTPS
- Restart services with SSL enabled

### 4. Configure Salt Edge Callbacks

Go to your [Salt Edge Dashboard](https://www.saltedge.com/clients/profile) and configure these callback URLs:

**AIS (Account Information) Callbacks:**
- Success URL: `https://your-domain.com/api/v1/callbacks/ais/success`
- Failure URL: `https://your-domain.com/api/v1/callbacks/ais/failure`
- Notify URL: `https://your-domain.com/api/v1/callbacks/ais/notify`
- Destroy URL: `https://your-domain.com/api/v1/callbacks/ais/destroy`
- Provider Changes URL: `https://your-domain.com/api/v1/callbacks/ais/provider-changes`

**PIS (Payment Initiation) Callbacks** (if using payments):
- Success URL: `https://your-domain.com/api/v1/callbacks/pis/success`
- Failure URL: `https://your-domain.com/api/v1/callbacks/pis/failure`
- Notify URL: `https://your-domain.com/api/v1/callbacks/pis/notify`

## 🛠️ Manual Deployment Steps

If you prefer manual deployment or need custom configuration:

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Application Setup

```bash
# Create application directory
mkdir -p /opt/money-manager
cd /opt/money-manager

# Copy your application files
# ... copy all files from your development environment

# Create necessary directories
mkdir -p data logs ssl credentials backups monitoring certbot/www

# Set permissions
sudo chown -R $USER:$USER /opt/money-manager
chmod +x deploy.sh
```

### 3. Environment Configuration

```bash
# Copy and edit environment file
cp env.production.template .env
nano .env
```

### 4. Deploy Application

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d money-manager nginx

# Check status
docker-compose -f docker-compose.prod.yml ps
```

### 5. SSL Certificate Setup

```bash
# Stop nginx temporarily
docker-compose -f docker-compose.prod.yml stop nginx

# Get certificates
docker-compose -f docker-compose.prod.yml --profile ssl-setup run --rm certbot

# Copy certificates to nginx directory
sudo cp ssl/live/your-domain.com/fullchain.pem ssl/
sudo cp ssl/live/your-domain.com/privkey.pem ssl/

# Start nginx with SSL
docker-compose -f docker-compose.prod.yml up -d nginx
```

## 🔧 Management Commands

Use the `deploy.sh` script for easy management:

```bash
# Show deployment status
./deploy.sh status

# View logs
./deploy.sh logs

# Restart application
./deploy.sh restart

# Stop application
./deploy.sh stop

# Update application
./deploy.sh update

# Start backup service
./deploy.sh backup

# Show help
./deploy.sh help
```

## 📁 Directory Structure

```
money-manager/
├── data/                   # SQLite database storage
├── logs/                   # Application logs
├── ssl/                    # SSL certificates
├── credentials/            # Google API credentials
├── backups/                # Database backups
├── monitoring/             # Health check logs
├── nginx/                  # Nginx configuration
│   ├── nginx.conf
│   └── default.conf
├── certbot/                # Let's Encrypt webroot
├── docker-compose.yml      # Development compose
├── docker-compose.prod.yml # Production compose
├── docker-compose.dev.yml  # Development with live reload
├── Dockerfile              # Application container
├── deploy.sh               # Deployment script
└── env.production.template # Environment template
```

## 🔐 Security Considerations

### SSL/TLS Configuration
- **Let's Encrypt**: Automatic SSL certificates
- **Strong Ciphers**: TLS 1.2+ with secure cipher suites
- **HSTS**: HTTP Strict Transport Security enabled
- **Security Headers**: X-Frame-Options, X-Content-Type-Options, etc.

### Rate Limiting
- **API Endpoints**: 10 requests/second per IP
- **Callback Endpoints**: 50 requests/second per IP (for webhooks)
- **Burst Protection**: Configurable burst limits

### Network Security
- **Internal Network**: Services communicate on isolated Docker network
- **Firewall**: Only ports 80 and 443 exposed
- **Non-root User**: Application runs as non-privileged user

## 📊 Monitoring and Maintenance

### Health Checks
- **Application**: Built-in health endpoint at `/health`
- **Database**: SQLite file integrity
- **SSL**: Certificate expiration monitoring

### Logging
- **Application Logs**: Stored in `./logs/` directory
- **Nginx Logs**: Access and error logs
- **Docker Logs**: Container-level logging with rotation

### Backups
- **Database**: Automated daily backups with 30-day retention
- **Configuration**: Manual backup of `.env` and certificates
- **Location**: `./backups/` directory

### Updates
```bash
# Update application
./deploy.sh update

# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker-compose -f docker-compose.prod.yml pull
```

## 🚨 Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check logs
./deploy.sh logs

# Check container status
docker-compose -f docker-compose.prod.yml ps

# Rebuild containers
docker-compose -f docker-compose.prod.yml build --no-cache
```

#### SSL Certificate Issues
```bash
# Check domain DNS
nslookup your-domain.com

# Verify nginx configuration
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# Renew certificates
docker-compose -f docker-compose.prod.yml --profile ssl-setup run --rm certbot renew
```

#### Database Issues
```bash
# Check database file permissions
ls -la data/

# View database logs
docker-compose -f docker-compose.prod.yml logs money-manager

# Restore from backup
cp backups/money_manager_YYYYMMDD_HHMMSS.db data/money_manager.db
```

#### Salt Edge Callback Issues
```bash
# Check callback accessibility
curl -f https://your-domain.com/api/v1/callbacks/test

# Monitor callback traffic
./deploy.sh logs | grep callback

# Verify webhook signatures in logs
```

### Performance Tuning

#### Nginx Configuration
- Adjust `worker_processes` and `worker_connections`
- Configure appropriate cache settings
- Optimize SSL session caching

#### Application Configuration
- Monitor memory usage with `docker stats`
- Adjust container resource limits if needed
- Scale horizontally by running multiple app instances

#### Database Optimization
- Regular VACUUM operations for SQLite
- Monitor database file size growth
- Consider WAL mode for better concurrency

## 🔄 Development Workflow

For development with Docker:

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# View development logs
docker-compose -f docker-compose.dev.yml logs -f

# Access development environment
# Application: http://localhost:8000
# Database viewer: http://localhost:8080 (with tools profile)
```

## 📞 Support

For issues:
1. Check the logs: `./deploy.sh logs`
2. Review the troubleshooting section
3. Check Salt Edge documentation: [docs.saltedge.com](https://docs.saltedge.com/)
4. Verify callback setup in Salt Edge Dashboard

## 🎯 Next Steps After Deployment

1. **Test the deployment**: Visit `https://your-domain.com/health`
2. **Configure callbacks**: Set up Salt Edge Dashboard callbacks
3. **Create first customer**: Use the API to test the integration
4. **Monitor logs**: Watch for any errors or issues
5. **Set up backups**: Configure automated backup strategy
6. **Security review**: Review firewall and access controls
7. **Performance monitoring**: Set up monitoring tools if needed

Your Money Manager application is now ready for production use! 🎉
