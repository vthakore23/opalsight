#!/bin/bash

# OpalSight Production Deployment Script
# Usage: ./deploy.sh [environment]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-production}
DOCKER_COMPOSE_FILE="docker-compose.prod.yml"
BACKUP_DIR="./backups"
LOG_DIR="./logs"

echo -e "${GREEN}OpalSight Deployment Script${NC}"
echo -e "Environment: ${YELLOW}$ENVIRONMENT${NC}"
echo "================================"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

if ! command_exists docker; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command_exists docker-compose; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites met${NC}"

# Create necessary directories
echo -e "\n${YELLOW}Creating directories...${NC}"
mkdir -p $BACKUP_DIR $LOG_DIR ./backend/logs ./nginx/ssl
echo -e "${GREEN}✓ Directories created${NC}"

# Check for .env file
if [ ! -f .env ]; then
    echo -e "\n${RED}Error: .env file not found${NC}"
    echo "Please create a .env file with the required environment variables"
    echo "You can use .env.example as a template"
    exit 1
fi

# Load environment variables
set -a
source .env
set +a

# Validate required environment variables
echo -e "\n${YELLOW}Validating environment variables...${NC}"

required_vars=("FMP_API_KEY" "DB_PASSWORD" "SECRET_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=($var)
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo -e "${RED}Error: Missing required environment variables:${NC}"
    printf '%s\n' "${missing_vars[@]}"
    exit 1
fi

echo -e "${GREEN}✓ Environment variables validated${NC}"

# Backup existing database (if running)
if docker ps | grep -q opalsight_db; then
    echo -e "\n${YELLOW}Backing up existing database...${NC}"
    timestamp=$(date +%Y%m%d_%H%M%S)
    docker exec opalsight_db pg_dump -U opalsight opalsight > "$BACKUP_DIR/pre_deploy_$timestamp.sql"
    echo -e "${GREEN}✓ Database backed up to $BACKUP_DIR/pre_deploy_$timestamp.sql${NC}"
fi

# Build and deploy
echo -e "\n${YELLOW}Building and deploying services...${NC}"

# Pull latest images
docker-compose -f $DOCKER_COMPOSE_FILE pull

# Build custom images
docker-compose -f $DOCKER_COMPOSE_FILE build --no-cache

# Stop existing services
docker-compose -f $DOCKER_COMPOSE_FILE down

# Start services
docker-compose -f $DOCKER_COMPOSE_FILE up -d

# Wait for services to be healthy
echo -e "\n${YELLOW}Waiting for services to be healthy...${NC}"

services=("opalsight_db_prod" "opalsight_redis_prod" "opalsight_backend_prod")
max_attempts=30

for service in "${services[@]}"; do
    echo -n "Checking $service..."
    attempts=0
    while [ $attempts -lt $max_attempts ]; do
        if docker ps --filter "name=$service" --filter "health=healthy" | grep -q $service; then
            echo -e " ${GREEN}✓${NC}"
            break
        fi
        attempts=$((attempts + 1))
        sleep 2
        echo -n "."
    done
    
    if [ $attempts -eq $max_attempts ]; then
        echo -e " ${RED}✗${NC}"
        echo -e "${RED}Error: $service failed to become healthy${NC}"
        docker logs $service --tail 50
        exit 1
    fi
done

# Run database migrations
echo -e "\n${YELLOW}Running database migrations...${NC}"
docker exec opalsight_backend_prod flask db upgrade
echo -e "${GREEN}✓ Migrations completed${NC}"

# Add performance indexes
echo -e "\n${YELLOW}Adding performance indexes...${NC}"
docker exec opalsight_backend_prod python migrations/add_performance_indexes.py
echo -e "${GREEN}✓ Indexes created${NC}"

# Verify deployment
echo -e "\n${YELLOW}Verifying deployment...${NC}"

# Check API health
if curl -f -s http://localhost:5000/api/health > /dev/null; then
    echo -e "${GREEN}✓ API is healthy${NC}"
else
    echo -e "${RED}✗ API health check failed${NC}"
    docker logs opalsight_backend_prod --tail 50
    exit 1
fi

# Check frontend
if curl -f -s http://localhost > /dev/null; then
    echo -e "${GREEN}✓ Frontend is accessible${NC}"
else
    echo -e "${RED}✗ Frontend is not accessible${NC}"
    docker logs opalsight_frontend_prod --tail 50
fi

# Display service URLs
echo -e "\n${GREEN}Deployment completed successfully!${NC}"
echo -e "\n${YELLOW}Service URLs:${NC}"
echo "• Frontend: http://localhost"
echo "• API: http://localhost:5000"
echo "• Grafana: http://localhost:3001 (admin/${GRAFANA_PASSWORD:-admin})"
echo "• Prometheus: http://localhost:9090"

# Display useful commands
echo -e "\n${YELLOW}Useful commands:${NC}"
echo "• View logs: docker-compose -f $DOCKER_COMPOSE_FILE logs -f [service_name]"
echo "• Stop services: docker-compose -f $DOCKER_COMPOSE_FILE down"
echo "• Restart service: docker-compose -f $DOCKER_COMPOSE_FILE restart [service_name]"
echo "• Run data collection: docker exec opalsight_backend_prod python -c 'from app.services.data_collector import DataCollector; DataCollector().run_weekly_collection()'"

# Cleanup old backups (keep last 7 days)
echo -e "\n${YELLOW}Cleaning up old backups...${NC}"
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
echo -e "${GREEN}✓ Cleanup completed${NC}"

echo -e "\n${GREEN}Deployment finished!${NC}" 