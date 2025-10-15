/**
 * End-to-end tests for NightLoom MVP bootstrap flow.
 * 
 * Tests the complete user journey from landing page through keyword selection
 * using Playwright. Implements Fail First testing strategy.
 */

import { test, expect } from '@playwright/test';

test.describe('NightLoom Bootstrap Flow', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to the main page
    await page.goto('/');
  });

  test('should complete bootstrap flow with suggested keyword', async ({ page }) => {
    // Wait for bootstrap to complete and keywords to load
    await expect(page.locator('[data-testid="keyword-candidates"]')).toBeVisible({ timeout: 10000 });
    
    // Verify initial state
    await expect(page.locator('[data-testid="initial-character"]')).toBeVisible();
    await expect(page.locator('[data-testid="keyword-candidates"] button')).toHaveCount(4);
    
    // Verify keyword candidates are displayed
    const keywordButtons = page.locator('[data-testid="keyword-candidates"] button');
    for (let i = 0; i < 4; i++) {
      const button = keywordButtons.nth(i);
      await expect(button).toBeVisible();
      await expect(button).toHaveText(/^.+$/); // Should have non-empty text
    }
    
    // Select first suggested keyword
    const firstKeyword = keywordButtons.first();
    const selectedKeywordText = await firstKeyword.textContent();
    await firstKeyword.click();
    
    // Should navigate to first scene
    await expect(page.locator('[data-testid="scene-narrative"]')).toBeVisible({ timeout: 5000 });
    
    // Verify scene structure
    await expect(page.locator('[data-testid="scene-index"]')).toHaveText('1');
    await expect(page.locator('[data-testid="scene-narrative"]')).toContainText(selectedKeywordText || '');
    await expect(page.locator('[data-testid="choice-options"] button')).toHaveCount(4);
    
    // Verify progress indicator
    await expect(page.locator('[data-testid="progress-indicator"]')).toBeVisible();
    await expect(page.locator('[data-testid="progress-text"]')).toContainText('1/4');
  });

  test('should complete bootstrap flow with custom keyword', async ({ page }) => {
    // Wait for bootstrap to complete
    await expect(page.locator('[data-testid="keyword-candidates"]')).toBeVisible({ timeout: 10000 });
    
    // Enter custom keyword
    const customInput = page.locator('[data-testid="custom-keyword-input"]');
    await expect(customInput).toBeVisible();
    
    const customKeyword = 'テスト';
    await customInput.fill(customKeyword);
    
    // Submit custom keyword
    const submitButton = page.locator('[data-testid="submit-custom-keyword"]');
    await expect(submitButton).toBeEnabled();
    await submitButton.click();
    
    // Should navigate to first scene with custom keyword
    await expect(page.locator('[data-testid="scene-narrative"]')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('[data-testid="scene-narrative"]')).toContainText(customKeyword);
  });

  test('should handle bootstrap loading states', async ({ page }) => {
    // Verify loading state is shown initially
    await expect(page.locator('[data-testid="bootstrap-loading"]')).toBeVisible();
    
    // Loading should disappear when bootstrap completes
    await expect(page.locator('[data-testid="bootstrap-loading"]')).toBeHidden({ timeout: 10000 });
    
    // Keyword selection should be available
    await expect(page.locator('[data-testid="keyword-candidates"]')).toBeVisible();
  });

  test('should validate custom keyword input', async ({ page }) => {
    await expect(page.locator('[data-testid="keyword-candidates"]')).toBeVisible({ timeout: 10000 });
    
    const customInput = page.locator('[data-testid="custom-keyword-input"]');
    const submitButton = page.locator('[data-testid="submit-custom-keyword"]');
    
    // Test empty input
    await customInput.fill('');
    await expect(submitButton).toBeDisabled();
    
    // Test valid input
    await customInput.fill('有効');
    await expect(submitButton).toBeEnabled();
    
    // Test too long input (over 20 characters)
    const longKeyword = 'あ'.repeat(21);
    await customInput.fill(longKeyword);
    await expect(submitButton).toBeDisabled();
    
    // Test valid length boundary (exactly 20 characters)
    const boundaryKeyword = 'あ'.repeat(20);
    await customInput.fill(boundaryKeyword);
    await expect(submitButton).toBeEnabled();
  });

  test('should handle network errors gracefully', async ({ page, context }) => {
    // Intercept API calls and simulate network failure
    await page.route('/api/sessions/start', route => {
      route.abort('failed');
    });
    
    // Reload page to trigger bootstrap with failure
    await page.reload();
    
    // Should show error state
    await expect(page.locator('[data-testid="bootstrap-error"]')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
    
    // Remove network failure and retry
    await page.unroute('/api/sessions/start');
    await page.locator('[data-testid="retry-button"]').click();
    
    // Should recover and show keyword selection
    await expect(page.locator('[data-testid="keyword-candidates"]')).toBeVisible({ timeout: 10000 });
  });

  test('should maintain theme consistency', async ({ page }) => {
    await expect(page.locator('[data-testid="keyword-candidates"]')).toBeVisible({ timeout: 10000 });
    
    // Verify theme is applied
    const themeContainer = page.locator('[data-testid="theme-container"]');
    await expect(themeContainer).toHaveAttribute('data-theme', /^(serene|adventure|focus|fallback)$/);
    
    // Select keyword and verify theme persists
    await page.locator('[data-testid="keyword-candidates"] button').first().click();
    
    await expect(page.locator('[data-testid="scene-container"]')).toBeVisible({ timeout: 5000 });
    const sceneTheme = page.locator('[data-testid="scene-container"]');
    
    // Theme should be consistent
    const initialTheme = await themeContainer.getAttribute('data-theme');
    const sceneThemeValue = await sceneTheme.getAttribute('data-theme');
    expect(sceneThemeValue).toBe(initialTheme);
  });

  test('should meet performance requirements', async ({ page }) => {
    const startTime = Date.now();
    
    // Wait for bootstrap to complete
    await expect(page.locator('[data-testid="keyword-candidates"]')).toBeVisible({ timeout: 10000 });
    
    const endTime = Date.now();
    const bootstrapTime = endTime - startTime;
    
    // Should meet p95 ≤ 800ms requirement (allowing some buffer for E2E overhead)
    expect(bootstrapTime).toBeLessThan(2000); // More lenient for E2E tests
    
    // Verify no performance console errors
    const logs = await page.evaluate(() => {
      return (window as any).performanceLogs || [];
    });
    
    // Check for any performance warnings
    const performanceErrors = logs.filter((log: any) => 
      log.level === 'error' && log.message.includes('performance')
    );
    expect(performanceErrors).toHaveLength(0);
  });

  test('should support keyboard navigation', async ({ page }) => {
    await expect(page.locator('[data-testid="keyword-candidates"]')).toBeVisible({ timeout: 10000 });
    
    // Test tab navigation through keyword buttons
    const firstButton = page.locator('[data-testid="keyword-candidates"] button').first();
    await firstButton.focus();
    
    // Should be able to navigate with arrow keys
    await page.keyboard.press('ArrowRight');
    const secondButton = page.locator('[data-testid="keyword-candidates"] button').nth(1);
    await expect(secondButton).toBeFocused();
    
    // Should be able to select with Enter key
    await page.keyboard.press('Enter');
    
    // Should navigate to scene
    await expect(page.locator('[data-testid="scene-narrative"]')).toBeVisible({ timeout: 5000 });
  });

  test('should handle fallback scenarios', async ({ page }) => {
    // Intercept bootstrap API to simulate fallback response
    await page.route('/api/sessions/start', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          sessionId: '550e8400-e29b-41d4-a716-446655440000',
          axes: [
            {
              id: 'logic_emotion',
              name: 'Logic vs Emotion',
              description: 'Test axis',
              direction: '論理的 ⟷ 感情的'
            }
          ],
          keywordCandidates: ['希望', '挑戦', '成長', '発見'],
          initialCharacter: 'あ',
          themeId: 'fallback',
          fallbackUsed: true
        })
      });
    });
    
    await page.reload();
    
    // Should still work with fallback data
    await expect(page.locator('[data-testid="keyword-candidates"]')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('[data-testid="keyword-candidates"] button')).toHaveCount(4);
    
    // Verify fallback theme is applied
    const themeContainer = page.locator('[data-testid="theme-container"]');
    await expect(themeContainer).toHaveAttribute('data-theme', 'fallback');
    
    // Should be able to proceed normally
    await page.locator('[data-testid="keyword-candidates"] button').first().click();
    await expect(page.locator('[data-testid="scene-narrative"]')).toBeVisible({ timeout: 5000 });
  });

  test('should display session ID for debugging', async ({ page }) => {
    await expect(page.locator('[data-testid="keyword-candidates"]')).toBeVisible({ timeout: 10000 });
    
    // In development mode, session ID should be available for debugging
    const sessionInfo = page.locator('[data-testid="session-debug-info"]');
    if (await sessionInfo.isVisible()) {
      const sessionId = await sessionInfo.getAttribute('data-session-id');
      expect(sessionId).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i);
    }
  });

});

