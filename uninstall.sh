#!/bin/bash
# AI Marketing Skills — Claude Code Skills Uninstaller
# Removes market-ru-seo skill

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   AI Marketing Suite — Claude Code           ║${NC}"
echo -e "${CYAN}║   market-ru-seo Uninstaller                 ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════╝${NC}"
echo ""

SKILLS_DIR="$HOME/.claude/skills"
AGENTS_DIR="$HOME/.claude/agents"

REMOVED=0

if [ -d "$SKILLS_DIR/market-ru-seo" ]; then
    rm -rf "$SKILLS_DIR/market-ru-seo"
    echo -e "  ${GREEN}✓${NC} Removed $SKILLS_DIR/market-ru-seo/"
    REMOVED=$((REMOVED + 1))
fi

if [ -f "$AGENTS_DIR/market-ru-seo.md" ]; then
    rm -f "$AGENTS_DIR/market-ru-seo.md"
    echo -e "  ${GREEN}✓${NC} Removed $AGENTS_DIR/market-ru-seo.md"
    REMOVED=$((REMOVED + 1))
fi

echo ""
if [ $REMOVED -gt 0 ]; then
    echo -e "${GREEN}Uninstallation complete!${NC}"
    echo -e "  Removed $REMOVED item(s)"
else
    echo -e "${YELLOW}market-ru-seo was not installed${NC}"
fi
echo ""