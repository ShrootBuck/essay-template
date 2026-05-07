#!/bin/bash
# Setup script to install git hooks

echo "Installing git hooks..."
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
echo "Pre-commit hook installed!"
