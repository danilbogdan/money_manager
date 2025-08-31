#!/bin/bash

# Money Manager Deployment Script
# This script helps deploy the Money Manager application to your server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
check_env_file() {
    if [ ! -f ".env" ]; then
        print_error ".env file not found!"
        print_status "Creating .env file from template..."
        cp env.production.template .env
        print_warning "Please edit .env file with your actual configuration values"
        print_warning "Required: DOMAIN, SSL_EMAIL, SALTEDGE_* variables"
        echo -e "${YELLOW}Edit .env file now? (y/n):${NC} "
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            ${EDITOR:-nano} .env
        else
            print_error "Please edit .env file before proceeding"
            exit 1
        fi
    fi
}

# Check required dependencies
check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    print_success "Dependencies check passed"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    mkdir -p data logs credentials backups
    
    # Set proper permissions for Docker volumes
    chmod 777 data logs credentials 2>/dev/null || true
    
    print_success "Directories created with proper permissions"
}

# Build and start services
deploy_application() {
    print_status "Building and starting Money Manager..."
    
    # Stop existing containers
    docker compose down 2>/dev/null || true
    
    # Build and start
    docker compose build
    docker compose up -d money-manager
    
    print_success "Application deployed successfully"
}

# Setup SSL certificates
setup_ssl() {
    print_status "Setting up SSL certificates..."
    
    # Check if domain is set
    if ! grep -q "DOMAIN=your-domain.com" .env; then
        # Get SSL certificate
        docker compose -f docker compose.prod.yml --profile ssl-setup run --rm certbot
        
        # Copy certificates to correct location
        sudo cp ssl/live/$(grep DOMAIN .env | cut -d'=' -f2)/fullchain.pem ssl/
        sudo cp ssl/live/$(grep DOMAIN .env | cut -d'=' -f2)/privkey.pem ssl/
        
        print_success "SSL certificates configured"
    else
        print_warning "Please set your domain in .env file first"
        return 1
    fi
}

# Check application health
check_health() {
    print_status "Checking application health..."
    
    # Wait for application to start
    sleep 30
    
    if docker compose exec money-manager curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Application is healthy"
        return 0
    else
        print_error "Application health check failed"
        return 1
    fi
}

# Show deployment status
show_status() {
    print_status "Deployment Status:"
    docker compose ps
    
    echo ""
    print_status "Application URLs (configure in your nginx):"
    print_status "Application runs on: http://localhost:8000"
    echo "  🌐 Application: http://localhost:8000"
    echo "  📚 API Documentation: http://localhost:8000/docs"
    echo "  ❤️  Health Check: http://localhost:8000/health"
    
    echo ""
    print_status "Configure these Salt Edge Callback URLs in your nginx:"
    echo "  📞 AIS Success: https://your-domain.com/api/v1/callbacks/ais/success"
    echo "  📞 AIS Failure: https://your-domain.com/api/v1/callbacks/ais/failure"
    echo "  📞 AIS Notify: https://your-domain.com/api/v1/callbacks/ais/notify"
    echo "  📞 AIS Destroy: https://your-domain.com/api/v1/callbacks/ais/destroy"
    echo "  📞 Provider Changes: https://your-domain.com/api/v1/callbacks/ais/provider-changes"
}

# Main deployment function
main() {
    echo "🚀 Money Manager Deployment Script"
    echo "=================================="
    echo ""
    
    # Check environment
    check_env_file
    check_dependencies
    
    # Create directories
    create_directories
    
    # Deploy application
    deploy_application
    
    # Check health
    if check_health; then
        show_status
        
        echo ""
        print_success "Deployment completed successfully! 🎉"
        echo ""
        print_status "Next steps:"
        echo "1. Configure your DNS to point to this server"
        echo "2. Run './deploy.sh ssl' to setup SSL certificates"
        echo "3. Configure Salt Edge callbacks in your dashboard"
        echo "4. Test the application"
        
    else
        print_error "Deployment failed. Check logs with: docker compose -f docker compose.prod.yml logs"
        exit 1
    fi
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "ssl")
        setup_ssl
        if [ $? -eq 0 ]; then
            print_status "SSL certificates configured - restart your nginx to use them"
        fi
        ;;
    "status")
        show_status
        ;;
    "logs")
        docker compose logs -f
        ;;
    "stop")
        print_status "Stopping Money Manager..."
        docker compose down
        print_success "Stopped"
        ;;
    "restart")
        print_status "Restarting Money Manager..."
        docker compose restart
        print_success "Restarted"
        ;;
    "backup")
        print_status "Starting backup service..."
        docker compose --profile backup up -d backup
        print_success "Backup service started"
        ;;
    "adminer")
        print_status "Building and starting Adminer database management..."
        docker compose --profile adminer build adminer --no-cache
        docker compose --profile adminer up -d adminer
        print_success "Adminer started - access via http://localhost:8080"
        echo ""
        print_status "Adminer access information:"
        echo "  🌐 Local access: http://localhost:8080"
        echo "  🌐 Web access: https://danilbogdan.com/adminer/ (if nginx configured)"
        echo ""
        print_status "Login credentials:"
        echo "  Server: sqlite:///data/money_manager.db"
        echo "  Username: (leave empty)"
        echo "  Password: admin"
        echo ""
        print_status "The SQLite database will be accessible after web login."
        ;;
    "stop-adminer")
        print_status "Stopping Adminer..."
        docker compose stop adminer
        docker compose rm -f adminer
        print_success "Adminer stopped"
        ;;
    "update")
        print_status "Updating Money Manager..."
        docker compose down
        docker compose build --no-cache
        docker compose up -d
        print_success "Updated"
        ;;
    "help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  deploy        - Deploy the application (default)"
        echo "  ssl           - Setup SSL certificates"
        echo "  status        - Show deployment status"
        echo "  logs          - Show application logs"
        echo "  stop          - Stop the application"
        echo "  restart       - Restart the application"
        echo "  backup        - Start backup service"
        echo "  adminer       - Start Adminer database management (http://localhost:8080)"
        echo "  stop-adminer  - Stop Adminer service"
        echo "  setup-auth    - Setup basic auth for callbacks"
        echo "                  Usage: $0 setup-auth [username] [password]"
        echo "  update        - Update and restart the application"
        echo "  help          - Show this help message"
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for available commands"
        exit 1
        ;;
esac
