#!/bin/bash
# Quick setup script for RAG Bollettini

echo "RAG Bollettini - Quick Setup"
echo "===================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi
echo "✓ Python 3 found"

# Create venv
echo "→ Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "→ Installing dependencies (this may take a while)..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Copy .env.example to .env and add your OPENAI_API_KEY"
echo "  2. Test: python run_pipeline.py --query-only"
echo "  3. Production: python scheduler.py"
