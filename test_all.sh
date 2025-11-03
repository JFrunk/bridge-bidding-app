#!/bin/bash
# Comprehensive test script - runs all tests before commit
# Usage: ./test_all.sh [--quick|--skip-e2e]

set -e  # Exit on first failure

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
QUICK_MODE=false
SKIP_E2E=false
START_SERVERS=true

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --quick)
      QUICK_MODE=true
      shift
      ;;
    --skip-e2e)
      SKIP_E2E=true
      shift
      ;;
    --no-servers)
      START_SERVERS=false
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: ./test_all.sh [--quick] [--skip-e2e] [--no-servers]"
      exit 1
      ;;
  esac
done

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Bridge Bidding App - Test Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to check if port is in use
port_in_use() {
  lsof -ti:$1 > /dev/null 2>&1
}

# Function to start servers if needed
start_servers() {
  if [ "$START_SERVERS" = false ]; then
    echo -e "${YELLOW}⚠️  Skipping server startup (--no-servers)${NC}"
    return
  fi

  echo -e "${BLUE}Starting servers...${NC}"

  # Check if backend is already running
  if port_in_use 5001; then
    echo -e "${GREEN}✓ Backend already running on port 5001${NC}"
  else
    echo "  Starting backend server..."
    cd backend
    source venv/bin/activate
    python server.py > /tmp/test-backend.log 2>&1 &
    BACKEND_PID=$!
    cd ..
    sleep 3
    echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
  fi

  # Check if frontend is already running
  if port_in_use 3000; then
    echo -e "${GREEN}✓ Frontend already running on port 3000${NC}"
  else
    echo "  Starting frontend server..."
    cd frontend
    npm start > /tmp/test-frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    sleep 8
    echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
  fi

  echo ""
}

# Function to cleanup servers
cleanup_servers() {
  if [ "$START_SERVERS" = true ] && [ ! -z "$BACKEND_PID" ]; then
    echo -e "${BLUE}Cleaning up servers...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
      kill $BACKEND_PID 2>/dev/null || true
      echo "  Backend stopped"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
      kill $FRONTEND_PID 2>/dev/null || true
      echo "  Frontend stopped"
    fi
  fi
}

# Set trap to cleanup on exit
trap cleanup_servers EXIT INT TERM

# Track test results
BACKEND_TESTS_PASSED=false
FRONTEND_TESTS_PASSED=false
E2E_TESTS_PASSED=false

# ============================================
# 1. Backend Tests
# ============================================
echo -e "${BLUE}[1/3] Running Backend Tests${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd backend

if [ "$QUICK_MODE" = true ]; then
  echo "Running quick tests (unit only)..."
  ./test_quick.sh
else
  echo "Running full backend test suite..."
  ./test_full.sh
fi

BACKEND_EXIT_CODE=$?
cd ..

if [ $BACKEND_EXIT_CODE -eq 0 ]; then
  echo -e "${GREEN}✓ Backend tests PASSED${NC}"
  BACKEND_TESTS_PASSED=true
else
  echo -e "${RED}✗ Backend tests FAILED${NC}"
  echo -e "${RED}Fix backend tests before committing!${NC}"
  exit 1
fi

echo ""

# ============================================
# 2. Frontend Tests (Jest/React Testing Library)
# ============================================
echo -e "${BLUE}[2/3] Running Frontend Unit Tests${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd frontend
CI=true npm test -- --watchAll=false --passWithNoTests
FRONTEND_EXIT_CODE=$?
cd ..

if [ $FRONTEND_EXIT_CODE -eq 0 ]; then
  echo -e "${GREEN}✓ Frontend tests PASSED${NC}"
  FRONTEND_TESTS_PASSED=true
else
  echo -e "${RED}✗ Frontend tests FAILED${NC}"
  echo -e "${RED}Fix frontend tests before committing!${NC}"
  exit 1
fi

echo ""

# ============================================
# 3. E2E Tests (Playwright)
# ============================================
if [ "$SKIP_E2E" = true ]; then
  echo -e "${YELLOW}[3/3] E2E Tests - SKIPPED${NC}"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo -e "${YELLOW}⚠️  Skipping E2E tests (--skip-e2e flag)${NC}"
  E2E_TESTS_PASSED=true
else
  echo -e "${BLUE}[3/3] Running E2E Tests (Playwright)${NC}"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # Start servers if needed
  start_servers

  # Wait for servers to be ready
  echo "Waiting for servers to be ready..."
  sleep 2

  # Run E2E tests
  cd frontend
  npx playwright test --reporter=line
  E2E_EXIT_CODE=$?
  cd ..

  if [ $E2E_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ E2E tests PASSED${NC}"
    E2E_TESTS_PASSED=true
  else
    echo -e "${RED}✗ E2E tests FAILED${NC}"
    echo -e "${YELLOW}Tip: Run 'npm run test:e2e:ui' in frontend/ for interactive debugging${NC}"
    exit 1
  fi
fi

echo ""

# ============================================
# Summary
# ============================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ "$BACKEND_TESTS_PASSED" = true ]; then
  echo -e "${GREEN}✓ Backend Tests:  PASSED${NC}"
else
  echo -e "${RED}✗ Backend Tests:  FAILED${NC}"
fi

if [ "$FRONTEND_TESTS_PASSED" = true ]; then
  echo -e "${GREEN}✓ Frontend Tests: PASSED${NC}"
else
  echo -e "${RED}✗ Frontend Tests: FAILED${NC}"
fi

if [ "$E2E_TESTS_PASSED" = true ]; then
  if [ "$SKIP_E2E" = true ]; then
    echo -e "${YELLOW}⚠ E2E Tests:      SKIPPED${NC}"
  else
    echo -e "${GREEN}✓ E2E Tests:      PASSED${NC}"
  fi
else
  echo -e "${RED}✗ E2E Tests:      FAILED${NC}"
fi

echo ""

if [ "$BACKEND_TESTS_PASSED" = true ] && [ "$FRONTEND_TESTS_PASSED" = true ] && [ "$E2E_TESTS_PASSED" = true ]; then
  echo -e "${GREEN}========================================${NC}"
  echo -e "${GREEN}  ALL TESTS PASSED! ✓${NC}"
  echo -e "${GREEN}  Safe to commit.${NC}"
  echo -e "${GREEN}========================================${NC}"
  exit 0
else
  echo -e "${RED}========================================${NC}"
  echo -e "${RED}  TESTS FAILED! ✗${NC}"
  echo -e "${RED}  Do not commit until tests pass.${NC}"
  echo -e "${RED}========================================${NC}"
  exit 1
fi
