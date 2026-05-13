#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  LeadFlow AI – Mac Mini One-Click Installer
#  For non-technical real estate agents
# ─────────────────────────────────────────────────────────────
set -e

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log() { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }

echo ""
echo "  🏠 LeadFlow AI – Installer"
echo "  ─────────────────────────"
echo ""

# 1. Check Homebrew
if ! command -v brew &>/dev/null; then
  warn "Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi
log "Homebrew ready"

# 2. Check Python
if ! command -v python3 &>/dev/null; then
  warn "Installing Python..."
  brew install python
fi
log "Python ready"

# 3. Install Ollama (local AI)
if ! command -v ollama &>/dev/null; then
  warn "Installing Ollama (local AI engine)..."
  brew install ollama
fi
log "Ollama ready"

# 4. Pull AI model
warn "Downloading AI model (one-time, ~5GB)..."
ollama pull llama3.1:8b
log "AI model downloaded"

# 5. Python dependencies
warn "Installing Python packages..."
pip3 install -q fastapi uvicorn anthropic ollama geopy httpx \
  apscheduler pyyaml python-multipart jinja2 aiosqlite \
  beautifulsoup4 requests
log "Packages installed"

# 6. Create launch script
cat > ~/Desktop/Start\ LeadFlow.command << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd /path/to/realestate-lead-engine
caffeinate -i python3 app.py &
sleep 3
open http://localhost:8000
EOF
chmod +x ~/Desktop/Start\ LeadFlow.command

# Fix path in launch script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
sed -i '' "s|/path/to/realestate-lead-engine|$SCRIPT_DIR|g" ~/Desktop/Start\ LeadFlow.command

log "Launch icon created on Desktop"

echo ""
echo "  ─────────────────────────────────────────────"
echo "  🎉 Installation complete!"
echo ""
echo "  To start LeadFlow AI:"
echo "  → Double-click 'Start LeadFlow' on your Desktop"
echo ""
echo "  Your dashboard will open at: http://localhost:8000"
echo "  ─────────────────────────────────────────────"
echo ""
