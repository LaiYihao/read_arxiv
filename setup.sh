#!/bin/bash
# Setup script for arXiv Report

set -e

echo "========================================="
echo "arXiv Report — Setup Script"
echo "========================================="

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "Error: Conda is not installed. Please install Miniconda or Anaconda first."
    exit 1
fi

# Create conda environment
echo ""
echo "Creating conda environment 'arxiv-report'..."
conda env create -f environment.yml --yes

echo ""
echo "Setup completed!"
echo ""
echo "To activate the environment, run:"
echo "  conda activate arxiv-report"
echo ""
echo "Then copy .env.example to .env and fill in your DeepSeek API key:"
echo "  cp .env.example .env"
echo "  # Edit .env with your API key"
echo ""
echo "Finally, run the application:"
echo "  python main.py"
