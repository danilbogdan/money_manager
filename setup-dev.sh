#!/bin/bash

# Development Setup Script with UV Package Manager
# This script sets up the development environment using UV

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "🚀 Money Manager - Development Setup with UV"
echo "============================================"
echo ""

# Check if UV is installed
check_uv() {
    print_status "Checking UV installation..."
    if command -v uv &> /dev/null; then
        UV_VERSION=$(uv --version)
        print_success "UV is installed: $UV_VERSION"
        return 0
    else
        print_warning "UV not found. Installing UV..."
        return 1
    fi
}

# Install UV
install_uv() {
    print_status "Installing UV package manager..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
        # Source the shell configuration to get uv in PATH
        export PATH="$HOME/.cargo/bin:$PATH"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        print_error "Please install UV manually on Windows: https://github.com/astral-sh/uv#installation"
        exit 1
    else
        print_error "Unsupported OS: $OSTYPE"
        exit 1
    fi
    
    # Verify installation
    if command -v uv &> /dev/null; then
        print_success "UV installed successfully!"
    else
        print_error "UV installation failed. Please install manually."
        exit 1
    fi
}

# Setup Python environment
setup_environment() {
    print_status "Setting up Python environment..."
    
    # Check if we're in a virtual environment or should create one
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        print_success "Already in virtual environment: $VIRTUAL_ENV"
    else
        print_status "Creating virtual environment..."
        uv venv
        
        # Activate virtual environment
        if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
            source .venv/Scripts/activate
        else
            source .venv/bin/activate
        fi
        print_success "Virtual environment created and activated"
    fi
}

# Install dependencies
install_dependencies() {
    print_status "Installing project dependencies..."
    
    # Install production dependencies
    uv pip install -e .
    
    # Install development dependencies
    print_status "Installing development dependencies..."
    uv pip install -e ".[dev]"
    
    print_success "Dependencies installed successfully!"
}

# Setup pre-commit hooks
setup_pre_commit() {
    print_status "Setting up pre-commit hooks..."
    
    if command -v pre-commit &> /dev/null; then
        pre-commit install
        print_success "Pre-commit hooks installed"
    else
        print_warning "pre-commit not available, skipping hooks setup"
    fi
}

# Create development environment file
setup_env_file() {
    print_status "Setting up environment file..."
    
    if [ ! -f ".env" ]; then
        cp env.production.template .env
        print_success "Environment file created from template"
        print_warning "Please edit .env file with your actual configuration"
        echo ""
        echo "Required configuration:"
        echo "  - SALTEDGE_APP_ID"
        echo "  - SALTEDGE_SECRET_KEY"
        echo "  - SALTEDGE_CLIENT_ID"
        echo ""
    else
        print_success "Environment file already exists"
    fi
}

# Run initial tests
run_tests() {
    print_status "Running initial tests..."
    
    # Create tests directory if it doesn't exist
    mkdir -p tests
    
    # Run tests if they exist
    if [ -d "tests" ] && [ "$(ls -A tests)" ]; then
        uv run pytest tests/ -v
        print_success "Tests completed"
    else
        print_warning "No tests found, skipping test run"
    fi
}

# Show next steps
show_next_steps() {
    echo ""
    print_success "Development environment setup complete! 🎉"
    echo ""
    echo "📋 Next steps:"
    echo ""
    echo "1. Edit your environment configuration:"
    echo "   nano .env"
    echo ""
    echo "2. Start the development server:"
    echo "   uv run uvicorn main:app --reload --port 8000"
    echo ""
    echo "3. Access the application:"
    echo "   🌐 App: http://localhost:8000"
    echo "   📚 Docs: http://localhost:8000/docs"
    echo ""
    echo "4. Available UV commands:"
    echo "   uv run pytest                    # Run tests"
    echo "   uv run black .                   # Format code"
    echo "   uv run ruff check .              # Lint code"
    echo "   uv run mypy .                    # Type checking"
    echo "   uv add <package>                 # Add new dependency"
    echo "   uv remove <package>              # Remove dependency"
    echo "   uv lock                          # Update lockfile"
    echo ""
    echo "5. For local callback testing:"
    echo "   python setup_ngrok.py           # Setup ngrok for webhooks"
    echo ""
    echo "6. Docker development:"
    echo "   docker-compose -f docker-compose.dev.yml up -d"
    echo ""
    print_status "Happy coding! 🚀"
}

# Main setup process
main() {
    # Check and install UV if needed
    if ! check_uv; then
        install_uv
    fi
    
    # Setup environment and dependencies
    setup_environment
    install_dependencies
    
    # Setup development tools
    setup_pre_commit
    setup_env_file
    
    # Optional: run tests
    echo ""
    echo -e "${YELLOW}Run initial tests? (y/n):${NC} "
    read -r run_tests_response
    if [[ "$run_tests_response" =~ ^[Yy]$ ]]; then
        run_tests
    fi
    
    # Show next steps
    show_next_steps
}

# Handle command line arguments
case "${1:-setup}" in
    "setup")
        main
        ;;
    "install-uv")
        install_uv
        ;;
    "sync")
        print_status "Syncing dependencies..."
        uv pip install -e ".[dev]"
        uv lock
        print_success "Dependencies synced"
        ;;
    "clean")
        print_status "Cleaning up development environment..."
        rm -rf .venv __pycache__ .pytest_cache .mypy_cache .ruff_cache
        find . -name "*.pyc" -delete
        print_success "Environment cleaned"
        ;;
    "test")
        uv run pytest tests/ -v
        ;;
    "format")
        print_status "Formatting code..."
        uv run black .
        uv run ruff check . --fix
        print_success "Code formatted"
        ;;
    "type-check")
        uv run mypy .
        ;;
    "lint")
        uv run ruff check .
        ;;
    "help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  setup      - Full development setup (default)"
        echo "  install-uv - Install UV package manager only"
        echo "  sync       - Sync dependencies and update lockfile"
        echo "  clean      - Clean development environment"
        echo "  test       - Run tests"
        echo "  format     - Format code with black and ruff"
        echo "  type-check - Run type checking with mypy"
        echo "  lint       - Run linting with ruff"
        echo "  help       - Show this help message"
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for available commands"
        exit 1
        ;;
esac
