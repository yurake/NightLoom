
/**
 * End-to-End tests for NightLoom MVP complete diagnosis flow including results.
 * 
 * Tests the complete user journey from start to results display and re-diagnosis.
 * Implements T044 requirements with Fail First testing strategy.
 */

import { test, expect, Page } from '@playwright/test';

test.describe('Complete Diagnosis Flow with Results E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the main application
    await page.goto('/');
  });

  test('should complete full diagnosis flow from start to results', async ({ page }) => {
    // Step 1: Bootstrap and keyword selection
    await expect(page.locator('[data-testid="loading-indicator"]')).toBeVisible();
    await expect(page.locator('[data-testid="keyword-candidate"]').first()).toBeVisible();
    
    const selectedKeyword = await page.locator('[data-testid="keyword-candidate"]').first().textContent();
    await page.locator('[data-testid="keyword-candidate"]').first().click();
    
    // Step 2: Complete all 4 scenes
    for (let sceneIndex = 1; sceneIndex <= 4; sceneIndex++) {
      // Wait for scene to load
      await expect(page.locator('[data-testid="scene-index"]')).toContainText(sceneIndex.toString());
      await expect(page.locator('[data-testid="scene-narrative"]')).toBeVisible();
      
      // Verify progress indicator
      await expect(page.locator('[data-testid="progress-text"]')).toContainText(`${sceneIndex} / 4`);
      
      // Select choice (vary selection to create diverse scores)
      const choiceIndex = (sceneIndex - 1) % 4; // 0, 1, 2, 3
      const choices = page.locator('[data-testid="choice-option"]');
      await expect(choices).toHaveCount(4);
      await choices.nth(choiceIndex).click();
      
      // Wait for transition (except after scene 4)
      if (sceneIndex < 4) {
        await expect(page.locator('[data-testid="loading-indicator"]')).toBeVisible();
      }
    }
    
    // Step 3: Verify result page navigation
    await expect(page.locator('[data-testid="result-screen"]')).toBeVisible({ timeout: 10000 });
    
    // Step 4: Verify result content display
    // Selected keyword should be displayed
    await expect(page.locator('[data-testid="result-keyword"]')).toContainText(selectedKeyword || '');
    
    // Axis scores should be displayed
    await expect(page.locator('[data-testid="axis-scores"]')).toBeVisible();
    const axisItems = page.locator('[data-testid="axis-score-item"]');
    expect(await axisItems.count()).toBeGreaterThan(1); // At least 2 axes
    
    // Type profile should be displayed
    await expect(page.locator('[data-testid="type-profile"]')).toBeVisible();
    await expect(page.locator('[data-testid="type-name"]')).toBeVisible();
    await expect(page.locator('[data-testid="type-description"]')).toBeVisible();
    
    // Multiple type cards should be available
    const typeCards = page.locator('[data-testid="type-card"]');
    expect(await typeCards.count()).toBeGreaterThanOrEqual(4);
    
    // Step 5: Verify "restart diagnosis" functionality
    await expect(page.locator('[data-testid="restart-button"]')).toBeVisible();
    await page.locator('[data-testid="restart-button"]').click();
    
    // Should return to initial state
    await expect(page.locator('[data-testid="keyword-candidate"]')).toBeVisible();
  });

  test('should display accurate axis scores based on choices made', async ({ page }) => {
    // Complete bootstrap
    await page.locator('[data-testid="keyword-candidate"]').first().click();
    
    // Make consistent choices to create predictable scores
    // Always select first choice (should have consistent weights)
    for (let sceneIndex = 1; sceneIndex <= 4; sceneIndex++) {
      await expect(page.locator('[data-testid="scene-index"]')).toContainText(sceneIndex.toString());
      await page.locator('[data-testid="choice-option"]').first().click();
    }
    
    // Verify result display
    await expect(page.locator('[data-testid="result-screen"]')).toBeVisible();
    
    // Check axis score displays
    const axisScores = page.locator('[data-testid="axis-score-item"]');
    const axisCount = await axisScores.count();
    
    for (let i = 0; i < axisCount; i++) {
      const axisItem = axisScores.nth(i);
      
      // Each axis should have name, score, and visual indicator
      await expect(axisItem.locator('[data-testid="axis-name"]')).toBeVisible();
      await expect(axisItem.locator('[data-testid="axis-score"]')).toBeVisible();
      await expect(axisItem.locator('[data-testid="axis-bar"]')).toBeVisible();
      
      // Score should be numeric and within range
      const scoreText = await axisItem.locator('[data-testid="axis-score"]').textContent();
      const score = parseInt(scoreText?.replace(/\D/g, '') || '0');
      expect(score).toBeGreaterThanOrEqual(0);
      expect(score).toBeLessThanOrEqual(100);
    }
  });

  test('should display relevant type profiles based on calculated scores', async ({ page }) => {
    // Complete diagnosis
    await page.locator('[data-testid="keyword-candidate"]').first().click();
    
    // Make specific choice pattern to influence type profiling
    const choicePattern = [0, 0, 0, 0]; // All first choices for consistency
    
    for (let sceneIndex = 1; sceneIndex <= 4; sceneIndex++) {
      await expect(page.locator('[data-testid="scene-index"]')).toContainText(sceneIndex.toString());
      await page.locator('[data-testid="choice-option"]').nth(choicePattern[sceneIndex - 1]).click();
    }
    
    // Verify type profile display
    await expect(page.locator('[data-testid="result-screen"]')).toBeVisible();
    
    // Main type profile should be prominently displayed
    const mainTypeProfile = page.locator('[data-testid="main-type-profile"]');
    await expect(mainTypeProfile).toBeVisible();
    await expect(mainTypeProfile.locator('[data-testid="type-name"]')).toBeVisible();
    await expect(mainTypeProfile.locator('[data-testid="type-description"]')).toBeVisible();
    
    // Additional type cards should provide variety
    const typeCards = page.locator('[data-testid="type-card"]');
    const cardCount = await typeCards.count();
    expect(cardCount).toBeGreaterThanOrEqual(4);
    
    // Each type card should have complete information
    for (let i = 0; i < Math.min(cardCount, 4); i++) {
      const typeCard = typeCards.nth(i);
      await expect(typeCard.locator('[data-testid="type-card-name"]')).toBeVisible();
      await expect(typeCard.locator('[data-testid="type-card-description"]')).toBeVisible();
      
      // Type cards should have interactive elements
      await expect(typeCard).toBeVisible();
    }
  });

  test('should handle results display with different score patterns', async ({ page }) => {
    // Test multiple diagnosis runs with different choice patterns
    const testPatterns = [
      { name: 'Logic-Heavy', pattern: [0, 0, 0, 0] },  // All first choices
      { name: 'Emotion-Heavy', pattern: [1, 1, 1, 1] }, // All second choices
      { name: 'Speed-Heavy', pattern: [2, 2, 2, 2] },   // All third choices
      { name: 'Caution-Heavy', pattern: [3, 3, 3, 3] }  // All fourth choices
    ];
    
    for (const testCase of testPatterns) {
      // Start fresh diagnosis
      await page.goto('/');
      await page.locator('[data-testid="keyword-candidate"]').first().click();
      
      // Execute choice pattern
      for (let sceneIndex = 1; sceneIndex <= 4; sceneIndex++) {
        await expect(page.locator('[data-testid="scene-index"]')).toContainText(sceneIndex.toString());
        await page.locator('[data-testid="choice-option"]').nth(testCase.pattern[sceneIndex - 1]).click();
      }
      
      // Verify results are displayed
      await expect(page.locator('[data-testid="result-screen"]')).toBeVisible();
      
      // Results should reflect the choice pattern
      await expect(page.locator('[data-testid="axis-scores"]')).toBeVisible();
      await expect(page.locator('[data-testid="type-profile"]')).toBeVisible();
      
      // Type name should reflect the choice bias (implementation dependent)
      const typeName = await page.locator('[data-testid="type-name"]').textContent();
      expect(typeName).toBeTruthy();
      expect(typeName!.length).toBeGreaterThan(0);
    }
  });

  test('should meet performance requirements for complete flow', async ({ page }) => {
    const startTime = Date.now();
    
    // Complete entire diagnosis flow
    await page.locator('[data-testid="keyword-candidate"]').first().click();
    
    const sceneStartTime = Date.now();
    
    // Complete all 4 scenes quickly
    for (let sceneIndex = 1; sceneIndex <= 4; sceneIndex++) {
      const sceneTransitionStart = Date.now();
      
      await expect(page.locator('[data-testid="scene-index"]')).toContainText(sceneIndex.toString());
      await page.locator('[data-testid="choice-option"]').first().click();
      
      const sceneTransitionEnd = Date.now();
      const transitionTime = sceneTransitionEnd - sceneTransitionStart;
      
      // Each scene transition should be under 800ms
      expect(transitionTime).toBeLessThan(800);
    }
    
    const resultStartTime = Date.now();
    
    // Wait for results to load
    await expect(page.locator('[data-testid="result-screen"]')).toBeVisible();
    
    const resultEndTime = Date.now();
    const resultCalculationTime = resultEndTime - resultStartTime;
    
    // Result generation should be under 1200ms (p95 requirement)
    expect(resultCalculationTime).toBeLessThan(1200);
    
    const totalTime = resultEndTime - startTime;
    
    // Total flow should complete in reasonable time
    expect(totalTime).toBeLessThan(5000); // 5 seconds total
  });

  test('should handle restart diagnosis functionality correctly', async ({ page }) => {
    // Complete full diagnosis
    await page.locator('[data-testid="keyword-candidate"]').first().click();
    
    for (let sceneIndex = 1; sceneIndex <= 4; sceneIndex++) {
      await expect(page.locator('[data-testid="scene-index"]')).toContainText(sceneIndex.toString());
      await page.locator('[data-testid="choice-option"]').first().click();
    }
    
    // Reach results
    await expect(page.locator('[data-testid="result-screen"]')).toBeVisible();
    
    // Store first result for comparison
    const firstTypeName = await page.locator('[data-testid="type-name"]').textContent();
    const firstKeyword = await page.locator('[data-testid="result-keyword"]').textContent();
    
    // Restart diagnosis
    await page.locator('[data-testid="restart-button"]').click();
    
    // Should return to initial state
    await expect(page.locator('[data-testid="keyword-candidate"]')).toBeVisible();
    
    // Complete second diagnosis with different choices
    await page.locator('[data-testid="keyword-candidate"]').nth(1).click(); // Select different keyword
    
    for (let sceneIndex = 1; sceneIndex <= 4; sceneIndex++) {
      await expect(page.locator('[data-testid="scene-index"]')).toContainText(sceneIndex.toString());
      // Select different choice pattern
      await page.locator('[data-testid="choice-option"]').nth(sceneIndex % 4).click();
    }
    
    // Reach second results
    await expect(page.locator('[data-testid="result-screen"]')).toBeVisible();
    
    // Results should be different (due to different choices/keyword)
    const secondTypeName = await page.locator('[data-testid="type-name"]').textContent();
    const secondKeyword = await page.locator('[data-testid="result-keyword"]').textContent();
    
    // Should have fresh results (keyword should be different)
    expect(secondKeyword).not.toBe(firstKeyword);
  });

  test('should display results with proper accessibility features', async ({ page }) => {
    // Complete diagnosis
    await page.locator('[data-testid="keyword-candidate"]').first().click();
    
    for (let sceneIndex = 1; sceneIndex <= 4; sceneIndex++) {
      await expect(page.locator('[data-testid="scene-index"]')).toContainText(sceneIndex.toString());
      await page.locator('[data-testid="choice-option"]').first().click();
    }
    
    await expect(page.locator('[data-testid="result-screen"]')).toBeVisible();
    
    // Check accessibility features
    // Proper headings structure
    expect(await page.locator('h1, h2, h3').count()).toBeGreaterThan(0);
    
    // ARIA labels for scores
    const axisScores = page.locator('[data-testid="axis-score-item"]');
    const axisCount = await axisScores.count();
    
    for (let i = 0; i < axisCount; i++) {
      const axisItem = axisScores.nth(i);
      
      // Should have proper ARIA labels
      await expect(axisItem).toHaveAttribute('role', 'group');
      
      // Score bars should have accessible descriptions
      const scoreBar = axisItem.locator('[data-testid="axis-bar"]');
      await expect(scoreBar).toHaveAttribute('aria-valuenow');
    }
    
    // Restart button should be accessible
    const restartButton = page.locator('[data-testid="restart-button"]');
    await expect(restartButton).toHaveAttribute('aria-label');
    
    // Focus should be manageable with keyboard
    await restartButton.focus();
    await expect(restartButton).toBeFocused();
  });

  test('should handle keyboard navigation in results screen', async ({ page }) => {
    // Complete diagnosis
    await page.locator('[data-testid="keyword-candidate"]').first().click();
    
    for (let sceneIndex = 1; sceneIndex <= 4; sceneIndex++) {
      await expect(page.locator('[data-testid="scene-index"]')).toContainText(sceneIndex.toString());
      await page.locator('[data-testid="choice-option"]').first().click();
    }
    
    await expect(page.locator('[data-testid="result-screen"]')).toBeVisible();
    
    // Test keyboard navigation through results
    // Tab through axis scores
    const axisItems = page.locator('[data-testid="axis-score-item"]');
    const axisCount = await axisItems.count();
    
    // Start from first focusable element
    await page.keyboard.press('Tab');
    
    // Navigate through axis scores with keyboard
    for (let i = 0; i < axisCount; i++) {
      await page.keyboard.press('Tab');
    }
    
    // Navigate to type cards
    const typeCards = page.locator('[data-testid="type-card"]');
    const cardCount = await typeCards.count();
    
    for (let i = 0; i < Math.min(cardCount, 3); i++) {
      await page.keyboard.press('Tab');
      // Press Enter to interact with type card
      await page.keyboard.press('Enter');
    }
    
    // Navigate to restart button
    await page.keyboard.press('Tab');
    const restartButton = page.locator('[data-testid="restart-button"]');
    await expect(restartButton).toBeFocused();
    
    // Press Enter to restart
    await page.keyboard.press('Enter');
    
    // Should return to keyword selection
    await expect(page.locator('[data-testid="keyword-candidate"]')).toBeVisible();
  });

  test('should handle result sharing or export functionality', async ({ page }) => {
    // Complete diagnosis
    await page.locator('[data-testid="keyword-candidate"]').first().click();
    
    for (let sceneIndex = 1; sceneIndex <= 4; sceneIndex++) {
      await expect(page.locator('[data-testid="scene-index"]')).toContainText(sceneIndex.toString());
      await page.locator('[data-testid="choice-option"]').first().click();
    }
    
    await expect(page.locator('[data-testid="result-screen"]')).toBeVisible();
    
    // Check for sharing or export functionality (if implemented)
    const shareButton = page.locator('[data-testid="share-button"]');
    const exportButton = page.locator('[data-testid="export-button"]');
    
    // These may not be implemented yet, but test documents expected behavior
    if (await shareButton.isVisible()) {
      await shareButton.click();
      // Should show sharing options
      await expect(page.locator('[data-testid="share-modal"]')).toBeVisible();
    }
    
    if (await exportButton.isVisible()) {
      await exportButton.click();
      // Should trigger export functionality
    }
  });
});