test.describe('Bootstrap Accessibility', () => {
  
  test('should meet accessibility standards', async ({ page }) => {
    await expect(page.locator('[data-testid="keyword-candidates"]')).toBeVisible({ timeout: 10000 });
    
    // Check for proper ARIA labels
    await expect(page.locator('[data-testid="keyword-candidates"]')).toHaveAttribute('role', 'group');
    await expect(page.locator('[data-testid="keyword-candidates"]')).toHaveAttribute('aria-label');
    
    // Check button accessibility
    const buttons = page.locator('[data-testid="keyword-candidates"] button');
    for (let i = 0; i < 4; i++) {
      const button = buttons.nth(i);
      await expect(button).toHaveAttribute('aria-label');
      await expect(button).toHaveAttribute('type', 'button');
    }
    
    // Check custom input accessibility
    const customInput = page.locator('[data-testid="custom-keyword-input"]');
    await expect(customInput).toHaveAttribute('aria-label');
    await expect(customInput).toHaveAttribute('maxlength', '20');
  });

  test('should support screen reader announcements', async ({ page }) => {
    await expect(page.locator('[data-testid="keyword-candidates"]')).toBeVisible({ timeout: 10000 });
    
    // Check for aria-live regions for status updates
    await expect(page.locator('[aria-live="polite"]')).toBeVisible();
    
    // Verify loading announcements
    if (await page.locator('[data-testid="bootstrap-loading"]').isVisible()) {
      const loadingText = await page.locator('[data-testid="bootstrap-loading"]').textContent();
      expect(loadingText).toContain('読み込み中');
    }
  });

});
