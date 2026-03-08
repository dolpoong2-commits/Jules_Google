#!/bin/bash
# setup.sh
# Automated Environment Setup Script for Local LLM Agent Architecture on Ubuntu

set -e

echo "Starting Local LLM Agent Environment Setup..."

# 1. Update system packages
echo "Updating system..."
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y curl wget git build-essential docker.io docker-compose python3 python3-pip python3-venv sqlite3 postgresql postgresql-contrib

# 2. Install NVM (Node Version Manager) & Node.js 22
echo "Installing NVM & Node.js 22..."
if [ ! -d "$HOME/.nvm" ]; then
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
else
    echo "NVM already installed."
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
fi

nvm install 22
nvm use 22
nvm alias default 22

# 3. Install OpenClaw, OpenGoat (Node-based orchestrators)
echo "Installing OpenClaw and OpenGoat..."
npm install -g openclaw opengoat

# 4. Install Antigravity (Agent Development Platform)
echo "Installing Antigravity..."
npm install -g @google/antigravity

# 5. Install Python Dependencies (LiteLLM, NadirClaw)
echo "Setting up Python environment..."
python3 -m venv ~/llm-agent-env
source ~/llm-agent-env/bin/activate

echo "Installing Python dependencies (LiteLLM, python-telegram-bot, mcp)..."
pip install litellm python-telegram-bot mcp pydantic requests
# Placeholder for NadirClaw which acts as a proxy
# If NadirClaw is pip installable from github:
# pip install git+https://github.com/doramirdor/NadirClaw.git
echo "To install NadirClaw natively, clone from https://github.com/doramirdor/NadirClaw and follow its setup."

# 6. Install Cursor IDE
echo "Installing Cursor..."
CURSOR_APPIMAGE="Cursor-x86_64.AppImage"
if [ ! -f "$CURSOR_APPIMAGE" ]; then
    wget -O $CURSOR_APPIMAGE "https://downloader.cursor.sh/linux/appImage/x64"
    chmod +x $CURSOR_APPIMAGE
    echo "Cursor downloaded. Run it with ./$CURSOR_APPIMAGE"
else
    echo "Cursor AppImage already exists."
fi

echo "Setup complete!"
echo "Please reload your shell or run: source ~/.bashrc"
echo "Then activate your python env: source ~/llm-agent-env/bin/activate"
