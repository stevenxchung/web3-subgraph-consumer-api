#!/bin/bash

VENV_PATH=".venv"

# Activate the virtual environment (adjust depending on your operating system)
echo "Activating Python virtual environment..."
source "$VENV_PATH/Scripts/activate"

# Run acceptance tests
python -m pytest tests/e2e/
