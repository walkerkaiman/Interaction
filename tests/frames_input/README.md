# Frames Input Module Tests

This directory contains comprehensive tests for the unified Frames Input module, including backend unit tests and UI tests with Playwright.

## Test Structure

- `test_frames_input_backend.py` - Backend unit tests using Python's unittest framework
- `test_frames_input_ui.spec.ts` - UI tests using Playwright
- `playwright.config.ts` - Playwright configuration
- `run_tests.py` - Comprehensive test runner script
- `package.json` - Node.js dependencies for Playwright

## Running Tests

### Quick Start

Run all tests with the comprehensive test runner:

```bash
python run_tests.py
```

This will:
1. Run backend unit tests
2. Install Playwright if needed
3. Run UI tests
4. Run integration tests
5. Generate a test report

### Individual Test Suites

#### Backend Tests Only

```bash
python -m unittest test_frames_input_backend.TestFramesInputModule -v
```

#### UI Tests Only

First, install dependencies:
```bash
npm install
npx playwright install
```

Then run UI tests:
```bash
npx playwright test
```

#### UI Tests with Browser

```bash
npx playwright test --headed
```

#### UI Tests in Debug Mode

```bash
npx playwright test --debug
```

## Test Coverage

### Backend Tests

The backend tests cover:

- ✅ Module initialization (streaming and trigger modes)
- ✅ Manifest loading and validation
- ✅ Frame number extraction from DMX data
- ✅ Trigger condition checking logic
- ✅ Event emission in both modes
- ✅ State tracking to prevent duplicate triggers
- ✅ Configuration updates
- ✅ Display data generation
- ✅ Error handling (sACN library unavailable)
- ✅ sACN receiver start/stop lifecycle

### UI Tests

The UI tests cover:

- ✅ Module selection in dropdown
- ✅ Default streaming mode loading
- ✅ Mode switching (streaming ↔ trigger)
- ✅ Conditional field visibility
- ✅ Trigger configuration (comparison operators, threshold values)
- ✅ Configuration persistence
- ✅ Input validation
- ✅ Module switching behavior
- ✅ Compatibility with different output modules

### Integration Tests

The integration tests verify:

- ✅ Module loads correctly in the main system
- ✅ Manifest integration
- ✅ Configuration handling

## Test Requirements

### Backend Requirements

- Python 3.8+
- `sacn` library (optional, tests handle missing library gracefully)
- `unittest` (built-in)

### UI Requirements

- Node.js 18+
- Playwright
- Running frontend server (tests will start it automatically)

## Test Configuration

### Playwright Configuration

The Playwright tests are configured to:

- Run against Chrome, Firefox, and Safari
- Take screenshots on failure
- Record videos on failure
- Collect traces for debugging
- Automatically start the frontend dev server

### Backend Test Configuration

Backend tests use:

- Mock objects for external dependencies
- Isolated test cases
- Comprehensive assertion coverage
- Error condition testing

## Debugging Tests

### Backend Test Debugging

To debug backend tests, you can run individual test methods:

```bash
python -m unittest test_frames_input_backend.TestFramesInputModule.test_frame_number_extraction -v
```

### UI Test Debugging

To debug UI tests:

1. Run in headed mode to see the browser:
   ```bash
   npx playwright test --headed
   ```

2. Run in debug mode to step through:
   ```bash
   npx playwright test --debug
   ```

3. View test reports:
   ```bash
   npx playwright show-report
   ```

## Adding New Tests

### Adding Backend Tests

1. Add new test methods to `TestFramesInputModule` class
2. Follow the naming convention: `test_<feature_name>`
3. Use descriptive docstrings
4. Include both positive and negative test cases

### Adding UI Tests

1. Add new test functions to the test suite
2. Use descriptive test names
3. Include proper waits and assertions
4. Test both success and failure scenarios

## Continuous Integration

The tests are designed to work in CI environments:

- Backend tests run without external dependencies
- UI tests can run in headless mode
- All tests provide clear pass/fail output
- Test runner returns appropriate exit codes

## Troubleshooting

### Common Issues

1. **Playwright not found**: Run `npm install` and `npx playwright install`
2. **Frontend server not starting**: Ensure port 5173 is available
3. **sACN library missing**: Tests handle this gracefully, but install with `pip install sacn` for full functionality
4. **Test timeouts**: Increase timeout values in Playwright config if needed

### Getting Help

- Check the test output for specific error messages
- Run tests individually to isolate issues
- Use debug mode for UI tests to see what's happening
- Review the test logs for detailed information 