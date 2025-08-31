#!/bin/bash

# Server Requirements Check Script
# Run this on your server before deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() { echo -e "${BLUE}[CHECK]${NC} $1"; }
print_success() { echo -e "${GREEN}[PASS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[FAIL]${NC} $1"; }

echo "🔍 Money Manager Server Requirements Check"
echo "========================================"
echo ""

# Check OS
print_status "Checking operating system..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_VERSION=$(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)
    print_success "Linux detected: $OS_VERSION"
else
    print_error "Linux required. Detected: $OSTYPE"
    exit 1
fi

# Check Docker
print_status "Checking Docker installation..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    print_success "Docker installed: $DOCKER_VERSION"
    
    # Check Docker daemon
    if docker ps &> /dev/null; then
        print_success "Docker daemon is running"
    else
        print_error "Docker daemon is not running or user lacks permissions"
        echo "Try: sudo usermod -aG docker \$USER && newgrp docker"
    fi
else
    print_error "Docker not installed"
    echo "Install: curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
fi

# Check Docker Compose
print_status "Checking Docker Compose..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
    print_success "Docker Compose installed: $COMPOSE_VERSION"
else
    print_error "Docker Compose not installed"
    echo 'Install: sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose'
    echo "chmod: sudo chmod +x /usr/local/bin/docker-compose"
fi

# Check ports
print_status "Checking required ports..."
for port in 80 443; do
    if ss -tlnp | grep ":$port " > /dev/null; then
        print_warning "Port $port is in use"
        ss -tlnp | grep ":$port "
    else
        print_success "Port $port is available"
    fi
done

# Check disk space
print_status "Checking disk space..."
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -lt 80 ]; then
    print_success "Disk space: ${DISK_USAGE}% used"
else
    print_warning "Disk space: ${DISK_USAGE}% used (consider cleanup)"
fi

# Check memory
print_status "Checking memory..."
MEMORY_GB=$(free -g | awk 'NR==2{printf "%.1f", $2}')
if (( $(echo "$MEMORY_GB >= 1" | bc -l) )); then
    print_success "Memory: ${MEMORY_GB}GB available"
else
    print_warning "Memory: ${MEMORY_GB}GB (minimum 1GB recommended)"
fi

# Check curl
print_status "Checking curl..."
if command -v curl &> /dev/null; then
    print_success "curl is installed"
else
    print_error "curl not installed (required for health checks)"
    echo "Install: sudo apt update && sudo apt install curl"
fi

# Check firewall
print_status "Checking firewall..."
if command -v ufw &> /dev/null; then
    UFW_STATUS=$(ufw status | head -1 | cut -d' ' -f2)
    if [ "$UFW_STATUS" = "active" ]; then
        print_success "UFW firewall is active"
        print_status "Checking firewall rules..."
        
        if ufw status | grep -q "80/tcp"; then
            print_success "HTTP (80) allowed"
        else
            print_warning "HTTP (80) not explicitly allowed"
        fi
        
        if ufw status | grep -q "443/tcp"; then
            print_success "HTTPS (443) allowed"
        else
            print_warning "HTTPS (443) not explicitly allowed"
        fi
    else
        print_warning "UFW firewall is inactive"
    fi
else
    print_warning "UFW not installed (firewall management recommended)"
fi

# Check systemctl
print_status "Checking systemd..."
if command -v systemctl &> /dev/null; then
    print_success "systemd available"
else
    print_warning "systemd not available (some features may not work)"
fi

echo ""
echo "📋 Server Requirements Summary"
echo "=============================="
echo "✅ Required for basic deployment:"
echo "   - Linux OS"
echo "   - Docker + Docker Compose" 
echo "   - Ports 80 and 443 available"
echo "   - Minimum 1GB RAM"
echo "   - curl for health checks"
echo ""
echo "🔧 Recommended for production:"
echo "   - UFW firewall configured"
echo "   - systemd for service management"
echo "   - Regular security updates"
echo "   - Monitoring and backup strategy"
echo ""
echo "🚀 Next Steps:"
echo "   1. Fix any failed requirements above"
echo "   2. Copy your Money Manager code to this server"
echo "   3. Run: ./deploy.sh deploy"
echo ""

# Final status
if docker --version &> /dev/null && docker-compose --version &> /dev/null; then
    print_success "Server is ready for Money Manager deployment!"
    exit 0
else
    print_error "Please install missing requirements before deployment"
    exit 1
fi
