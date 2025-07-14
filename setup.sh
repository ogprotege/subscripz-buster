#!/bin/bash
# Subscripz-Buster Quick Setup Script
# Make executable with: chmod +x setup.sh

echo "🚀 Subscripz-Buster Setup"
echo "========================="
echo ""

# Check Python version
echo "📍 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then 
    echo "✅ Python $python_version (OK)"
else
    echo "❌ Python $python_version is too old. Need 3.8+"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "server.py" ]; then
    echo "❌ Error: Run this script from the subscripz-buster directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment exists"
fi

# Activate virtual environment
echo ""
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo ""
echo "📚 Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet pandas openpyxl

# Create requirements.txt if it doesn't exist
if [ ! -f "requirements.txt" ]; then
    echo "pandas>=1.3.0" > requirements.txt
    echo "openpyxl>=3.0.0" >> requirements.txt
    echo "✅ Created requirements.txt"
fi

# Test setup
echo ""
echo "🧪 Testing setup..."
python3 test_setup.py

# Check MCP installation
echo ""
echo "🔍 Checking MCP installation..."
if python3 -c "import mcp" 2>/dev/null; then
    echo "✅ MCP is installed"
else
    echo "⚠️  MCP not found. Installing..."
    pip install --quiet "mcp[cli]"
fi

# Create Claude config example
echo ""
echo "📝 Creating Claude Desktop config example..."
cat > claude_config_example.json << 'EOF'
{
  "mcpServers": {
    "subscripz-buster": {
      "command": "/Users/YOUR_USERNAME/Desktop/subscripz-buster/.venv/bin/python",
      "args": [
        "/Users/YOUR_USERNAME/Desktop/subscripz-buster/server.py"
      ]
    }
  }
}
EOF

echo "✅ Created claude_config_example.json"

# Final instructions
echo ""
echo "✨ Setup Complete!"
echo "=================="
echo ""
echo "Next steps:"
echo "1. To use with Claude Desktop, update claude_config_example.json with your username"
echo "2. Copy it to: ~/Library/Application Support/Claude/claude_desktop_config.json"
echo "3. Restart Claude Desktop"
echo ""
echo "To run standalone:"
echo "  python3 scan_subscriptions_now.py"
echo ""
echo "For help:"
echo "  python3 scan_subscriptions_now.py"
echo "  Then choose option 5 (Debug)"
echo ""
echo "Happy subscription hunting! 💰"