test.describe('Complete Diagnosis Flow Error Scenarios', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should handle API failures during result calculation', async ({ page }) => {
    // Complete 4 scenes
    await page.locator('[data-testid="keyword-candidate"]').first().click();
    
    for (let sceneIndex = 1; sceneIndex <= 4; sceneIndex++) {
      await expect(page.locator('[data-testid="scene-index"]')).toContainText(sceneIndex.toString());
      await page.locator('[data-testid="choice-option"]').first().click();
    }
    
    // Mock API failure for result endpoint
    await page.route('**/api/sessions/*/result', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error_code: 'INTERNAL_ERROR',
          message: 'Result calculation failed',
          details: {}
        })
      });
    });
    
    // Should handle result calculation failure
    await expect(page.locator('[data-testid="error-message"]')).toContainText(/結果|エラー|計算/);
    
    // Should provide retry or restart option
    const retryButton = page.locator('[data-testid="retry-button"]');
    const restartButton = page.locator('[data-testid="restart-button"]');
    
    expect(await retryButton.isVisible() || await restartButton.isVisible()).toBe(true);
  });

  test('should handle incomplete session during result request', async ({ page }) => {
    // Complete only 2 scenes
    await page.locator('[data-testid="keyword-candidate"]').first().click();
    
    for (let sceneIndex = 1; sceneIndex <= 2; sceneIndex++) {
      await expect(page.locator('[data-testid="scene-index"]')).toContainText(sceneIndex.toString());
      await page.locator('[data-testid="choice-option"]').first().click();
    }
    
    // Try to navigate to results prematurely (if possible)
    // This should be prevented by the UI, but test documents expected behavior
    
    // Should not be able to access results with incomplete session
    const currentUrl = page.url();
    expect(currentUrl).not.toMatch(/result/);
  });

  test('should handle browser navigation during result display', async ({ page }) => {
    // Complete diagnosis
    await page.locator('[data-testid="keyword-candidate"]').first().click();
    
    for (let sceneIndex = 1; sceneIndex <= 4; sceneIndex++) {
      await expect(page.locator('[data-testid="scene-index"]')).toContainText(sceneIndex.toString());
      await page.locator('[data-testid="choice-option"]').first().click();
    }
    
    await expect(page.locator('[data-testid="result-screen"]')).toBeVisible();
    
    // Test browser back button
    await page.goBack();
    
    // Should handle navigation gracefully
    // May show warning about losing progress or return to results
    
    // Test browser forward button
    await page.goForward();
    
    // Should return to results if session is still valid
    // Or show appropriate message if session expired
  });
});
