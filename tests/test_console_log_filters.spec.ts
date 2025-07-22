import { test, expect } from '@playwright/test';
import axios from 'axios';

const FRONTEND_URL = 'http://localhost:5173/console';
const BACKEND_LOG_API = 'http://localhost:8000/api/test_log';

const TEST_LOGS = [
  { message: 'System log test', module: 'system', category: 'system' },
  { message: 'Audio log test', module: 'audio_output', category: 'audio' },
  { message: 'OSC log test', module: 'osc_output', category: 'osc' },
  { message: 'Serial log test', module: 'serial_input', category: 'serial' },
  { message: 'DMX log test', module: 'dmx_output', category: 'dmx' },
];

test.describe('Console Log Filters UI Integration', () => {
  test.beforeAll(async () => {
    // Send test logs to the backend (assumes backend endpoint exists for testing)
    for (const log of TEST_LOGS) {
      await axios.post(BACKEND_LOG_API, log);
    }
  });

  test('should display and filter logs by category', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    // Wait for all test logs to appear
    for (const log of TEST_LOGS) {
      await expect(page.locator(`span:has-text("${log.message}")`)).toHaveCount(1, { timeout: 5000 });
    }
    // Test each filter
    for (const log of TEST_LOGS) {
      // Open filter dropdown and select category
      await page.click('label:has-text("Log Category") + div');
      await page.click(`li:has-text("${log.category.charAt(0).toUpperCase() + log.category.slice(1)}")`);
      // Only the log for this category should be visible
      await expect(page.locator(`span:has-text("${log.message}")`)).toBeVisible();
      // All other logs should not be visible
      for (const other of TEST_LOGS) {
        if (other.category !== log.category) {
          await expect(page.locator(`span:has-text("${other.message}")`)).toHaveCount(0);
        }
      }
    }
    // Reset filter to 'All Logs' and check all logs are visible
    await page.click('label:has-text("Log Category") + div');
    await page.click('li:has-text("All Logs")');
    for (const log of TEST_LOGS) {
      await expect(page.locator(`span:has-text("${log.message}")`)).toBeVisible();
    }
  });
}); 