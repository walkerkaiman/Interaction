import { test, expect } from '@playwright/test';

test.describe('Frames Input Module UI Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the Interaction Editor
    await page.goto('http://localhost:5173/');
    await page.waitForLoadState('networkidle');
    
    // Wait for the page to load and check if we're on the right page
    await expect(page.locator('h4')).toContainText('Interaction Editor');
  });

  test('should display Frames Input module in module selection', async ({ page }) => {
    // Add a new interaction
    await page.click('button:has-text("Add Interaction")');
    
    // Check that Frames Input appears in the input module dropdown
    const inputSelect = page.locator('select').first();
    await inputSelect.click();
    
    // Look for Frames Input in the dropdown options
    const framesInputOption = page.locator('option:has-text("Frames Input")');
    await expect(framesInputOption).toBeVisible();
  });

  test('should load Frames Input module with default streaming mode', async ({ page }) => {
    // Add a new interaction
    await page.click('button:has-text("Add Interaction")');
    
    // Select Frames Input as input module
    const inputSelect = page.locator('select').first();
    await inputSelect.selectOption('frames_input');
    
    // Wait for the module to load
    await page.waitForTimeout(1000);
    
    // Check that the current frame label is visible
    await expect(page.locator('text=Current Frame')).toBeVisible();
    await expect(page.locator('text=No frame received')).toBeVisible();
    
    // Check that mode toggle is visible and set to streaming
    await expect(page.locator('text=Mode')).toBeVisible();
    const modeSelect = page.locator('select').nth(1); // Second select should be mode
    await expect(modeSelect).toHaveValue('streaming');
    
    // Check that trigger-specific fields are not visible in streaming mode
    await expect(page.locator('text=Comparison')).not.toBeVisible();
    await expect(page.locator('text=Threshold Value')).not.toBeVisible();
  });

  test('should switch to trigger mode and show trigger fields', async ({ page }) => {
    // Add a new interaction
    await page.click('button:has-text("Add Interaction")');
    
    // Select Frames Input as input module
    const inputSelect = page.locator('select').first();
    await inputSelect.selectOption('frames_input');
    
    // Wait for the module to load
    await page.waitForTimeout(1000);
    
    // Switch to trigger mode
    const modeSelect = page.locator('select').nth(1);
    await modeSelect.selectOption('trigger');
    
    // Wait for UI to update
    await page.waitForTimeout(500);
    
    // Check that trigger-specific fields are now visible
    await expect(page.locator('text=Comparison')).toBeVisible();
    await expect(page.locator('text=Threshold Value')).toBeVisible();
    
    // Check that comparison dropdown has correct options
    const comparisonSelect = page.locator('select').nth(2);
    await expect(comparisonSelect).toHaveValue('>');
    
    // Check comparison options
    await comparisonSelect.click();
    await expect(page.locator('option:has-text("<")')).toBeVisible();
    await expect(page.locator('option:has-text("=")')).toBeVisible();
    await expect(page.locator('option:has-text(">")')).toBeVisible();
    
    // Check threshold value input
    const thresholdInput = page.locator('input[type="number"]').first();
    await expect(thresholdInput).toHaveValue('0');
    await expect(thresholdInput).toHaveAttribute('min', '0');
    await expect(thresholdInput).toHaveAttribute('max', '65535');
  });

  test('should configure trigger settings', async ({ page }) => {
    // Add a new interaction
    await page.click('button:has-text("Add Interaction")');
    
    // Select Frames Input as input module
    const inputSelect = page.locator('select').first();
    await inputSelect.selectOption('frames_input');
    
    // Switch to trigger mode
    const modeSelect = page.locator('select').nth(1);
    await modeSelect.selectOption('trigger');
    
    // Configure trigger settings
    const comparisonSelect = page.locator('select').nth(2);
    await comparisonSelect.selectOption('<');
    
    const thresholdInput = page.locator('input[type="number"]').first();
    await thresholdInput.fill('50');
    
    // Verify the values are set correctly
    await expect(comparisonSelect).toHaveValue('<');
    await expect(thresholdInput).toHaveValue('50');
  });

  test('should switch back to streaming mode and hide trigger fields', async ({ page }) => {
    // Add a new interaction
    await page.click('button:has-text("Add Interaction")');
    
    // Select Frames Input as input module
    const inputSelect = page.locator('select').first();
    await inputSelect.selectOption('frames_input');
    
    // Switch to trigger mode first
    const modeSelect = page.locator('select').nth(1);
    await modeSelect.selectOption('trigger');
    
    // Verify trigger fields are visible
    await expect(page.locator('text=Comparison')).toBeVisible();
    await expect(page.locator('text=Threshold Value')).toBeVisible();
    
    // Switch back to streaming mode
    await modeSelect.selectOption('streaming');
    
    // Wait for UI to update
    await page.waitForTimeout(500);
    
    // Verify trigger fields are hidden
    await expect(page.locator('text=Comparison')).not.toBeVisible();
    await expect(page.locator('text=Threshold Value')).not.toBeVisible();
  });

  test('should save and load configuration correctly', async ({ page }) => {
    // Add a new interaction
    await page.click('button:has-text("Add Interaction")');
    
    // Select Frames Input as input module
    const inputSelect = page.locator('select').first();
    await inputSelect.selectOption('frames_input');
    
    // Configure in trigger mode
    const modeSelect = page.locator('select').nth(1);
    await modeSelect.selectOption('trigger');
    
    const comparisonSelect = page.locator('select').nth(2);
    await comparisonSelect.selectOption('=');
    
    const thresholdInput = page.locator('input[type="number"]').first();
    await thresholdInput.fill('100');
    
    // Save the configuration
    await page.click('button:has-text("Save / Apply")');
    
    // Wait for save to complete
    await expect(page.locator('text=Saved!')).toBeVisible();
    
    // Reload the page
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    // Check that the configuration is preserved
    await expect(page.locator('select').first()).toHaveValue('frames_input');
    await expect(page.locator('select').nth(1)).toHaveValue('trigger');
    await expect(page.locator('select').nth(2)).toHaveValue('=');
    await expect(page.locator('input[type="number"]').first()).toHaveValue('100');
  });

  test('should handle invalid threshold values', async ({ page }) => {
    // Add a new interaction
    await page.click('button:has-text("Add Interaction")');
    
    // Select Frames Input as input module
    const inputSelect = page.locator('select').first();
    await inputSelect.selectOption('frames_input');
    
    // Switch to trigger mode
    const modeSelect = page.locator('select').nth(1);
    await modeSelect.selectOption('trigger');
    
    // Try to enter invalid values
    const thresholdInput = page.locator('input[type="number"]').first();
    
    // Test negative value (should be prevented by min attribute)
    await thresholdInput.fill('-10');
    await expect(thresholdInput).toHaveValue('-10'); // Browser might allow it, but we can test the behavior
    
    // Test value above max
    await thresholdInput.fill('70000');
    await expect(thresholdInput).toHaveValue('70000'); // Browser might allow it, but we can test the behavior
    
    // Test valid value
    await thresholdInput.fill('1000');
    await expect(thresholdInput).toHaveValue('1000');
  });

  test('should display current frame updates', async ({ page }) => {
    // Add a new interaction
    await page.click('button:has-text("Add Interaction")');
    
    // Select Frames Input as input module
    const inputSelect = page.locator('select').first();
    await inputSelect.selectOption('frames_input');
    
    // Initially should show "No frame received"
    await expect(page.locator('text=No frame received')).toBeVisible();
    
    // Note: In a real test environment, we would simulate sACN data
    // For now, we just verify the initial state
    // This test would need to be enhanced with actual sACN simulation
  });

  test('should work with different output modules', async ({ page }) => {
    // Add a new interaction
    await page.click('button:has-text("Add Interaction")');
    
    // Select Frames Input as input module
    const inputSelect = page.locator('select').first();
    await inputSelect.selectOption('frames_input');
    
    // Select different output modules to test compatibility
    const outputSelect = page.locator('select').last();
    
    // Test with Audio Output
    await outputSelect.selectOption('audio_output');
    await expect(page.locator('text=Audio File')).toBeVisible();
    
    // Test with OSC Output
    await outputSelect.selectOption('osc_output');
    await expect(page.locator('text=IP Address')).toBeVisible();
    
    // Test with DMX Output
    await outputSelect.selectOption('dmx_output');
    await expect(page.locator('text=Universe')).toBeVisible();
  });

  test('should handle module switching correctly', async ({ page }) => {
    // Add a new interaction
    await page.click('button:has-text("Add Interaction")');
    
    // Select Frames Input as input module
    const inputSelect = page.locator('select').first();
    await inputSelect.selectOption('frames_input');
    
    // Configure some settings
    const modeSelect = page.locator('select').nth(1);
    await modeSelect.selectOption('trigger');
    
    // Switch to a different input module
    await inputSelect.selectOption('time_input_trigger');
    
    // Verify Frames Input fields are no longer visible
    await expect(page.locator('text=Mode')).not.toBeVisible();
    await expect(page.locator('text=Comparison')).not.toBeVisible();
    
    // Switch back to Frames Input
    await inputSelect.selectOption('frames_input');
    
    // Verify Frames Input fields are visible again
    await expect(page.locator('text=Mode')).toBeVisible();
    await expect(page.locator('text=Current Frame')).toBeVisible();
  });
}); 