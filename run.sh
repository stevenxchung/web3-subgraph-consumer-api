#!/bin/bash

VENV_PATH=".venv"
PROGRAM_PATH="src/app.py"
PROJECT_ROOT=$(pwd)
PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/src"

# Activate the virtual environment (adjust depending on your operating system)
echo "Activating Python virtual environment..."
source "$VENV_PATH/Scripts/activate"

# Set the Python path
export PYTHONPATH

# Start the application
python "$PROGRAM_PATH"
