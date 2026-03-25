#!/usr/bin/env bash
#
# CLERK Setup Script
# One-command setup for all dependencies
#
# Usage: ./scripts/setup.sh [options]
#
# Options:
#   --help, -h       Show this help message
#   --skip-db        Skip database setup
#   --skip-env       Skip copying .env.example to .env
#
# This script checks for required tools and installs all dependencies.
# Target: Under 5 minutes setup time

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Flags
SKIP_DB=false
SKIP_ENV=false

# Help message
show_help() {
    cat << 'EOF'
CLERK Setup Script
==================
One-command setup for all dependencies.

Usage: ./scripts/setup.sh [options]

Options:
  --help, -h       Show this help message
  --skip-db        Skip database setup
  --skip-env       Skip copying .env.example to .env

Prerequisites:
  - Python 3.13+
  - Node.js 20+
  - UV (Python package manager)

The script will:
  1. Check for required tools
  2. Install Python dependencies (uv sync)
  3. Install frontend dependencies (npm install)
  4. Copy .env.example to .env (if not exists)
  5. Run database setup (clerk db setup)

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --skip-db)
            SKIP_DB=true
            shift
            ;;
        --skip-env)
            SKIP_ENV=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Get Python version
get_python_version() {
    python3 --version 2>/dev/null | awk '{print $2}' | cut -d. -f1,2
}

# Check Python version is at least 3.13
check_python_version() {
    local version
    version=$(get_python_version)
    local major=$(echo "$version" | cut -d. -f1)
    local minor=$(echo "$version" | cut -d. -f2)
    
    if [[ "$major" -lt 3 ]] || [[ "$major" -eq 3 && "$minor" -lt 13 ]]; then
        return 1
    fi
    return 0
}

# Get Node version
get_node_version() {
    node --version 2>/dev/null | sed 's/v//' | cut -d. -f1
}

# Check Node version is at least 20
check_node_version() {
    local version
    version=$(get_node_version)
    if [[ "$version" -lt 20 ]]; then
        return 1
    fi
    return 0
}

# ============================================
# Main Setup
# ============================================

echo ""
echo "========================================"
echo "  CLERK Setup"
echo "  One-command dependency installation"
echo "========================================"
echo ""

# Check prerequisites
log_info "Checking prerequisites..."

# Check Python
if ! command_exists python3; then
    log_error "Python 3 is not installed. Please install Python 3.13 or later."
    log_info "Visit: https://www.python.org/downloads/"
    exit 1
fi

if ! check_python_version; then
    local version
    version=$(get_python_version)
    log_error "Python 3.13+ is required. Found: $version"
    log_info "Please upgrade Python: https://www.python.org/downloads/"
    exit 1
fi
log_success "Python $(get_python_version) found"

# Check Node.js
if ! command_exists node; then
    log_error "Node.js is not installed. Please install Node.js 20 or later."
    log_info "Visit: https://nodejs.org/"
    exit 1
fi

if ! check_node_version; then
    local version
    version=$(get_node_version)
    log_error "Node.js 20+ is required. Found: $version"
    log_info "Please upgrade Node.js: https://nodejs.org/"
    exit 1
fi
log_success "Node.js $(node --version | sed 's/v//') found"

# Check UV
if ! command_exists uv; then
    log_warning "UV is not installed. Attempting to install..."
    
    # Try to install UV
    if command_exists curl; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
    elif command_exists wget; then
        wget -qO- https://astral.sh/uv/install.sh | sh
    else
        log_error "Cannot install UV. Please install manually:"
        log_info "  curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    
    # Source the cargo environment if it exists
    if [[ -f "$HOME/.cargo/env" ]]; then
        source "$HOME/.cargo/env"
    fi
    
    if ! command_exists uv; then
        log_error "UV installation failed. Please install manually."
        exit 1
    fi
    log_success "UV installed successfully"
else
    log_success "UV $(uv --version | awk '{print $2}') found"
fi

# ============================================
# Install Python Dependencies
# ============================================

echo ""
log_info "Installing Python dependencies..."
cd "$PROJECT_ROOT/packages/clerk"

if uv sync; then
    log_success "Python dependencies installed"
else
    log_error "Failed to install Python dependencies"
    exit 1
fi

# ============================================
# Install Frontend Dependencies
# ============================================

echo ""
log_info "Installing frontend dependencies..."
cd "$PROJECT_ROOT/apps/website"

if npm install; then
    log_success "Frontend dependencies installed"
else
    log_error "Failed to install frontend dependencies"
    exit 1
fi

# ============================================
# Copy .env.example to .env
# ============================================

echo ""
if [[ "$SKIP_ENV" == false ]]; then
    cd "$PROJECT_ROOT"
    if [[ -f ".env" ]]; then
        log_warning ".env already exists. Skipping copy."
    else
        log_info "Creating .env from .env.example..."
        cp .env.example .env
        log_success ".env created"
        log_warning "IMPORTANT: Please edit .env and add your API keys!"
    fi
else
    log_info "Skipping .env creation (--skip-env)"
fi

# ============================================
# Database Setup
# ============================================

echo ""
if [[ "$SKIP_DB" == false ]]; then
    log_info "Setting up database..."
    cd "$PROJECT_ROOT/packages/clerk"
    
    if uv run clerk db setup; then
        log_success "Database setup complete"
    else
        log_warning "Database setup failed (this is OK if you don't have DB configured yet)"
        log_info "You can run 'clerk db setup' later after configuring .env"
    fi
else
    log_info "Skipping database setup (--skip-db)"
fi

# ============================================
# Success
# ============================================

echo ""
echo "========================================"
echo -e "${GREEN}  Setup Complete!${NC}"
echo "========================================"
echo ""
echo "Next steps:"
echo ""
echo "  1. Edit .env and add your API keys:"
echo "     - OPENAI_API_KEY (required)"
echo "     - SUPABASE credentials (optional)"
echo ""
echo "  2. Start the development server:"
echo "     npm run dev"
echo ""
echo "  3. Or start backend and frontend separately:"
echo "     cd packages/clerk && uv run clerk web --port 8000"
echo "     cd apps/website && npm run dev"
echo ""
echo "Documentation:"
echo "  - README.md"
echo "  - CONTRIBUTING.md"
echo ""
