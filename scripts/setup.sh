#!/bin/bash

# ============================================
# HR-RAG Setup Script
# ============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       HR-RAG Setup Script v1.0         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Determine docker-compose command
DOCKER_COMPOSE="docker-compose"
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
fi

# Function to prompt for user input
prompt() {
    local prompt_text=$1
    local default_value=$2
    local var_name=$3
    
    if [ -n "$default_value" ]; then
        read -p "$prompt_text [$default_value]: " input
        input=${input:-$default_value}
    else
        read -p "$prompt_text: " input
    fi
    
    export "$var_name=$input"
}

# Function to create .env file
create_env_file() {
    echo ""
    echo -e "${YELLOW}Setting up environment variables...${NC}"
    
    # Copy example env file
    if [ ! -f .env ]; then
        cp .env.example .env
        echo -e "${GREEN}Created .env file from .env.example${NC}"
    else
        echo -e "${YELLOW}.env file already exists, skipping...${NC}"
    fi
}

# Function to setup backend
setup_backend() {
    echo ""
    echo -e "${YELLOW}Setting up backend...${NC}"
    
    cd backend
    
    # Create virtual environment if not exists
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
        echo -e "${GREEN}Created Python virtual environment${NC}"
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Install dependencies
    pip install --upgrade pip
    pip install -r requirements.txt
    
    cd ..
    echo -e "${GREEN}Backend setup complete!${NC}"
}

# Function to setup frontend
setup_frontend() {
    echo ""
    echo -e "${YELLOW}Setting up frontend...${NC}"
    
    cd frontend
    
    # Install dependencies
    npm install
    
    cd ..
    echo -e "${GREEN}Frontend setup complete!${NC}"
}

# Function to start services
start_services() {
    echo ""
    echo -e "${YELLOW}Starting Docker services...${NC}"
    
    $DOCKER_COMPOSE up -d
    
    echo ""
    echo -e "${GREEN}Services started!${NC}"
    echo ""
    echo "Services:"
    echo "  - Frontend (Next.js): http://localhost:3000"
    echo "  - Backend (FastAPI):  http://localhost:8000"
    echo "  - Qdrant:             http://localhost:6333"
    echo "  - Redis:              http://localhost:6379"
    echo "  - TiDB (local):       http://localhost:4000"
    echo ""
    echo "API Documentation: http://localhost:8000/docs"
}

# Function to initialize database
init_database() {
    echo ""
    echo -e "${YELLOW}Initializing database...${NC}"
    
    # Wait for TiDB to be ready
    echo "Waiting for TiDB to be ready..."
    sleep 5
    
    # Run migrations and seed data
    $DOCKER_COMPOSE exec -T tidb mysql -h 127.0.0.1 -P 4000 -u root -e "CREATE DATABASE IF NOT EXISTS hr_rag;"
    
    # Note: In production with TiDB Cloud, use:
    # mysql -h ${TIDB_HOST} -P ${TIDB_PORT} -u ${TIDB_USER} -p${TIDB_PASSWORD} hr_rag < database/schema.sql
    
    echo -e "${GREEN}Database initialized!${NC}"
}

# Main menu
show_menu() {
    echo ""
    echo "Select an option:"
    echo "  1) Full setup (create env + install deps + start services)"
    echo "  2) Create .env file only"
    echo "  3) Start services only"
    echo "  4) Stop services"
    echo "  5) View logs"
    echo "  6) Reset everything"
    echo "  7) Exit"
    echo ""
    read -p "Enter option [1-7]: " option
    
    case $option in
        1)
            create_env_file
            setup_backend
            setup_frontend
            start_services
            init_database
            ;;
        2)
            create_env_file
            ;;
        3)
            start_services
            ;;
        4)
            echo -e "${YELLOW}Stopping services...${NC}"
            $DOCKER_COMPOSE down
            echo -e "${GREEN}Services stopped!${NC}"
            ;;
        5)
            $DOCKER_COMPOSE logs -f
            ;;
        6)
            echo -e "${YELLOW}Resetting everything...${NC}"
            $DOCKER_COMPOSE down -v
            rm -f .env
            echo -e "${GREEN}Reset complete!${NC}"
            ;;
        7)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option${NC}"
            show_menu
            ;;
    esac
}

# Run menu
show_menu
