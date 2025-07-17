# Interaction Framework Test Suite

This directory contains comprehensive regression tests for the Interaction Framework, designed to ensure that features don't break when code is modified.

## Overview

The test suite uses **pytest** and **Playwright** to provide comprehensive coverage of:

- 🔗 **API Endpoints** - All REST API routes and functionality
- 🖥️ **Frontend UI** - Web interface components and user interactions  
- 🧩 **Module System** - Module loading, configuration, and event handling
- ⚡ **Performance** - Response times, memory usage, and throughput
- 🔄 **Integration** - End-to-end workflows and cross-component interactions

## Quick Start

### 1. Install Dependencies

```bash
# Install test dependencies and Playwright browsers
python tests/run_tests.py install
```

### 2. Run Quick Regression Tests

```bash
# Run fast unit and API tests (recommended for development)
python tests/run_tests.py quick
```

### 3. Run Full Test Suite

```bash
# Run all tests (takes longer, includes UI tests)
python tests/run_tests.py all
```

## Test Suites

### 🏃‍♂️ Quick Tests (Recommended for Development)
```bash
python tests/run_tests.py quick
```
- Fast unit tests
- API endpoint validation
- Module system verification
- **Runtime: ~30 seconds**

### 🔗 API Tests
```bash
python tests/run_tests.py api
```
- Tests all REST endpoints (`/modules`, `/config`, `/api/*`)
- Validates request/response formats
- Checks error handling
- Tests file upload/download functionality

### 🖥️ Frontend UI Tests
```bash
python tests/run_tests.py frontend
```
- Tests web interface with real browser
- Navigation and page loading
- Form interactions and button clicks
- Responsive design validation
- JavaScript error detection

### 🧩 Module System Tests  
```bash
python tests/run_tests.py unit
```
- Module loading and discovery
- Configuration validation
- Event routing and handling
- Module interaction workflows

### ⚡ Performance Tests
```bash
python tests/run_tests.py performance
```
- API response times
- Event processing throughput
- Memory usage stability
- Concurrent request handling

### 🔄 Integration Tests
```bash
python tests/run_tests.py integration
```
- Complete user workflows
- Frontend-to-backend communication
- Configuration persistence
- Multi-user scenarios

### 🤖 CI/CD Tests
```bash
python tests/run_tests.py ci
```
- Headless UI tests suitable for automation
- Excludes slow-running tests
- Optimized for continuous integration

## Test Files

| File | Purpose | Key Features |
|------|---------|--------------|
| `conftest.py` | Test configuration and fixtures | Browser setup, test server, mock data |
| `test_api_endpoints.py` | API endpoint testing | HTTP requests, response validation |
| `test_frontend_ui.py` | UI testing with Playwright | Page interactions, navigation |
| `test_module_system.py` | Module system testing | Loading, configuration, events |
| `test_performance.py` | Performance benchmarks | Response times, throughput |
| `test_integration.py` | End-to-end workflows | Complete user scenarios |

## Running Individual Tests

### Run Specific Test File
```bash
pytest tests/test_api_endpoints.py -v
```

### Run Specific Test Method
```bash
pytest tests/test_frontend_ui.py::TestFrontendUI::test_homepage_loads -v
```

### Run with Specific Markers
```bash
# Run only fast tests
pytest tests/ -m "not slow" -v

# Run only API tests
pytest tests/ -m "api" -v
```

## Test Configuration

### Environment Variables
- `INTERACTION_CONFIG_DIR` - Test configuration directory
- `PYTEST_HEADLESS` - Run browser tests in headless mode

### Command Line Options
```bash
# Run with visible browser (default: headless)
pytest tests/test_frontend_ui.py --headed

# Stop on first failure
pytest tests/ -x

# Run tests in parallel
pytest tests/ -n auto
```

## Writing New Tests

### 1. API Endpoint Test
```python
@pytest.mark.asyncio
async def test_new_endpoint(self, app_server, http_client):
    """Test a new API endpoint."""
    response = await http_client.get(f"{app_server}/new_endpoint")
    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data
```

### 2. Frontend UI Test
```python
@pytest.mark.asyncio
async def test_new_ui_feature(self, page: Page, app_server):
    """Test a new UI feature."""
    await page.goto(f"{app_server}/new_page")
    await page.wait_for_load_state("networkidle")
    
    await expect(page.locator('text=New Feature')).to_be_visible()
    await page.click('button:text("Action")')
    
    # Verify result
    await expect(page.locator('text=Success')).to_be_visible()
```

### 3. Module System Test
```python
def test_new_module_feature(self):
    """Test new module functionality."""
    from modules.new_module import NewModule
    
    module = NewModule("test_config")
    module.configure({"param": "value"})
    
    # Test functionality
    result = module.process_event({"type": "test"})
    assert result["status"] == "success"
```

## Fixtures Available

### Test Infrastructure
- `app_server` - Running application server
- `http_client` - HTTP client for API calls
- `browser` - Playwright browser instance
- `page` - Browser page for UI tests

### Test Data
- `sample_interaction` - Example interaction configuration
- `sample_audio_file` - Test audio file
- `mock_modules` - Mock module definitions
- `test_config_dir` - Temporary config directory

## Best Practices

### ✅ Do
- Test both success and error cases
- Use descriptive test names
- Keep tests independent and isolated
- Mock external dependencies
- Test actual user workflows
- Include performance assertions

### ❌ Don't
- Create dependencies between tests
- Use hardcoded timeouts (use proper waits)
- Test implementation details
- Create temporary files without cleanup
- Skip error handling tests

## Troubleshooting

### Browser Tests Failing
```bash
# Install/update browsers
playwright install chromium

# Run with visible browser for debugging
pytest tests/test_frontend_ui.py --headed --slowmo=1000
```

### Server Not Starting
```bash
# Check if port is in use
netstat -tulpn | grep 8899

# Kill existing processes
pkill -f "python main.py"
```

### Import Errors
```bash
# Ensure you're in the project root
cd /path/to/interaction-framework

# Install dependencies
pip install -r requirements.txt
```

### Slow Tests
```bash
# Run only fast tests
pytest tests/ -m "not slow"

# Run with multiple workers
pytest tests/ -n 4
```

## Continuous Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: |
          pip install -r requirements.txt
          playwright install chromium
          python tests/run_tests.py ci
```

### Pre-commit Hook
```bash
# Add to .git/hooks/pre-commit
#!/bin/bash
python tests/run_tests.py quick
if [ $? -ne 0 ]; then
    echo "Tests failed! Commit aborted."
    exit 1
fi
```

## Coverage Reporting

```bash
# Install coverage
pip install pytest-cov

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Performance Monitoring

The test suite includes performance benchmarks to ensure:
- API responses < 1 second
- Event processing > 1000 events/sec  
- Memory usage stays stable under load
- UI interactions complete quickly

Run performance tests regularly to catch regressions:
```bash
python tests/run_tests.py performance
```

---

## Support

For questions or issues with the test suite:
1. Check this README for common solutions
2. Review test output for specific error messages
3. Run tests with `-v` flag for verbose output
4. Use `--pdb` flag to drop into debugger on failure