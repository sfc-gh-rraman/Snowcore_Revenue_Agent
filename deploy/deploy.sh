#!/bin/bash
# =============================================================================
# GRANITE Vulcan Revenue Intelligence - SPCS Deployment Script
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
IMAGE_NAME="granite"
IMAGE_TAG="latest"

DATABASE="VULCAN_MATERIALS_DB"
SCHEMA="ML"
IMAGE_REPO="IMAGES"
COMPUTE_POOL="GRANITE_COMPUTE_POOL"
SERVICE_NAME="GRANITE_SERVICE"
CONNECTION="${SNOWFLAKE_CONNECTION:-my_snowflake}"

REGISTRY_URL=""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

setup_spcs() {
    log_info "Setting up SPCS infrastructure..."
    
    snow sql -c $CONNECTION -q "
    CREATE COMPUTE POOL IF NOT EXISTS $COMPUTE_POOL
    MIN_NODES = 1
    MAX_NODES = 1
    INSTANCE_FAMILY = CPU_X64_XS
    AUTO_RESUME = TRUE
    AUTO_SUSPEND_SECS = 3600;
    " 2>/dev/null || log_warning "Compute pool may already exist"
    
    log_success "SPCS infrastructure setup complete!"
}

get_registry_url() {
    log_info "Getting Snowflake registry URL..."
    REGISTRY_URL=$(snow sql -c $CONNECTION -q "SHOW IMAGE REPOSITORIES LIKE '$IMAGE_REPO' IN SCHEMA $DATABASE.$SCHEMA" --format JSON 2>/dev/null | \
        python3 -c "import sys, json; data = json.load(sys.stdin); print(data[0]['repository_url'])" 2>/dev/null)
    
    if [ -z "$REGISTRY_URL" ]; then
        log_error "Failed to get registry URL."
        exit 1
    fi
    
    log_info "Registry URL: $REGISTRY_URL"
}

build_image() {
    log_info "Building Docker image..."
    cd "$PROJECT_DIR"
    
    echo -e "${CYAN}"
    echo "  ██████╗ ██████╗  █████╗ ███╗   ██╗██╗████████╗███████╗"
    echo " ██╔════╝ ██╔══██╗██╔══██╗████╗  ██║██║╚══██╔══╝██╔════╝"
    echo " ██║  ███╗██████╔╝███████║██╔██╗ ██║██║   ██║   █████╗  "
    echo " ██║   ██║██╔══██╗██╔══██║██║╚██╗██║██║   ██║   ██╔══╝  "
    echo " ╚██████╔╝██║  ██║██║  ██║██║ ╚████║██║   ██║   ███████╗"
    echo "  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝   ╚═╝   ╚══════╝"
    echo " Vulcan Revenue Intelligence"
    echo -e "${NC}"
    
    docker build \
        --platform linux/amd64 \
        -f deploy/Dockerfile \
        -t "${IMAGE_NAME}:${IMAGE_TAG}" \
        .
    
    log_success "Docker image built: ${IMAGE_NAME}:${IMAGE_TAG}"
}

push_image() {
    get_registry_url
    
    log_info "Logging into Snowflake registry..."
    snow spcs image-registry login -c $CONNECTION
    
    log_info "Tagging image for Snowflake registry..."
    FULL_IMAGE_URL="${REGISTRY_URL}/${IMAGE_NAME}:${IMAGE_TAG}"
    docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "$FULL_IMAGE_URL"
    
    log_info "Pushing image to Snowflake registry..."
    docker push "$FULL_IMAGE_URL"
    
    log_success "Image pushed: $FULL_IMAGE_URL"
}

