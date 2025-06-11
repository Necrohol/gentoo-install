#!/bin/bash

# Wrapper for gentoo_repo_manager.py

SCRIPT_PATH="./user-contributed-scripts/gentoo_repo_manager.py"
PYTHON_EXEC="python3"

# Execute the script with any passed arguments
$PYTHON_EXEC "$SCRIPT_PATH" "$@"
