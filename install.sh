#!/bin/bash
# GPT-OS Installation Script
# This script installs GPT-OS and its dependencies

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                   GPT-OS Installation                         ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ Error: GPT-OS currently only supports Linux"
    exit 1
fi

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not installed"
    echo "   Install it with: sudo apt install python3 python3-pip"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check for pip
if ! command -v pip3 &> /dev/null; then
    echo "📦 Installing pip3..."
    sudo apt update
    sudo apt install -y python3-pip
fi

echo "✅ pip3 found: $(pip3 --version)"

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip3 install --user openai

# Make the shell executable
echo ""
echo "🔧 Making GPT shell executable..."
chmod +x gpt_shell.py

# Create a convenient launcher script
echo ""
echo "🔧 Creating launcher script..."
cat > gpt-os << 'EOF'
#!/bin/bash
# GPT-OS Launcher
cd "$(dirname "$0")"
python3 gpt_shell.py "$@"
EOF

chmod +x gpt-os

# Check for OpenAI API key
echo ""
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OpenAI API key not found in environment"
    echo ""
    echo "To use GPT-OS, you need an OpenAI API key:"
    echo "1. Get your API key from: https://platform.openai.com/api-keys"
    echo "2. Set it in your environment:"
    echo "   export OPENAI_API_KEY='your-api-key-here'"
    echo ""
    echo "Add this to your ~/.bashrc or ~/.zshrc to make it permanent:"
    echo "   echo 'export OPENAI_API_KEY=\"your-api-key-here\"' >> ~/.bashrc"
    echo ""
else
    echo "✅ OpenAI API key found"
fi

# Offer to add to PATH
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                  Installation Complete!                       ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 To start GPT-OS, run:"
echo "   ./gpt-os"
echo ""
echo "Or add it to your PATH for system-wide access:"
echo "   sudo ln -s $(pwd)/gpt-os /usr/local/bin/gpt-os"
echo ""
echo "Then you can run it from anywhere with:"
echo "   gpt-os"
echo ""
