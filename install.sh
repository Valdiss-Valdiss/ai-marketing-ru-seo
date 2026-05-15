#!/bin/bash
# AI Marketing Skills — Universal Installer
# Supports: OpenCode + Claude Code on macOS, Linux, Windows (Git Bash/WSL)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SKILL_NAME="market-ru-seo"
REPO="https://github.com/Valdiss-Valdiss/ai-marketing-ru-seo.git"

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   AI Marketing Suite — Universal Installer    ║${NC}"
echo -e "${CYAN}║   $SKILL_NAME                            ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════╝${NC}"
echo ""

detect_platform() {
    if command -v claude &>/dev/null; then
        echo "claude"
    elif [ -d "$HOME/.claude" ]; then
        echo "claude"
    elif [ -d "$HOME/.config/opencode" ] || [ -n "$OPENCODE_CONFIG_DIR" ]; then
        echo "opencode"
    elif command -v opencode &>/dev/null; then
        echo "opencode"
    else
        echo "unknown"
    fi
}

if [ -n "$BASH_SOURCE" ] && [ "$BASH_SOURCE" != "bash" ] && [ -f "$BASH_SOURCE" ]; then
    SCRIPT_DIR="$(cd "$(dirname "$BASH_SOURCE")" && pwd)"
else
    echo -e "${YELLOW}Running remote install — cloning repository...${NC}"
    TEMP_DIR=$(mktemp -d)
    git clone --depth 1 "$REPO" "$TEMP_DIR/$SKILL_NAME" 2>/dev/null || {
        echo -e "${RED}Failed to clone repository.${NC}"
        exit 1
    }
    SCRIPT_DIR="$TEMP_DIR/$SKILL_NAME"
fi

PLATFORM=$(detect_platform)
echo -e "${BLUE}Detected platform:${NC} $PLATFORM"

case "$PLATFORM" in
    claude)
        echo -e "${GREEN}Installing for Claude Code...${NC}"
        SKILLS_DIR="$HOME/.claude/skills"
        AGENTS_DIR="$HOME/.claude/agents"

        mkdir -p "$SKILLS_DIR"
        mkdir -p "$AGENTS_DIR"

        echo -e "${BLUE}Installing $SKILL_NAME...${NC}"
        mkdir -p "$SKILLS_DIR/$SKILL_NAME"
        cp "$SCRIPT_DIR/skills/$SKILL_NAME/SKILL.md" "$SKILLS_DIR/$SKILL_NAME/SKILL.md"
        echo -e "  ${GREEN}✓${NC} skills/$SKILL_NAME/SKILL.md"

        if [ -f "$SCRIPT_DIR/agents/$SKILL_NAME.md" ]; then
            cp "$SCRIPT_DIR/agents/$SKILL_NAME.md" "$AGENTS_DIR/$SKILL_NAME.md"
            echo -e "  ${GREEN}✓${NC} agents/$SKILL_NAME.md"
        fi

        SCRIPTS_TARGET="$SKILLS_DIR/$SKILL_NAME/scripts"
        mkdir -p "$SCRIPTS_TARGET"
        if [ -d "$SCRIPT_DIR/scripts" ]; then
            cp "$SCRIPT_DIR/scripts"/*.py "$SCRIPTS_TARGET/" 2>/dev/null || true
            echo -e "  ${GREEN}✓${NC} scripts/*.py"
        fi
        ;;

    opencode)
        echo -e "${GREEN}Installing for OpenCode...${NC}"

        if command -v npm &>/dev/null; then
            echo -e "${BLUE}Installing via npm...${NC}"
            cd "$SCRIPT_DIR"
            npm install -g 2>/dev/null || {
                echo -e "${YELLOW}npm install failed, trying alternative...${NC}"
            }
            cd ~
        fi

        NPM_ROOT=$(npm root -g 2>/dev/null)
        if [ -d "$NPM_ROOT/$SKILL_NAME" ]; then
            echo -e "${GREEN}✓${NC} npm package installed to $NPM_ROOT/$SKILL_NAME"

            OPENCODE_JSON="$HOME/.config/opencode/opencode.json"
            if [ -f "$OPENCODE_JSON" ]; then
                PLUGIN_PATH="$NPM_ROOT/$SKILL_NAME/.opencode/plugins/$SKILL_NAME.js"

                if ! grep -q "$PLUGIN_PATH" "$OPENCODE_JSON" 2>/dev/null; then
                    echo -e "${BLUE}Adding plugin to opencode.json...${NC}"

                    if grep -q '"plugin": \[' "$OPENCODE_JSON"; then
                        sed -i "s|(\"plugin\": \[)|\\1\n    \"$PLUGIN_PATH\",|" "$OPENCODE_JSON"
                    else
                        echo "  ${YELLOW}⚠${NC} Could not find plugin array in opencode.json"
                        echo "  Please add manually: $PLUGIN_PATH"
                    fi
                else
                    echo -e "${GREEN}✓${NC} Plugin already in opencode.json"
                fi
            else
                echo -e "${YELLOW}⚠${NC} opencode.json not found at $OPENCODE_JSON"
            fi
        else
            echo -e "${YELLOW}⚠${NC} npm package not found, falling back to manual install"
            MANUAL_DIR="$HOME/.config/skills/$SKILL_NAME"
            mkdir -p "$MANUAL_DIR"
            cp -r "$SCRIPT_DIR/skills/$SKILL_NAME" "$MANUAL_DIR/"
            echo -e "${GREEN}✓${NC} Installed to $MANUAL_DIR"
        fi
        ;;

    *)
        echo -e "${YELLOW}⚠ Unknown platform, installing for Claude Code as fallback${NC}"
        SKILLS_DIR="$HOME/.claude/skills"
        mkdir -p "$SKILLS_DIR"
        mkdir -p "$SKILLS_DIR/$SKILL_NAME"
        cp -r "$SCRIPT_DIR/skills/$SKILL_NAME" "$SKILLS_DIR/"
        echo -e "${GREEN}✓${NC} Installed to $SKILLS_DIR/$SKILL_NAME"
        ;;
esac

if [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ]; then
    rm -rf "$TEMP_DIR"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Installation Complete!              ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Available Commands:${NC}"
echo "  /market-ru-seo <url>  SEO-аудит сайта (Google + Яндекс)"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Restart your AI assistant (OpenCode or Claude Code)"
echo "  2. Type: /market-ru-seo https://example.com"
echo ""