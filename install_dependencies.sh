#!/bin/bash

# Set up environment
echo "Setting up environment for Law Assistant..."

# Install required Python packages
echo "Installing Python dependencies..."
pip install --no-cache-dir "spacy>=3.6.0" "sentencepiece>=0.1.99"

# Download spaCy French language model
echo "Downloading spaCy French language model..."
python -m spacy download fr_core_news_lg

# Install Hugging Face transformers if not already installed
echo "Ensuring transformers is installed..."
pip install --no-cache-dir "transformers>=4.41.0"

# Set up PYTHONPATH for development environment
echo "Setting up PYTHONPATH..."
PROJECT_DIR=$(pwd)
export PYTHONPATH=$PROJECT_DIR:$PYTHONPATH
echo "PYTHONPATH is now set to: $PYTHONPATH"

echo "Installation complete! You can now run the data_admin.py tool."
echo "For permanent PYTHONPATH configuration, add the following to your .zshrc file:"
echo "export PYTHONPATH=$PROJECT_DIR:\$PYTHONPATH" 