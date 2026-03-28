#!/bin/bash
# setup.sh
# Automated Environment Setup Script for Local LLM Agent Architecture on Ubuntu

set -e

echo "Starting Local LLM Agent Environment Setup..."

# 1. Update system packages & Install Docker
echo "Updating system..."
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y curl wget git build-essential docker.io docker-compose-v2 python3 python3-pip python3-venv sqlite3 postgresql postgresql-contrib

# 1.5 Install NVIDIA Container Toolkit (Required for vLLM)
echo "Installing NVIDIA Container Toolkit..."
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

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

echo "Installing Python dependencies (LiteLLM, python-telegram-bot, mcp, flask, python-dotenv)..."
pip install litellm python-telegram-bot mcp pydantic requests flask pyyaml python-dotenv
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
echo "--------------------------------------------------------"
echo "⚠️ IMPORTANT NEXT STEPS:"
echo "1. Copy .env.example to .env and fill in your tokens:"
echo "   cp .env.example .env"
echo "   nano .env"
echo "2. Reload your shell or run: source ~/.bashrc"
echo "3. Activate your python env: source ~/llm-agent-env/bin/activate"
echo "4. Configure your models: python configure_models.py"
echo "--------------------------------------------------------"
