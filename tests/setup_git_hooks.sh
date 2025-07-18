#!/bin/bash
#
# Setup script for Git hooks
# Installs pre-commit and pre-push hooks for automatic testing
#

set -e

echo "🔧 Setting up Git hooks for automatic testing..."

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a Git repository"
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Copy and make hooks executable
echo "📋 Installing pre-commit hook..."
cp .githooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

echo "📋 Installing pre-push hook..."
cp .githooks/pre-push .git/hooks/pre-push
chmod +x .git/hooks/pre-push

echo "✅ Git hooks installed successfully!"
echo ""
echo "📝 What happens now:"
echo "  • Before each commit: Quick tests (unit + API) will run"
echo "  • Before each push: Comprehensive tests will run"
echo "  • Tests must pass for commits/pushes to proceed"
echo ""
echo "🆘 To bypass hooks (use sparingly):"
echo "  • git commit --no-verify"
echo "  • git push --no-verify"
echo ""
echo "🧪 Test the setup:"
echo "  git add ."
echo "  git commit -m 'Test automatic testing'"