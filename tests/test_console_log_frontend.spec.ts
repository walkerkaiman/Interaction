import { test, expect } from '@playwright/test';

test.describe('Console Log UI Integration', () => {
  test('should display a console_log message from the backend', async ({ page }) => {
    // Go to the frontend Console page
    await page.goto('http://localhost:5173/console');

    // Wait for the test log message to appear in the UI
    const logSelector = 'span:has-text("Test log: WebSocket client connected!")';
    await expect(page.locator(logSelector)).toHaveCount(1, { timeout: 5000 });

    // Optionally, check that the log has the correct module and category
    await expect(page.locator('span:has-text("[system]")')).toHaveCount(1);
    await expect(page.locator('span:has-text("[SYSTEM]")')).toHaveCount(1);
  });
}); 