deploy_service() {
    get_registry_url
    FULL_IMAGE_URL="${REGISTRY_URL}/${IMAGE_NAME}:${IMAGE_TAG}"
    
    log_info "Checking compute pool status..."
    POOL_STATUS=$(snow sql -c $CONNECTION -q "DESCRIBE COMPUTE POOL $COMPUTE_POOL" --format JSON 2>/dev/null | \
        python3 -c "import sys, json; data = json.load(sys.stdin); print(data[0].get('state', 'UNKNOWN'))" 2>/dev/null || echo "UNKNOWN")
    
    log_info "Compute pool status: $POOL_STATUS"
    
    if [ "$POOL_STATUS" == "SUSPENDED" ]; then
        log_info "Resuming compute pool..."
        snow sql -c $CONNECTION -q "ALTER COMPUTE POOL $COMPUTE_POOL RESUME"
        log_info "Waiting for compute pool to become active..."
        sleep 30
    fi
    
    log_info "Deploying service..."
    
    SERVICE_EXISTS=$(snow sql -c $CONNECTION -q "SHOW SERVICES LIKE '$SERVICE_NAME' IN SCHEMA $DATABASE.$SCHEMA" --format JSON 2>/dev/null | \
        python3 -c "import sys, json; data = json.load(sys.stdin); print('yes' if data else 'no')" 2>/dev/null || echo "no")
    
    if [ "$SERVICE_EXISTS" == "yes" ]; then
        log_info "Service exists. Dropping and recreating..."
        snow sql -c $CONNECTION -q "DROP SERVICE IF EXISTS $DATABASE.$SCHEMA.$SERVICE_NAME"
        sleep 5
    fi
    
    log_info "Creating new service..."
    snow sql -c $CONNECTION -q "CREATE SERVICE $DATABASE.$SCHEMA.$SERVICE_NAME
IN COMPUTE POOL $COMPUTE_POOL
FROM SPECIFICATION \$\$
spec:
  containers:
    - name: granite
      image: $FULL_IMAGE_URL
      env:
        SNOWFLAKE_DATABASE: $DATABASE
        SNOWFLAKE_SCHEMA: ML
        LOG_LEVEL: INFO
      resources:
        requests:
          memory: 2Gi
          cpu: 1
        limits:
          memory: 4Gi
          cpu: 2
      readinessProbe:
        port: 8080
        path: /health
  endpoints:
    - name: granite-endpoint
      port: 8080
      public: true
\$\$
MIN_INSTANCES = 1
MAX_INSTANCES = 1"
    
    log_success "Service deployed!"
    
    log_info "Waiting for service to be ready..."
    sleep 15
    get_status
}

get_status() {
    log_info "Checking service status..."
    
    snow sql -c $CONNECTION -q "DESCRIBE SERVICE $DATABASE.$SCHEMA.$SERVICE_NAME" 2>/dev/null || {
        log_error "Service not found"
        return 1
    }
    
    echo ""
    log_info "Service endpoints:"
    snow sql -c $CONNECTION -q "SHOW ENDPOINTS IN SERVICE $DATABASE.$SCHEMA.$SERVICE_NAME" 2>/dev/null
    
    ENDPOINT_URL=$(snow sql -c $CONNECTION -q "SHOW ENDPOINTS IN SERVICE $DATABASE.$SCHEMA.$SERVICE_NAME" --format JSON 2>/dev/null | \
        python3 -c "import sys, json; data = json.load(sys.stdin); print(data[0].get('ingress_url', 'Not available yet'))" 2>/dev/null || echo "Not available yet")
    
    echo ""
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}  GRANITE Vulcan Revenue Intelligence${NC}"
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${CYAN}  Endpoint URL: ${NC}$ENDPOINT_URL"
    echo -e "${GREEN}=========================================${NC}"
}

view_logs() {
    log_info "Fetching service logs..."
    snow sql -c $CONNECTION -q "CALL SYSTEM\$GET_SERVICE_LOGS('$DATABASE.$SCHEMA.$SERVICE_NAME', 0, 'granite', 100)"
}

stop_service() {
    log_info "Stopping service..."
    snow sql -c $CONNECTION -q "ALTER SERVICE $DATABASE.$SCHEMA.$SERVICE_NAME SUSPEND" 2>/dev/null || {
        log_warning "Service might not exist or already stopped"
    }
    log_success "Service stopped"
}

case "${1:-all}" in
    setup)
        setup_spcs
        ;;
    build)
        build_image
        ;;
    push)
        push_image
        ;;
    deploy)
        deploy_service
        ;;
    logs)
        view_logs
        ;;
    status)
        get_status
        ;;
    stop)
        stop_service
        ;;
    all)
        build_image
        push_image
        deploy_service
        ;;
    *)
        echo "Usage: $0 {setup|build|push|deploy|logs|status|stop|all}"
        exit 1
        ;;
esac
