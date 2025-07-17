# Makefile for Interaction Framework
# Provides convenient commands for testing and automation

.PHONY: help install-test-deps setup-hooks test test-quick test-api test-frontend test-performance test-integration test-all validate docker-test clean

# Default target
help:
	@echo "🎯 Interaction Framework - Automated Testing"
	@echo ""
	@echo "📦 Setup Commands:"
	@echo "  install-test-deps    Install testing dependencies"
	@echo "  setup-hooks         Install Git hooks for automatic testing"
	@echo "  setup-precommit     Install pre-commit framework"
	@echo "  validate            Validate test setup"
	@echo ""
	@echo "🧪 Test Commands:"
	@echo "  test-quick          Run quick tests (unit + API)"
	@echo "  test-api            Run API tests"
	@echo "  test-frontend       Run frontend UI tests"
	@echo "  test-performance    Run performance tests"
	@echo "  test-integration    Run integration tests"
	@echo "  test-all            Run all tests"
	@echo ""
	@echo "🐳 Docker Commands:"
	@echo "  docker-test         Run tests in Docker container"
	@echo "  docker-test-all     Run all tests in Docker"
	@echo ""
	@echo "🧹 Utility Commands:"
	@echo "  clean              Clean up test artifacts"
	@echo "  format             Format code with black and isort"

# Setup commands
install-test-deps:
	@echo "📦 Installing test dependencies..."
	pip install -r requirements.txt
	playwright install chromium

setup-hooks:
	@echo "🔧 Setting up Git hooks..."
	chmod +x setup_git_hooks.sh
	./setup_git_hooks.sh

setup-precommit:
	@echo "🔧 Setting up pre-commit framework..."
	pip install pre-commit
	pre-commit install
	pre-commit install --hook-type pre-push

validate:
	@echo "🔍 Validating test setup..."
	python tests/validate_setup.py

# Test commands
test-quick:
	@echo "🏃‍♂️ Running quick tests..."
	python tests/run_tests.py quick

test-api:
	@echo "🔗 Running API tests..."
	python tests/run_tests.py api

test-frontend:
	@echo "🖥️ Running frontend tests..."
	python tests/run_tests.py frontend

test-performance:
	@echo "⚡ Running performance tests..."
	python tests/run_tests.py performance

test-integration:
	@echo "🔄 Running integration tests..."
	python tests/run_tests.py integration

test-all:
	@echo "🎯 Running all tests..."
	python tests/run_tests.py all

# Docker commands
docker-test:
	@echo "🐳 Running tests in Docker..."
	docker-compose -f docker-compose.test.yml run --rm test-runner

docker-test-all:
	@echo "🐳 Running all tests in Docker..."
	docker-compose -f docker-compose.test.yml run --rm full-test-suite

# Utility commands
clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .coverage htmlcov/ test-results/ 2>/dev/null || true

format:
	@echo "✨ Formatting code..."
	black --line-length=100 .
	isort --profile=black --line-length=100 .

# Development workflow
dev-setup: install-test-deps setup-hooks validate
	@echo "✅ Development environment setup complete!"
	@echo "💡 Try: make test-quick"

ci-setup: install-test-deps validate
	@echo "✅ CI environment setup complete!"

# Continuous testing (runs tests when files change)
watch:
	@echo "👀 Watching for file changes..."
	@echo "💡 Install: pip install watchdog"
	python -m watchdog.watchmedo auto-restart --patterns="*.py" --recursive . python tests/run_tests.py quick