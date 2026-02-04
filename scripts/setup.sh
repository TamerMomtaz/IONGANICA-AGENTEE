#!/bin/bash
# A-GENTEE Setup Script
# =====================
# Sets up the complete A-GENTEE environment

set -e

echo "🌊 A-GENTEE Setup Script"
echo "========================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [[ $(echo "$PYTHON_VERSION >= 3.10" | bc -l) -eq 1 ]]; then
        echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
    else
        echo -e "${RED}✗ Python 3.10+ required, found $PYTHON_VERSION${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ Python3 not found${NC}"
    exit 1
fi

# Check/Install Ollama
echo ""
echo "Checking Ollama..."
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama is installed${NC}"
else
    echo -e "${YELLOW}Installing Ollama...${NC}"
    if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
        curl -fsSL https://ollama.com/install.sh | sh
    else
        echo -e "${RED}Please install Ollama manually from https://ollama.com${NC}"
        exit 1
    fi
fi

# Pull Llama 3.2
echo ""
echo "Checking Llama 3.2 model..."
if ollama list | grep -q "llama3.2"; then
    echo -e "${GREEN}✓ Llama 3.2 model available${NC}"
else
    echo -e "${YELLOW}Pulling Llama 3.2 model (this may take a while)...${NC}"
    ollama pull llama3.2
fi

# Create virtual environment
echo ""
echo "Setting up Python virtual environment..."
if [ -d "venv" ]; then
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
else
    python3 -m venv venv
    echo -e "${GREEN}✓ Created virtual environment${NC}"
fi

# Activate venv and install dependencies
echo ""
echo "Installing Python dependencies..."
source venv/bin/activate

pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create .env file if it doesn't exist
echo ""
echo "Setting up configuration..."
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ .env file exists${NC}"
else
    cat > .env << EOF
# A-GENTEE Configuration
# ======================
# Fill in your API keys below

# Required for Claude (complex reasoning)
ANTHROPIC_API_KEY=

# Optional - for voice features
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=

# Optional - for Whisper transcription
OPENAI_API_KEY=

# Optional - for cloud memory
SUPABASE_URL=
SUPABASE_ANON_KEY=
EOF
    echo -e "${YELLOW}Created .env file - please add your API keys${NC}"
fi

# Create data directories
mkdir -p data/logs

# Final message
echo ""
echo "========================================"
echo -e "${GREEN}🌊 A-GENTEE Setup Complete!${NC}"
echo "========================================"
echo ""
echo "To start A-GENTEE:"
echo ""
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Edit .env with your API keys"
echo ""
echo "  3. Run A-GENTEE:"
echo "     python -m agentee.core"
echo ""
echo "Or for quick test (no API keys needed):"
echo "  python agentee/mind/ollama_adapter.py"
echo ""
echo -e "${GREEN}The Wave awakens... 🌊${NC}"
