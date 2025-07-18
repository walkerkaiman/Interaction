# 🤖 Automated Testing Setup Guide

This guide explains how to set up automatic testing for the Interaction Framework. Choose the approach that best fits your workflow.

## 🚀 **Quick Setup (Recommended)**

```bash
# Install everything and set up Git hooks
make dev-setup

# Or manually:
python tests/run_tests.py install
./setup_git_hooks.sh
python tests/validate_setup.py
```

## 🔄 **1. Git Hooks (Local Automation)**

Automatically run tests before commits and pushes.

### Setup
```bash
# Simple setup
./setup_git_hooks.sh

# Or using make
make setup-hooks
```

### What it does:
- **Pre-commit**: Runs quick tests (unit + API) before each commit
- **Pre-push**: Runs comprehensive tests before pushes to main/develop
- **Automatic**: No manual intervention needed

### Usage:
```bash
# Normal workflow - tests run automatically
git add .
git commit -m "Add new feature"  # ← Tests run here
git push origin main             # ← More tests run here

# Bypass if needed (use sparingly)
git commit --no-verify
git push --no-verify
```

---

## 🤖 **2. GitHub Actions (CI/CD)**

Automatic testing on GitHub for every push and PR.

### Setup
1. The `.github/workflows/tests.yml` file is already configured
2. Push to GitHub - workflows will run automatically
3. Check the "Actions" tab in your GitHub repository

### What it does:
- **On every push/PR**: Quick tests and frontend tests
- **On main branch**: Full test suite including performance and integration
- **Daily**: Test matrix across Python versions
- **Security**: Dependency vulnerability scanning

### Viewing Results:
- Go to your GitHub repo → Actions tab
- See test results for each commit/PR
- Get notifications if tests fail

---

## 🔧 **3. Pre-commit Framework (Advanced)**

More sophisticated hook management with code formatting and linting.

### Setup
```bash
# Install pre-commit
pip install pre-commit

# Set up hooks
make setup-precommit

# Or manually
pre-commit install
pre-commit install --hook-type pre-push
```

### Features:
- **Smart testing**: Only runs relevant tests for changed files
- **Code formatting**: Automatic formatting with Black and isort
- **Linting**: Code quality checks with flake8
- **Security**: Security scanning with bandit
- **File checks**: JSON/YAML validation, trailing whitespace, etc.

### Usage:
```bash
# Run all hooks manually
pre-commit run --all-files

# Update hook versions
pre-commit autoupdate
```

---

## 🐳 **4. Docker Testing**

Consistent testing environment regardless of your local setup.

### Setup
```bash
# Build test container
docker-compose -f docker-compose.test.yml build

# Or use make commands
make docker-test        # Quick tests
make docker-test-all    # Full suite
```

### Benefits:
- **Consistent**: Same environment as CI/CD
- **Isolated**: Doesn't affect your local Python environment
- **Clean**: Fresh environment for each test run

### Usage:
```bash
# Different test suites
docker-compose -f docker-compose.test.yml run --rm test-runner      # Quick
docker-compose -f docker-compose.test.yml run --rm api-tests        # API only
docker-compose -f docker-compose.test.yml run --rm frontend-tests   # UI only
docker-compose -f docker-compose.test.yml run --rm full-test-suite  # Everything
```

---

## 📋 **5. Makefile Commands**

Convenient shortcuts for all testing operations.

### Available Commands:
```bash
make help              # Show all available commands

# Setup
make install-test-deps # Install dependencies
make setup-hooks       # Install Git hooks
make setup-precommit   # Install pre-commit framework
make validate          # Validate test setup

# Testing
make test-quick        # Quick tests (recommended for development)
make test-api          # API tests only
make test-frontend     # Frontend UI tests only
make test-performance  # Performance benchmarks
make test-integration  # End-to-end tests
make test-all          # Everything

# Docker
make docker-test       # Quick tests in Docker
make docker-test-all   # Full suite in Docker

# Utilities
make clean            # Clean up test artifacts
make format           # Format code
make watch            # Watch files and run tests on changes
```

---

## ⚙️ **Configuration Options**

### Test Selection
```bash
# Run specific test types
python tests/run_tests.py api           # Just API tests
python tests/run_tests.py frontend      # Just UI tests
python tests/run_tests.py performance   # Just performance tests

# Run with different options
pytest tests/ -m "not slow"             # Skip slow tests
pytest tests/ -x                        # Stop on first failure
pytest tests/ --headed                  # Show browser (not headless)
```

### Environment Variables
```bash
export PYTEST_HEADLESS=true             # Force headless browser tests
export INTERACTION_CONFIG_DIR=/tmp/test  # Custom config directory
```

### CI/CD Customization
Edit `.github/workflows/tests.yml` to:
- Change Python versions tested
- Modify when tests run (branches, schedule)
- Add notifications (Slack, email, etc.)
- Add deployment steps after successful tests

---

## 🎯 **Recommended Workflows**

### For Solo Development:
1. **Setup**: `make dev-setup`
2. **Daily coding**: Git hooks run tests automatically
3. **Before releases**: `make test-all`

### For Teams:
1. **Setup**: Git hooks + GitHub Actions
2. **Feature development**: Tests run on every commit/push
3. **Code review**: PR tests must pass before merge
4. **Deployment**: Full test suite before production

### For Production:
1. **All of the above** plus:
2. **Docker testing** for consistent environments
3. **Scheduled tests** (daily/weekly)
4. **Performance monitoring** with alerts
5. **Security scanning** integrated

---

## 🚨 **Troubleshooting**

### Tests failing locally but not in CI:
```bash
# Use Docker to match CI environment
make docker-test

# Check Python version differences
python --version
```

### Browser tests failing:
```bash
# Update browsers
playwright install chromium

# Run with visible browser for debugging
pytest tests/test_frontend_ui.py --headed --slowmo=1000
```

### Slow tests:
```bash
# Run only fast tests
make test-quick

# Or skip slow tests
pytest tests/ -m "not slow"
```

### Git hooks not working:
```bash
# Reinstall hooks
./setup_git_hooks.sh

# Check hook permissions
ls -la .git/hooks/
```

### Import errors:
```bash
# Ensure you're in project root
pwd  # Should show your project directory

# Reinstall dependencies
pip install -r requirements.txt
```

---

## 📊 **Monitoring Test Health**

### Test Coverage
```bash
# Install coverage tools
pip install pytest-cov

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# View report
open htmlcov/index.html
```

### Performance Tracking
The test suite includes performance benchmarks that will alert you if:
- API response times exceed 1 second
- Event processing drops below 1000 events/second
- Memory usage grows excessively
- UI interactions become slow

### Test Results History
- **GitHub Actions**: Check the Actions tab for historical results
- **Local**: Test results are logged in the terminal
- **Docker**: Results saved to `test-results/` volume

---

## 🎉 **Success Indicators**

You'll know automatic testing is working when:
- ✅ Commits are blocked if tests fail
- ✅ GitHub shows green checkmarks on PRs
- ✅ You catch bugs before they reach production
- ✅ Refactoring is safe and confident
- ✅ Team members can contribute without breaking things

---

## 🆘 **Getting Help**

1. **Check the logs**: Test output usually explains what failed
2. **Validate setup**: Run `python tests/validate_setup.py`
3. **Check this guide**: Most issues are covered above
4. **Run individual tests**: Isolate the problem with specific test files
5. **Use debug mode**: Add `--pdb` to pytest commands for debugging

Remember: The goal is to make testing automatic and painless, so you can focus on building amazing features! 🚀