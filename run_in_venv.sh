#!/bin/bash
# Script to ensure commands run in virtual environment

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" != *"yc_env"* ]]; then
    echo "Activating virtual environment..."
    source yc_env/bin/activate
fi

# Execute the command passed as arguments
"$@" 