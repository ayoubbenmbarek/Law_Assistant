#!/usr/bin/env python3
"""
Script to check environment variables
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Print relevant variables
print("SUMMARIZER_MODEL:", os.getenv("SUMMARIZER_MODEL"))
print("NLP_MODEL:", os.getenv("NLP_MODEL"))
print("HUGGINGFACE_TOKEN:", os.getenv("HUGGINGFACE_TOKEN")[:5] + "..." if os.getenv("HUGGINGFACE_TOKEN") else None) 