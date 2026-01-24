#!/bin/bash
# Quick setup script

echo "Peronospora Inference - Quick Setup"
echo "===================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi
echo "✓ Python 3 found"

# Create venv
echo "→ Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "→ Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Configure AWS credentials - see DEVELOPER_GUIDE.md"
echo "  2. Run: python run_inference_pipeline.py"
