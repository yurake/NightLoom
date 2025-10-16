
/**
 * End-to-End tests for NightLoom MVP 4-scene completion flow.
 * 
 * Tests the complete user journey through all 4 scenes from start to finish.
 * Implements T033 requirements with Fail First testing strategy.
 */

import { test, expect, Page } from '@playwright/test';

test.describe('4-Scene Completion Flow E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the main application
    await page.goto('/');
  });

  test('should complete full 4-scene journey with choice selections', async ({ page }) => {
    // Step 1: Bootstrap session and select keyword
    await expect(page.locator('[data-testid="loading-indicator"]')).toBeVisible();
    
    // Wait for keyword candidates to appear
    await expect(page.locator('[data-testid="keyword-candidate"]').first()).toBeVisible();
    
    // Select first keyword candidate
    const firstKeyword = page.locator('[data-testid="keyword-candidate"]').first();
    const keywordText = await firstKeyword.textContent();
    await firstKeyword.click();
    
    // Step 2: Complete Scene 1
    await expect(page.locator('[data-testid="scene-narrative"]')).toBeVisible();
    await expect(page.locator('[data-testid="scene-index"]')).toContainText('1');
    
    // Verify scene 1 content
    const scene1Narrative = page.locator('[data-testid="scene-narrative"]');
    await expect(scene1Narrative).toContainText(keywordText || '');
    
    // Verify 4 choices are available
    const scene1Choices = page.locator('[data-testid="choice-option"]');
    await expect(scene1Choices).toHaveCount(4);
    
    // Select first choice in scene 1
    await scene1Choices.first().click();
    
    // Wait for scene transition
    await expect(page.locator('[data-testid="loading-indicator"]')).toBeVisible();
    
    // Step 3: Complete Scene 2
    await expect(page.locator('[data-testid="scene-index"]')).toContainText('2');
    await expect(page.locator('[data-testid="scene-narrative"]')).toBeVisible();
    
    // Verify progress indicator shows 2/4
    await expect(page.locator('[data-testid="progress-indicator"]')).toContainText('2');
    
    // Select second choice in scene 2
    const scene2Choices = page.locator('[data-testid="choice-option"]');
    await expect(scene2Choices).toHaveCount(4);
    await scene2Choices.nth(1).click();
    
    // Step 4: Complete Scene 3
    await expect(page.locator('[data-testid="scene-index"]')).toContainText('3');
    await expect(page.locator('[data-testid="progress-indicator"]')).toContainText('3');
    
    // Select third choice in scene 3
    const scene3Choices = page.locator('[data-testid="choice-option"]');
    await scene3Choices.nth(2).click();
    
    // Step 5: Complete Scene 4
    await expect(page.locator('[data-testid="scene-index"]')).toContainText('4');
    await expect(page.locator('[data-testid="progress-indicator"]')).toContainText('4');
    
    // Select fourth choice in scene 4
    const scene4Choices = page.locator('[data-testid="choice-option"]');
    await scene4Choices.nth(3).click();
    
    // Step 6: Verify completion and navigation to results
    // After scene 4, should navigate to results page or show completion
    await expect(page.locator('[data-testid="completion-indicator"]')).toBeVisible({ timeout: 10000 });
    
    // Verify we've progressed through all scenes
    // This could be a redirect to results page or completion state
    const currentUrl = page.url();
    expect(currentUrl).toMatch(/result|complete|finish/);
  });

  test('should display correct progress indicators throughout journey', async ({ page }) => {
    // Complete bootstrap
    await page.locator('[data-testid="keyword-candidate"]').first().click();
    
    // Scene 1: Progress should be 1/4 (25%)
    await expect(page.locator('[data-testid="progress-bar"]')).toHaveAttribute('aria-valuenow', '25');
    await expect(page.locator('[data-testid="progress-text"]')).toContainText('1 / 4');
    
    // Progress to scene 2
    await page.locator('[data-testid="choice-option"]').first().click();
    
    // Scene 2: Progress should be 2/4 (50%)
    await expect(page.locator('[data-testid="progress-bar"]')).toHaveAttribute('aria-valuenow', '50');
    await expect(page.locator('[data-testid="progress-text"]')).toContainText('2 / 4');
    
    // Progress to scene 3
    await page.locator('[data-testid="choice-option"]').first().click();
    
    // Scene 3: Progress should be 3/4 (75%)
    await expect(page.locator('[data-testid="progress-bar"]')).toHaveAttribute('aria-valuenow', '75');
    await expect(page.locator('[data-testid="progress-text"]')).toContainText('3 / 4');
    
    // Progress to scene 4
    await page.locator('[data-testid="choice-option"]').first().click();
    
    // Scene 4: Progress should be 4/4 (100%)
    await expect(page.locator('[data-testid="progress-bar"]')).toHaveAttribute('aria-valuenow', '100');
    await expect(page.locator('[data-testid="progress-text"]')).toContainText('4 / 4');
  });

  test('should maintain theme consistency across all scenes', async ({ page }) => {
    // Complete bootstrap and note the theme
    await page.locator('[data-testid="keyword-candidate"]').first().click();
    
    // Get theme from first scene
    const themeClass = await page.locator('[data-testid="theme-container"]').getAttribute('class');
    const themeId = themeClass?.match(/theme-(\w+)/)?.[1];
    
    // Progress through all scenes and verify theme consistency
    for (let sceneIndex = 1; sceneIndex <= 4; sceneIndex++) {
      await expect(page.locator('[data-testid="theme-container"]')).toHaveClass(new RegExp(`theme-${themeId}`));
      
      // Verify theme-specific elements are present
      await expect(page.locator(`[data-theme="${themeId}"]`)).toBeVisible();
      
      if (sceneIndex < 4) {
        // Move to next scene
        await page.locator('[data-testid="choice-option"]').first().click();
      }
    }
  });

  test('should handle network failures during scene progression gracefully', async ({ page }) => {
    // Complete bootstrap
    await page.locator('[data-testid="keyword-candidate"]').first().click();
    
    // Simulate network failure during choice submission
    await page.route('**/api/sessions/*/scenes/*/choice', async route => {
      if (route.request().method() === 'POST') {
        // First request fails
        await route.abort('failed');
      }
    });
    
    // Try to submit choice
    await page.locator('[data-testid="choice-option"]').first().click();
    
    // Should show error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toContainText(/ネットワーク|エラー|失敗/);
    
    // Should show retry option
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
    
    // Remove network failure and retry
    await page.unroute('**/api/sessions/*/scenes/*/choice');
    await page.locator('[data-testid="retry-button"]').click();
    
    // Should successfully progress to next scene
    await expect(page.locator('[data-testid="scene-index"]')).toContainText('2');
  });

  test('should prevent double submission of choices', async ({ page }) => {
    // Complete bootstrap
    await page.locator('[data-testid="keyword-candidate"]').first().click();
    
    // Track choice submission requests
    const choiceRequests: string[] = [];
    page.on('request', request => {
      if (request.url().includes('/choice') && request.method() === 'POST') {
        choiceRequests.push(request.url());
      }
    });
    
    // Rapidly click the same choice multiple times
    const firstChoice = page.locator('[data-testid="choice-option"]').first();
    await firstChoice.click();
    await firstChoice.click(); // Second click should be ignored
    await firstChoice.click(); // Third click should be ignored
    
    // Wait for any pending requests
    await page.waitForTimeout(1000);
    
    // Should only have one choice submission request
    expect(choiceRequests).toHaveLength(1);
    
    // Should successfully progress to scene 2
    await expect(page.locator('[data-testid="scene-index"]')).toContainText('2');
  });

  test('should meet performance requirements for scene transitions', async ({ page }) => {
    // Complete bootstrap
    await page.locator('[data-testid="keyword-candidate"]').first().click();
    
    // Measure scene transition times
    const transitionTimes: number[] = [];
    
    for (let sceneIndex = 1; sceneIndex < 4; sceneIndex++) {
      const startTime = Date.now();
      
      // Submit choice
      await page.locator('[data-testid="choice-option"]').first().click();
      
      // Wait for next scene to load
      await expect(page.locator('[data-testid="scene-index"]')).toContainText((sceneIndex + 1).toString());
      
      const endTime = Date.now();
      const transitionTime = endTime - startTime;
      transitionTimes.push(transitionTime);
      
      // Each transition should be under 800ms (p95 requirement)
      expect(transitionTime).toBeLessThan(800);
    }
    
    // Average transition time should be reasonable
    const averageTime = transitionTimes.reduce((a, b) => a + b, 0) / transitionTimes.length;
    expect(averageTime).toBeLessThan(500);
  });

  test('should handle browser refresh during scene progression', async ({ page }) => {
    // Complete bootstrap and progress to scene 2
    await page.locator('[data-testid="keyword-candidate"]').first().click();
    await page.locator('[data-testid="choice-option"]').first().click();
    
    // Verify we're at scene 2
    await expect(page.locator('[data-testid="scene-index"]')).toContainText('2');
    
    // Refresh the browser
    await page.reload();
    
    // Should handle session recovery appropriately
    // This might redirect to start, show error, or restore session
    // Implementation will determine exact behavior
    
    // At minimum, should not crash and should show some meaningful UI
    await expect(page.locator('body')).toBeVisible();
    
    // Should either restore session or show graceful restart option
    const isRestored = await page.locator('[data-testid="scene-index"]').isVisible();
    const hasRestart = await page.locator('[data-testid="restart-button"]').isVisible();
    
    expect(isRestored || hasRestart).toBe(true);
  });

  test('should display loading states during scene transitions', async ({ page }) => {
    // Complete bootstrap
    await page.locator('[data-testid="keyword-candidate"]').first().click();
    
    // Submit choice and immediately check for loading state
    const choicePromise = page.locator('[data-testid="choice-option"]').first().click();
    
    // Loading indicator should appear quickly
    await expect(page.locator('[data-testid="loading-indicator"]')).toBeVisible({ timeout: 100 });
    
    // Wait for choice submission to complete
    await choicePromise;
    
    // Loading indicator should disappear
    await expect(page.locator('[data-testid="loading-indicator"]')).not.toBeVisible();
    
    // Next scene should be visible
    await expect(page.locator('[data-testid="scene-narrative"]')).toBeVisible();
  });

  test('should support keyboard navigation through scenes', async ({ page }) => {
    // Complete bootstrap
    await page.locator('[data-testid="keyword-candidate"]').first().click();
    
    // Use keyboard navigation for choice selection
    // Tab to first choice
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab'); // Skip other elements to reach choices
    
    // Use arrow keys to navigate choices
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('ArrowUp');
    
    // Select choice with Enter
    await page.keyboard.press('Enter');
    
    // Should progress to next scene
    await expect(page.locator('[data-testid="scene-index"]')).toContainText('2');
    
    // Continue keyboard navigation through remaining scenes
    for (let sceneIndex = 2; sceneIndex <= 4; sceneIndex++) {
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab'); // Navigate to choices
      await page.keyboard.press('Enter'); // Select first choice
      
      if (sceneIndex < 4) {
        await expect(page.locator('[data-testid="scene-index"]')).toContainText((sceneIndex + 1).toString());
      }
    }
  });

  test('should handle different choice patterns and maintain score consistency', async ({ page }) => {
    // Complete bootstrap
    await page.locator('[data-testid="keyword-candidate"]').first().click();
    
    // Select different choice indices across scenes to test score accumulation
    const choicePattern = [0, 1, 2, 3]; // First, second, third, fourth choices
    
    for (let sceneIndex = 0; sceneIndex < 4; sceneIndex++) {
      const choices = page.locator('[data-testid="choice-option"]');
      await choices.nth(choicePattern[sceneIndex]).click();
      
      if (sceneIndex < 3) {
        // Wait for next scene
        await expect(page.locator('[data-testid="scene-index"]')).toContainText((sceneIndex + 2).toString());
      }
    }
    
    // After all scenes, should reach completion
    await expect(page.locator('[data-testid="completion-indicator"]')).toBeVisible();
  });
});

