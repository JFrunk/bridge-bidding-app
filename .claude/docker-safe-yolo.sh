#!/bin/bash
# Secure Docker configuration for Claude Code Safe YOLO mode
#
# This script runs Claude Code in a Docker container with security restrictions:
# - No internet access (--network none)
# - Read-only project mount
# - Resource limits (CPU, memory)
# - No privilege escalation
# - Isolated from host system
#
# Usage: ./.claude/docker-safe-yolo.sh [task description]
# Example: ./.claude/docker-safe-yolo.sh "Fix all lint errors in backend/"

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_NAME="claude-code-safe-yolo"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_NAME="anthropics/claude-code:latest"
CPU_LIMIT="2.0"
MEMORY_LIMIT="4g"

echo -e "${BLUE}=== Claude Code Safe YOLO Mode ===${NC}"
echo -e "${BLUE}Security Configuration:${NC}"
echo -e "  ${GREEN}✓${NC} Network: Isolated (no internet access)"
echo -e "  ${GREEN}✓${NC} File System: Read-only project mount"
echo -e "  ${GREEN}✓${NC} Resources: Limited to ${CPU_LIMIT} CPUs, ${MEMORY_LIMIT} RAM"
echo -e "  ${GREEN}✓${NC} Privileges: Disabled"
echo ""

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    echo "Please start Docker Desktop and try again"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker is running"

# Check if container already exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${YELLOW}⚠${NC}  Container '${CONTAINER_NAME}' already exists"
    echo -e "   Removing old container..."
    docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1
fi

# Check if image exists, pull if not
if ! docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠${NC}  Image '${IMAGE_NAME}' not found"
    echo -e "   Pulling image... (this may take a few minutes)"
    docker pull "${IMAGE_NAME}"
else
    echo -e "${GREEN}✓${NC} Image '${IMAGE_NAME}' found"
fi

# Get task from arguments or prompt
TASK="$*"
if [ -z "$TASK" ]; then
    echo ""
    echo -e "${YELLOW}What task should Claude perform?${NC}"
    echo -e "Example: Fix all lint errors in backend/"
    echo -n "> "
    read -r TASK
fi

echo ""
echo -e "${BLUE}Task:${NC} ${TASK}"
echo ""
echo -e "${YELLOW}⚠️  WARNING: Safe YOLO mode will execute commands without asking permission${NC}"
echo -e "${YELLOW}⚠️  However, it's isolated with no internet access and read-only files${NC}"
echo ""
echo -n "Continue? [y/N] "
read -r CONFIRM

if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 0
fi

echo ""
echo -e "${BLUE}Starting secure container...${NC}"

# Run Docker container with security restrictions
docker run \
    --name "${CONTAINER_NAME}" \
    --rm \
    --interactive \
    --tty \
    --network none \
    --cpus="${CPU_LIMIT}" \
    --memory="${MEMORY_LIMIT}" \
    --security-opt=no-new-privileges \
    --read-only \
    --tmpfs /tmp:rw,noexec,nosuid,size=1g \
    -v "${PROJECT_DIR}:/workspace:ro" \
    -w /workspace \
    "${IMAGE_NAME}" \
    claude --dangerously-skip-permissions -p "${TASK}"

echo ""
echo -e "${GREEN}✓${NC} Container completed and removed"
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Review the output above"
echo "  2. Check your project for changes (there shouldn't be any - read-only)"
echo "  3. If you want to apply changes, run without Docker"
