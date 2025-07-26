#!/bin/bash
# Script to activate the YC demo day batch virtual environment

echo "Activating YC Demo Day Batch virtual environment..."
source yc_env/bin/activate
echo "Virtual environment activated!"
echo "You can now run: python main.py --action scrape" 