test.describe('4-Scene Flow Error Scenarios', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should handle session timeout during progression', async ({ page }) => {
    // Complete bootstrap and start progression
    await page.locator('[data-testid="keyword-candidate"]').first().click();
    await page.locator('[data-testid="choice-option"]').first().click();
    
    // Simulate session timeout by intercepting API requests
    await page.route('**/api/sessions/*', async route => {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({
          error_code: 'SESSION_NOT_FOUND',
          message: 'Session has expired',
          details: {}
        })
      });
    });
    
    // Try to progress to next scene
    await page.locator('[data-testid="choice-option"]').first().click();
    
    // Should display session timeout error
    await expect(page.locator('[data-testid="error-message"]')).toContainText(/セッション|タイムアウト|期限切れ/);
    
    // Should provide restart option
    await expect(page.locator('[data-testid="restart-button"]')).toBeVisible();
    
    // Restart should work
    await page.locator('[data-testid="restart-button"]').click();
    await expect(page.locator('[data-testid="keyword-candidate"]')).toBeVisible();
  });

  test('should handle API server errors during scene progression', async ({ page }) => {
    // Complete bootstrap
    await page.locator('[data-testid="keyword-candidate"]').first().click();
    
    // Simulate 500 server error
    await page.route('**/api/sessions/*/scenes/*/choice', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error_code: 'INTERNAL_ERROR',
          message: 'Internal server error occurred',
          details: {}
        })
      });
    });
    
    // Try to submit choice
    await page.locator('[data-testid="choice-option"]').first().click();
    
    // Should display server error message
    await expect(page.locator('[data-testid="error-message"]')).toContainText(/サーバー|エラー|問題/);
    
    // Should show retry option
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
  });

  test('should handle malformed API responses', async ({ page }) => {
    // Complete bootstrap
    await page.locator('[data-testid="keyword-candidate"]').first().click();
    
    // Simulate malformed response
    await page.route('**/api/sessions/*/scenes/*/choice', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          // Missing required fields
          sessionId: 'test-session-id'
          // No sceneCompleted or nextScene
        })
      });
    });
    
    // Try to submit choice
    await page.locator('[data-testid="choice-option"]').first().click();
    
    // Should handle malformed response gracefully
    await expect(page.locator('[data-testid="error-message"]')).toContainText(/データ|形式|問題/);
  });

  test('should handle slow API responses with timeout', async ({ page }) => {
    // Complete bootstrap
    await page.locator('[data-testid="keyword-candidate"]').first().click();
    
    // Simulate slow API response
    await page.route('**/api/sessions/*/scenes/*/choice', async route => {
      // Delay response by 10 seconds (should trigger timeout)
      await new Promise(resolve => setTimeout(resolve, 10000));
      await route.continue();
    });
    
    // Try to submit choice
    await page.locator('[data-testid="choice-option"]').first().click();
    
    // Should show loading state initially
    await expect(page.locator('[data-testid="loading-indicator"]')).toBeVisible();
    
    // Should timeout and show error message
    await expect(page.locator('[data-testid="error-message"]')).toContainText(/タイムアウト|時間切れ/);
  });
});
