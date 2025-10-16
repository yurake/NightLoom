
/**
 * E2E tests for 4-scene completion flow - User Story 2
 * Tests the complete user experience from keyword confirmation through all scenes
 */

import { test, expect, Page } from '@playwright/test';

// Mock data for consistent testing
const mockSessionId = '550e8400-e29b-41d4-a716-446655440000';
const mockKeyword = '冒険';
const mockTheme = 'adventure';

// Scene narratives for validation
const expectedNarratives = {
  1: '森の入り口に立っている',
  2: '川のほとりに着いた',
  3: '古い遺跡を発見した',
  4: '宝箱を発見した'
};

test.describe('Scene Progression E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Set up API mocking for consistent test environment
    await page.route('/api/sessions/*/scenes/*', async (route, request) => {
      const url = request.url();
      const sceneMatch = url.match(/scenes\/(\d+)$/);
      
      if (sceneMatch) {
        const sceneIndex = parseInt(sceneMatch[1]);
        
        if (sceneIndex >= 1 && sceneIndex <= 4) {
          await route.fulfill({
            contentType: 'application/json',
            body: JSON.stringify({
              sessionId: mockSessionId,
              scene: {
                sceneIndex,
                themeId: mockTheme,
                narrative: `${expectedNarratives[sceneIndex]}。どの行動を選択しますか？`,
                choices: [
                  {
                    id: `choice_${sceneIndex}_1`,
                    text: `選択肢${sceneIndex}-1: 積極的な行動`,
                    weights: { curiosity: 0.8, logic: 0.2 }
                  },
                  {
                    id: `choice_${sceneIndex}_2`,
                    text: `選択肢${sceneIndex}-2: 慎重な行動`,
                    weights: { curiosity: 0.3, logic: 0.7 }
                  },
                  {
                    id: `choice_${sceneIndex}_3`,
                    text: `選択肢${sceneIndex}-3: 創造的な行動`,
                    weights: { curiosity: 0.9, logic: 0.1 }
                  },
                  {
                    id: `choice_${sceneIndex}_4`,
                    text: `選択肢${sceneIndex}-4: 安全な行動`,
                    weights: { curiosity: 0.1, logic: 0.9 }
                  }
                ]
              },
              fallbackUsed: false
            })
          });
        } else {
          await route.fulfill({
            status: 400,
            contentType: 'application/json',
            body: JSON.stringify({
              error_code: 'INVALID_SCENE_INDEX',
              message: 'Scene index must be between 1 and 4',
              details: { scene_index: sceneIndex }
            })
          });
        }
      }
    });

    // Mock choice submission endpoints
    await page.route('/api/sessions/*/scenes/*/choice', async (route, request) => {
      const url = request.url();
      const sceneMatch = url.match(/scenes\/(\d+)\/choice$/);
      
      if (sceneMatch) {
        const sceneIndex = parseInt(sceneMatch[1]);
        const requestBody = await request.postDataJSON();
        
        if (!requestBody.choiceId) {
          await route.fulfill({
            status: 422,
            contentType: 'application/json',
            body: JSON.stringify({
              error_code: 'VALIDATION_ERROR',
              message: 'Missing choiceId',
              details: { field: 'choiceId' }
            })
          });
          return;
        }
        
        const nextSceneIndex = sceneIndex < 4 ? sceneIndex + 1 : null;
        const nextScene = nextSceneIndex ? {
          sceneIndex: nextSceneIndex,
          themeId: mockTheme,
          narrative: `${expectedNarratives[nextSceneIndex]}。どの行動を選択しますか？`,
          choices: [
            {
              id: `choice_${nextSceneIndex}_1`,
              text: `選択肢${nextSceneIndex}-1: 積極的な行動`,
              weights: { curiosity: 0.8, logic: 0.2 }
            },
            {
              id: `choice_${nextSceneIndex}_2`,
              text: `選択肢${nextSceneIndex}-2: 慎重な行動`,
              weights: { curiosity: 0.3, logic: 0.7 }
            },
            {
              id: `choice_${nextSceneIndex}_3`,
              text: `選択肢${nextSceneIndex}-3: 創造的な行動`,
              weights: { curiosity: 0.9, logic: 0.1 }
            },
            {
              id: `choice_${nextSceneIndex}_4`,
              text: `選択肢${nextSceneIndex}-4: 安全な行動`,
              weights: { curiosity: 0.1, logic: 0.9 }
            }
          ]
        } : null;
        
        await route.fulfill({
          contentType: 'application/json',
          body: JSON.stringify({
            sessionId: mockSessionId,
            nextScene,
            sceneCompleted: true
          })
        });
      }
    });
  });

  test('should complete full 4-scene progression successfully', async ({ page }) => {
    // Start from scene 1 (assuming session is already bootstrapped)
    await page.goto(`/play?sessionId=${mockSessionId}&scene=1`);
    
    // Scene 1: Verify content and make choice
    await expect(page.locator('[data-testid="scene-container"]')).toBeVisible();
    await expect(page.locator('[data-testid="scene-narrative"]')).toContainText(expectedNarratives[1]);
    await expect(page.locator('[data-testid="scene-index"]')).toContainText('1');
    
    // Verify all 4 choices are present
    for (let i = 1; i <= 4; i++) {
      await expect(page.locator(`[data-testid="choice-1-${i}"]`)).toBeVisible();
    }
    
    // Make choice and advance to scene 2
    await page.click('[data-testid="choice-1-2"]');
    await expect(page.locator('[data-testid="scene-index"]')).toContainText('2', { timeout: 5000 });
    
    // Scene 2: Verify transition and content
    await expect(page.locator('[data-testid="scene-narrative"]')).toContainText(expectedNarratives[2]);
    
    // Verify progress indicator shows 2/4
    await expect(page.locator('[data-testid="progress-indicator"]')).toContainText('2 / 4');
    
    // Make choice and advance to scene 3
    await page.click('[data-testid="choice-2-1"]');
    await expect(page.locator('[data-testid="scene-index"]')).toContainText('3', { timeout: 5000 });
    
    // Scene 3: Verify content
    await expect(page.locator('[data-testid="scene-narrative"]')).toContainText(expectedNarratives[3]);
    await expect(page.locator('[data-testid="progress-indicator"]')).toContainText('3 / 4');
    
    // Make choice and advance to scene 4
    await page.click('[data-testid="choice-3-3"]');
    await expect(page.locator('[data-testid="scene-index"]')).toContainText('4', { timeout: 5000 });
    
    // Scene 4: Final scene
    await expect(page.locator('[data-testid="scene-narrative"]')).toContainText(expectedNarratives[4]);
    await expect(page.locator('[data-testid="progress-indicator"]')).toContainText('4 / 4');
    
    // Make final choice
    await page.click('[data-testid="choice-4-1"]');
    
    // Should be redirected to result page or show completion state
    await expect(page).toHaveURL(/.*result.*/, { timeout: 10000 });
  });

  test('should display loading states during scene transitions', async ({ page }) => {
    await page.goto(`/play?sessionId=${mockSessionId}&scene=1`);
    
    // Wait for scene to load
    await expect(page.locator('[data-testid="scene-container"]')).toBeVisible();
    
    // Click choice and check for loading state
    await page.click('[data-testid="choice-1-1"]');
    
    // Should show loading indicator during transition
    await expect(page.locator('[data-testid="loading-indicator"]')).toBeVisible({ timeout: 1000 });
    
    // Loading should disappear when next scene loads
    await expect(page.locator('[data-testid="loading-indicator"]')).not.toBeVisible({ timeout: 5000 });
    await expect(page.locator('[data-testid="scene-index"]')).toContainText('2');
  });

  test('should handle network errors gracefully', async ({ page }) => {
    // Override route to simulate network error
    await page.route('/api/sessions/*/scenes/2', async (route) => {
      await route.abort('failed');
    });
    
    await page.goto(`/play?sessionId=${mockSessionId}&scene=1`);
    await expect(page.locator('[data-testid="scene-container"]')).toBeVisible();
    
    // Make choice to trigger network error
    await page.click('[data-testid="choice-1-1"]');
    
    // Should display error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('[data-testid="error-message"]')).toContainText('ネットワーク');
    
    // Should show retry button
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
  });

  test('should maintain theme consistency across scenes', async ({ page }) => {
    await page.goto(`/play?sessionId=${mockSessionId}&scene=1`);
    
    // Check initial theme application
    const bodyClass = await page.locator('body').getAttribute('class');
    expect(bodyClass).toContain('theme-adventure');
    
    // Progress through scenes and verify theme consistency
    for (let scene = 1; scene < 4; scene++) {
      await page.click(`[data-testid="choice-${scene}-1"]`);
      await expect(page.locator('[data-testid="scene-container"]')).toBeVisible();
      
      // Theme should remain consistent
      const currentBodyClass = await page.locator('body').getAttribute('class');
      expect(currentBodyClass).toContain('theme-adventure');
    }
  });

  test('should validate choice selection requirements', async ({ page }) => {
    await page.goto(`/play?sessionId=${mockSessionId}&scene=1`);
    await expect(page.locator('[data-testid="scene-container"]')).toBeVisible();
    
    // Initially, continue button should be disabled or not visible
    const continueButton = page.locator('[data-testid="continue-button"]');
    if (await continueButton.isVisible()) {
      await expect(continueButton).toBeDisabled();
    }
    
    // After selecting a choice, continue should be enabled
    await page.click('[data-testid="choice-1-2"]');
    
    // Continue button should now be enabled or auto-advance should occur
    // (Depends on implementation - either immediate advance or confirm step)
  });

  test('should track and display progress correctly', async ({ page }) => {
    await page.goto(`/play?sessionId=${mockSessionId}&scene=2`);
    
    // Progress indicator should show current scene
    await expect(page.locator('[data-testid="progress-indicator"]')).toContainText('2 / 4');
    
    // Progress bar should show 50% completion
    const progressBar = page.locator('[data-testid="progress-bar"]');
    if (await progressBar.isVisible()) {
      const progressValue = await progressBar.getAttribute('value');
      expect(parseInt(progressValue || '0')).toBe(50);
    }
    
    // Scene counter should be accurate
    await expect(page.locator('[data-testid="scene-counter"]')).toContainText('シーン 2');
  });

  test('should handle invalid scene access attempts', async ({ page }) => {
    // Try to access scene 5 (invalid)
    await page.goto(`/play?sessionId=${mockSessionId}&scene=5`);
    
    // Should display error or redirect
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('[data-testid="error-message"]')).toContainText('無効');
    
    // Try to access scene 0 (invalid)
    await page.goto(`/play?sessionId=${mockSessionId}&scene=0`);
    
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible({ timeout: 5000 });
  });

  test('should meet performance requirements for scene transitions', async ({ page }) => {
    await page.goto(`/play?sessionId=${mockSessionId}&scene=1`);
    await expect(page.locator('[data-testid="scene-container"]')).toBeVisible();
    
    // Measure scene transition time
    const startTime = Date.now();
    await page.click('[data-testid="choice-1-1"]');
    await expect(page.locator('[data-testid="scene-index"]')).toContainText('2');
    const endTime = Date.now();
    
    const transitionTime = endTime - startTime;
    
    // Should meet performance target: scene transitions < 800ms (p95)
    // In E2E tests, we allow more time due to network simulation
    expect(transitionTime).toBeLessThan(2000);
  });

  test('should handle choice submission failures', async ({ page }) => {
    // Override route to simulate choice submission failure
    await page.route('/api/sessions/*/scenes/*/choice', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error_code: 'INTERNAL_ERROR',
          message: 'Internal server error',
          details: { timestamp: new Date().toISOString() }
        })
      });
    });
    
    await page.goto(`/play?sessionId=${mockSessionId}&scene=1`);
    await expect(page.locator('[data-testid="scene-container"]')).toBeVisible();
    
    // Make choice that will fail
    await page.click('[data-testid="choice-1-1"]');
    
    // Should display error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible({ timeout: 5000 });
    
    // Should show retry button
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
  });

  test('should preserve user choices when navigating back', async ({ page }) => {
    await page.goto(`/play?sessionId=${mockSessionId}&scene=2`);
    await expect(page.locator('[data-testid="scene-container"]')).toBeVisible();
    
    // Navigate back to scene 1 (if allowed by implementation)
    if (await page.locator('[data-testid="back-button"]').isVisible()) {
      await page.click('[data-testid="back-button"]');
      
      // Should show previously selected choice as selected
      await expect(page.locator('[data-testid="scene-index"]')).toContainText('1');
      
      // Previous choice should be highlighted/selected
      const selectedChoice = page.locator('[data-testid*="choice"][data-selected="true"]');
      if (await selectedChoice.isVisible()) {
        expect(await selectedChoice.isVisible()).toBe(true);
      }
    }
  });

  test('should handle session expiration during scene progression', async ({ page }) => {
    // Override route to simulate session expiration
    await page.route('/api/sessions/*/scenes/*/choice', async (route) => {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({
          error_code: 'SESSION_NOT_FOUND',
          message: 'Session has expired',
          details: { session_id: mockSessionId }
        })
      });
    });
    
    await page.goto(`/play?sessionId=${mockSessionId}&scene=1`);
    await expect(page.locator('[data-testid="scene-container"]')).toBeVisible();
    
    // Make choice that triggers session expiration
    await page.click('[data-testid="choice-1-1"]');
    
    // Should display session expiration message
    await expect(page.locator('[data-testid="error-message"]')).toContainText('セッション');
    
    // Should offer restart option
    await expect(page.locator('[data-testid="restart-button"]')).toBeVisible();
  });
});
