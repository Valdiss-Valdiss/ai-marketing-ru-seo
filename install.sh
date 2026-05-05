#!/bin/bash
# AI Marketing Skills — Claude Code Skills Installer
# Single skill: market-ru-seo

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   AI Marketing Suite — Claude Code Skills      ║${NC}"
echo -e "${CYAN}║   market-ru-seo (SEO-аудит)                  ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════╝${NC}"
echo ""

if [ -n "$BASH_SOURCE" ] && [ "$BASH_SOURCE" != "bash" ] && [ -f "$BASH_SOURCE" ]; then
    SCRIPT_DIR="$(cd "$(dirname "$BASH_SOURCE")" && pwd)"
else
    echo -e "${YELLOW}Running remote install — cloning repository...${NC}"
    TEMP_DIR=$(mktemp -d)
    git clone --depth 1 https://github.com/Valdiss-Valdiss/ai-marketing-ru-seo.git "$TEMP_DIR/ai-marketing-ru-seo" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to clone repository.${NC}"
        exit 1
    fi
    SCRIPT_DIR="$TEMP_DIR/ai-marketing-ru-seo"
fi

SKILLS_DIR="$HOME/.claude/skills"

echo -e "${BLUE}Source:${NC}  $SCRIPT_DIR"
echo -e "${BLUE}Target:${NC} $SKILLS_DIR"
echo ""

if command -v claude &>/dev/null; then
    echo -e "${GREEN}✓ Claude Code detected${NC}"
else
    echo -e "${YELLOW}⚠ Claude Code not found in PATH${NC}"
    if [ -t 0 ]; then
        read -p "  Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Installation cancelled."
            exit 0
        fi
    else
        echo "  Continuing (non-interactive mode)..."
    fi
fi

mkdir -p "$SKILLS_DIR"

echo -e "${BLUE}Installing market-ru-seo...${NC}"
mkdir -p "$SKILLS_DIR/market-ru-seo"
cp "$SCRIPT_DIR/skills/market-ru-seo/SKILL.md" "$SKILLS_DIR/market-ru-seo/SKILL.md"
echo -e "  ${GREEN}✓${NC} skills/market-ru-seo/SKILL.md"

if [ -f "$SCRIPT_DIR/agents/market-ru-seo.md" ]; then
    mkdir -p "$HOME/.claude/agents"
    cp "$SCRIPT_DIR/agents/market-ru-seo.md" "$HOME/.claude/agents/market-ru-seo.md"
    echo -e "  ${GREEN}✓${NC} agents/market-ru-seo.md"
fi

SCRIPTS_TARGET="$SKILLS_DIR/market-ru-seo/scripts"
mkdir -p "$SCRIPTS_TARGET"

if [ -f "$SCRIPT_DIR/scripts/analyze_page.py" ]; then
    cp "$SCRIPT_DIR/scripts/analyze_page.py" "$SCRIPTS_TARGET/analyze_page.py"
    chmod +x "$SCRIPTS_TARGET/analyze_page.py"
    echo -e "  ${GREEN}✓${NC} scripts/analyze_page.py"
fi

echo -e "${BLUE}Checking Python dependencies...${NC}"
if command -v python3 &>/dev/null; then
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
    echo -e "  ${GREEN}✓${NC} Python $PYTHON_VERSION detected"
else
    echo -e "  ${YELLOW}⚠${NC} Python 3 not found — scripts won't work"
fi

if [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ]; then
    rm -rf "$TEMP_DIR"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Installation Complete!              ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Skills installed:    ${GREEN}1${NC} (market-ru-seo)"
echo ""
echo -e "${CYAN}Available Commands:${NC}"
echo "  /market-ru-seo <url>  SEO-аудит сайта (Google + Яндекс)"
echo ""
echo -e "${CYAN}Usage in Claude Code:${NC}"
echo "  1. Start new Claude Code session"
echo "  2. Type: /market-ru-seo https://example.com"
echo ""
echo -e "  ${YELLOW}For OpenCode: npm install -g market-ru-seo${NC}"
echo ""