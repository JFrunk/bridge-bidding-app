#!/bin/bash

# Documentation Validation Script
# Run this script to validate all documentation in the project
# Usage: ./.claude/scripts/validate_documentation.sh

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Documentation Validation Tool${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

ERRORS=0
WARNINGS=0

# Check 1: Required documentation files exist
echo -e "${BLUE}[1/7] Checking required documentation files...${NC}"
REQUIRED_FILES=(
    ".claude/DOCUMENTATION_PRACTICES.md"
    ".claude/PROJECT_CONTEXT.md"
    "docs/DOCUMENTATION_CHECKLIST.md"
    "CONTRIBUTING.md"
    "README.md"
    "docs/README.md"
    "docs/project-overview/DOCUMENTATION_INDEX.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}  ❌ Missing: $file${NC}"
        ((ERRORS++))
    else
        echo -e "${GREEN}  ✓ Found: $file${NC}"
    fi
done

# Check 2: Documentation directory structure
echo ""
echo -e "${BLUE}[2/7] Checking documentation directory structure...${NC}"
REQUIRED_DIRS=(
    "docs/architecture"
    "docs/bug-fixes"
    "docs/development-phases"
    "docs/features"
    "docs/guides"
    "docs/project-overview"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo -e "${YELLOW}  ⚠️  Missing directory: $dir${NC}"
        ((WARNINGS++))
    else
        echo -e "${GREEN}  ✓ Found: $dir${NC}"
    fi
done

# Check 3: Documentation has proper structure
echo ""
echo -e "${BLUE}[3/7] Checking documentation file structure...${NC}"

check_doc_structure() {
    local file=$1
    local has_header=false
    local has_status=false
    local has_date=false

    if [ -f "$file" ]; then
        # Check for markdown header
        if head -n 5 "$file" | grep -q "^# "; then
            has_header=true
        fi

        # Check for status or last updated (not all files need this)
        if grep -q "Status:" "$file" || grep -q "Last Updated:" "$file"; then
            has_status=true
        fi

        if $has_header; then
            echo -e "${GREEN}  ✓ $file has proper structure${NC}"
        else
            echo -e "${YELLOW}  ⚠️  $file missing header${NC}"
            ((WARNINGS++))
        fi
    fi
}

# Check a few key files
check_doc_structure "docs/project-overview/FEATURES_SUMMARY.md"
check_doc_structure "docs/README.md"

# Check 4: No broken markdown links (basic check)
echo ""
echo -e "${BLUE}[4/7] Checking for obvious broken links...${NC}"

find docs -name "*.md" -type f | while read -r file; do
    # Look for [text](path) where path ends in .md but doesn't exist
    broken_links=$(grep -oE '\[([^\]]+)\]\(([^)]+\.md[^)]*)\)' "$file" | sed 's/.*(\(.*\))/\1/' | cut -d'#' -f1)

    for link in $broken_links; do
        # Skip http/https links
        if [[ $link == http* ]]; then
            continue
        fi

        # Check if relative path exists
        dir=$(dirname "$file")
        if [[ $link == /* ]]; then
            target_file=".$link"
        else
            target_file="$dir/$link"
        fi

        if [ ! -f "$target_file" ]; then
            echo -e "${YELLOW}  ⚠️  Potentially broken link in $file: $link${NC}"
            ((WARNINGS++))
        fi
    done
done

echo -e "${GREEN}  Link check complete${NC}"

# Check 5: Documentation for recent bug fixes
echo ""
echo -e "${BLUE}[5/7] Checking bug fix documentation...${NC}"

if [ -d "docs/bug-fixes" ]; then
    bug_fix_count=$(find docs/bug-fixes -name "*.md" -type f | wc -l)
    echo -e "${GREEN}  ✓ Found $bug_fix_count bug fix documentation files${NC}"
else
    echo -e "${YELLOW}  ⚠️  docs/bug-fixes directory missing${NC}"
    ((WARNINGS++))
fi

# Check 6: Feature documentation
echo ""
echo -e "${BLUE}[6/7] Checking feature documentation...${NC}"

if [ -d "docs/features" ]; then
    feature_count=$(find docs/features -name "*.md" -type f | wc -l)
    echo -e "${GREEN}  ✓ Found $feature_count feature documentation files${NC}"
else
    echo -e "${YELLOW}  ⚠️  docs/features directory missing${NC}"
    ((WARNINGS++))
fi

# Check 7: Run Python compliance checker
echo ""
echo -e "${BLUE}[7/7] Running Python compliance checker...${NC}"

if command -v python3 &> /dev/null; then
    if [ -f ".claude/scripts/check_documentation_compliance.py" ]; then
        if python3 .claude/scripts/check_documentation_compliance.py --verbose; then
            echo -e "${GREEN}  ✓ Python compliance checks passed${NC}"
        else
            echo -e "${RED}  ❌ Python compliance checks failed${NC}"
            ((ERRORS++))
        fi
    else
        echo -e "${YELLOW}  ⚠️  Compliance checker script not found${NC}"
        ((WARNINGS++))
    fi
else
    echo -e "${YELLOW}  ⚠️  Python3 not available, skipping compliance checks${NC}"
    ((WARNINGS++))
fi

# Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Validation Summary${NC}"
echo -e "${BLUE}========================================${NC}"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Documentation is in good shape.${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  $WARNINGS warning(s) found${NC}"
    echo -e "${YELLOW}Documentation is mostly good but could be improved.${NC}"
    exit 0
else
    echo -e "${RED}❌ $ERRORS error(s) and $WARNINGS warning(s) found${NC}"
    echo -e "${RED}Please fix the errors above.${NC}"
    exit 1
fi
