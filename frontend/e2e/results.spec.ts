
/**
 * E2E tests for complete diagnosis flow including results - User Story 3
 * Tests the full journey from session start through result display
 */

import { test, expect, Page } from '@playwright/test';

// Mock data for consistent testing
const mockSessionId = '550e8400-e29b-41d4-a716-446655440000';
const mockKeyword = '成長';
const mockTheme = 'focus';

// Expected result data structure
const mockResultData = {
  sessionId: mockSessionId,
  keyword: mockKeyword,
  axes: [
    { axisId: 'growth', score: 82.5, rawScore: 3.1 },
    { axisId: 'stability', score: 45.8, rawScore: -0.6 },
    { axisId: 'innovation', score: 76.2, rawScore: 2.4 }
  ],
  type: {
    dominantAxes: ['growth', 'innovation'],
    profiles: [
      {
        name: 'Developer',
        description: '継続的に成長し、新しいスキルを習得する',
        keywords: ['成長', '学習', '向上'],
        dominantAxes: ['growth', 'innovation'],
        polarity: 'Hi-Hi'
      },
      {
        name: 'Pioneer',
        description: '新しい分野を開拓し、革新を生み出す',
        keywords: ['開拓', '革新', '創造'],
        dominantAxes: ['innovation', 'growth'],
        polarity: 'Hi-Hi'
      },
      {
        name: 'Learner',
        description: '知識を蓄積し、経験から学ぶ',
        keywords: ['学習', '知識', '経験'],
        dominantAxes: ['growth', 'stability'],
        polarity: 'Hi-Mid'
      },
      {
        name: 'Adapter',
        description: '変化に適応し、柔軟性を発揮する',
        keywords: ['適応', '柔軟', '変化'],
        dominantAxes: ['innovation', 'growth'],
        polarity: 'Hi-Hi'
      }
    ],
    fallbackUsed: false
  },
  completedAt: '2024-01-15T10:35:00Z',
  fallbackFlags: []
};

const mockFallbackResultData = {
  sessionId: mockSessionId,
  keyword: mockKeyword,
  axes: [
    { axisId: 'stability', score: 50.0, rawScore: 0.0 },
    { axisId: 'adaptability', score: 50.0, rawScore: 0.0 }
  ],
  type: {
    dominantAxes: ['stability', 'adaptability'],
    profiles: [
      {
        name: 'Balanced',
        description: 'バランスの取れたアプローチを取る',
        keywords: ['バランス', '安定', '適応'],
        dominantAxes: ['stability', 'adaptability'],
        polarity: 'Mid-Mid'
      },
      {
        name: 'Steady',
        description: '着実に物事を進める',
        keywords: ['着実', '継続', '信頼'],
        dominantAxes: ['stability', 'adaptability'],
        polarity: 'Hi-Mid'
      },
      {
        name: 'Flexible',
        description: '状況に応じて対応する',
        keywords: ['柔軟', '対応', '変化'],
        dominantAxes: ['adaptability', 'stability'],
        polarity: 'Mid-Hi'
      },
      {
        name: 'Resilient',
        description: '困難に立ち向かう',
        keywords: ['回復', '強さ', '耐性'],
        dominantAxes: ['stability', 'adaptability'],
        polarity: 'Hi-Hi'
      }
    ],
    fallbackUsed: true
  },
  completedAt: '2024-01-15T10:35:30Z',
  fallbackFlags: ['TYPE_FALLBACK']
};

test.describe('Complete Diagnosis Flow E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Mock result API endpoint
    await page.route('/api/sessions/*/result', async (route, request) => {
      const url = request.url();
      
      if (url.includes('fallback-session')) {
        await route.fulfill({
          contentType: 'application/json',
          body: JSON.stringify(mockFallbackResultData)
        });
      } else if (url.includes('incomplete-session')) {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({
            error_code: 'SESSION_NOT_COMPLETED',
            message: 'Session has not completed all 4 scenes',
            details: { scenes_completed: 2, scenes_required: 4 }
          })
        });
      } else if (url.includes('expired-session')) {
        await route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({
            error_code: 'SESSION_NOT_FOUND',
            message: 'Session has expired or does not exist',
            details: { session_id: 'expired-session' }
          })
        });
      } else if (url.includes('llm-failure-session')) {
        await route.fulfill({
          status: 503,
          contentType: 'application/json',
          body: JSON.stringify({
            error_code: 'LLM_SERVICE_UNAVAILABLE',
            message: 'LLM service is currently unavailable',
            details: { retry_after: 30 }
          })
        });
      } else {
        await route.fulfill({
          contentType: 'application/json',
          body: JSON.stringify(mockResultData)
        });
      }
    });

    // Mock sessions cleanup endpoint (for restart functionality)
    await page.route('/api/sessions/*/cleanup', async (route) => {
      await route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({ success: true })
      });
    });
  });

  test('should complete full diagnosis flow and display results', async ({ page }) => {
    // Navigate to result page (assuming 4 scenes completed)
    await page.goto(`/play/result?sessionId=${mockSessionId}`);
    
    // Result page should load
    await expect(page.locator('[data-testid="result-container"]')).toBeVisible({ timeout: 10000 });
    
    // Verify result title and structure
    await expect(page.locator('[data-testid="result-title"]')).toBeVisible();
    await expect(page.locator('[data-testid="result-title"]')).toContainText('診断結果');
    
    // Verify keyword display
    await expect(page.locator('[data-testid="keyword-display"]')).toBeVisible();
    await expect(page.locator('[data-testid="keyword-display"]')).toContainText(mockKeyword);
    
    // Verify axes scores section
    await expect(page.locator('[data-testid="axes-section"]')).toBeVisible();
    
    // Check each axis score
    await expect(page.locator('[data-testid="axis-growth"]')).toBeVisible();
    await expect(page.locator('[data-testid="axis-growth"]')).toContainText('82.5');
    
    await expect(page.locator('[data-testid="axis-stability"]')).toBeVisible();
    await expect(page.locator('[data-testid="axis-stability"]')).toContainText('45.8');
    
    await expect(page.locator('[data-testid="axis-innovation"]')).toBeVisible();
    await expect(page.locator('[data-testid="axis-innovation"]')).toContainText('76.2');
    
    // Verify type profiles section
    await expect(page.locator('[data-testid="type-profiles-section"]')).toBeVisible();
    
    // Check type profiles are displayed
    await expect(page.locator('[data-testid="type-developer"]')).toBeVisible();
    await expect(page.locator('[data-testid="type-developer"]')).toContainText('Developer');
    await expect(page.locator('[data-testid="type-developer"]')).toContainText('継続的に成長');
    
    await expect(page.locator('[data-testid="type-pioneer"]')).toBeVisible();
    await expect(page.locator('[data-testid="type-pioneer"]')).toContainText('Pioneer');
    
    await expect(page.locator('[data-testid="type-learner"]')).toBeVisible();
    await expect(page.locator('[data-testid="type-learner"]')).toContainText('Learner');
    
    await expect(page.locator('[data-testid="type-adapter"]')).toBeVisible();
    await expect(page.locator('[data-testid="type-adapter"]')).toContainText('Adapter');
    
    // Verify restart functionality
    await expect(page.locator('[data-testid="restart-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="restart-button"]')).toContainText('もう一度診断');
  });

  test('should display fallback results with appropriate indicators', async ({ page }) => {
    await page.goto(`/play/result?sessionId=fallback-session`);
    
    // Result should load with fallback data
    await expect(page.locator('[data-testid="result-container"]')).toBeVisible({ timeout: 10000 });
    
    // Should show fallback indicator
    await expect(page.locator('[data-testid="fallback-indicator"]')).toBeVisible();
    await expect(page.locator('[data-testid="fallback-indicator"]')).toContainText('基本的な結果');
    
    // Should still show valid results
    await expect(page.locator('[data-testid="axes-section"]')).toBeVisible();
    await expect(page.locator('[data-testid="type-profiles-section"]')).toBeVisible();
    
    // Fallback scores should be displayed (50.0 for both axes)
    await expect(page.locator('[data-testid="axis-stability"]')).toContainText('50.0');
    await expect(page.locator('[data-testid="axis-adaptability"]')).toContainText('50.0');
  });

  test('should handle incomplete session appropriately', async ({ page }) => {
    await page.goto(`/play/result?sessionId=incomplete-session`);
    
    // Should show error or redirect back to scenes
    await expect(page.locator('[data-testid="error-container"]')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('[data-testid="error-message"]')).toContainText('完了していません');
    
    // Should provide option to continue
    await expect(page.locator('[data-testid="continue-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="continue-button"]')).toContainText('診断を続ける');
  });

  test('should handle expired session gracefully', async ({ page }) => {
    await page.goto(`/play/result?sessionId=expired-session`);
    
    // Should show session expired message
    await expect(page.locator('[data-testid="error-container"]')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('[data-testid="error-message"]')).toContainText('セッション');
    await expect(page.locator('[data-testid="error-message"]')).toContainText('期限切れ');
    
    // Should provide restart option
    await expect(page.locator('[data-testid="restart-button"]')).toBeVisible();
  });

  test('should handle LLM service failure with appropriate messaging', async ({ page }) => {
    await page.goto(`/play/result?sessionId=llm-failure-session`);
    
    // Should show service unavailable message
    await expect(page.locator('[data-testid="error-container"]')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('[data-testid="error-message"]')).toContainText('サービス');
    await expect(page.locator('[data-testid="error-message"]')).toContainText('利用できません');
    
    // Should provide retry option
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
  });

  test('should support restart functionality', async ({ page }) => {
    await page.goto(`/play/result?sessionId=${mockSessionId}`);
    
    // Wait for result to load
    await expect(page.locator('[data-testid="result-container"]')).toBeVisible();
    
    // Click restart button
    await page.click('[data-testid="restart-button"]');
    
    // Should navigate to start page or show confirmation
    await expect(page).toHaveURL(/.*start.*|.*play.*/, { timeout: 10000 });
  });

  test('should display results with proper visual hierarchy', async ({ page }) => {
    await page.goto(`/play/result?sessionId=${mockSessionId}`);
    
    await expect(page.locator('[data-testid="result-container"]')).toBeVisible();
    
    // Check visual hierarchy with heading levels
    await expect(page.locator('h1[data-testid="result-title"]')).toBeVisible();
    await expect(page.locator('h2[data-testid="axes-title"]')).toBeVisible();
    await expect(page.locator('h2[data-testid="types-title"]')).toBeVisible();
    
    // Verify sections are properly structured
    const axesSection = page.locator('[data-testid="axes-section"]');
    const typesSection = page.locator('[data-testid="type-profiles-section"]');
    
    await expect(axesSection).toBeVisible();
    await expect(typesSection).toBeVisible();
  });

  test('should meet accessibility requirements', async ({ page }) => {
    await page.goto(`/play/result?sessionId=${mockSessionId}`);
    
    await expect(page.locator('[data-testid="result-container"]')).toBeVisible();
    
    // Check keyboard navigation
    await page.keyboard.press('Tab');
    const focusedElement = await page.locator(':focus').getAttribute('data-testid');
    expect(focusedElement).toBeTruthy();
    
    // Check ARIA labels and roles
    await expect(page.locator('[role="main"]')).toBeVisible();
    await expect(page.locator('[aria-label*="診断結果"]')).toBeVisible();
    
    // Check screen reader friendly content
    const axisElements = page.locator('[data-testid^="axis-"]');
    const axisCount = await axisElements.count();
    
    for (let i = 0; i < axisCount; i++) {
      const axis = axisElements.nth(i);
      await expect(axis).toHaveAttribute('aria-label');
    }
  });

  test('should meet performance requirements for result loading', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto(`/play/result?sessionId=${mockSessionId}`);
    
    // Result should load within performance target
    await expect(page.locator('[data-testid="result-container"]')).toBeVisible({ timeout: 5000 });
    
    const endTime = Date.now();
    const loadTime = endTime - startTime;
    
    // Should meet performance target: p95 ≤ 1.2s for result generation
    // In E2E tests, we allow more time due to network simulation
    expect(loadTime).toBeLessThan(3000);
  });

  test('should handle responsive design on mobile viewports', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto(`/play/result?sessionId=${mockSessionId}`);
    
    await expect(page.locator('[data-testid="result-container"]')).toBeVisible();
    
    // Result should be properly displayed on mobile
    const container = page.locator('[data-testid="result-container"]');
    const boundingBox = await container.boundingBox();
    
    expect(boundingBox?.width).toBeLessThanOrEqual(375);
    
    // Axes and types should be vertically stacked on mobile
    const axesSection = page.locator('[data-testid="axes-section"]');
    const typesSection = page.locator('[data-testid="type-profiles-section"]');
    
    await expect(axesSection).toBeVisible();
    await expect(typesSection).toBeVisible();
  });

  test('should maintain theme consistency in results', async ({ page }) => {
    await page.goto(`/play/result?sessionId=${mockSessionId}`);
    
    await expect(page.locator('[data-testid="result-container"]')).toBeVisible();
    
    // Theme should be applied consistently
    const bodyClass = await page.locator('body').getAttribute('class');
    expect(bodyClass).toContain('theme-');
    
    // Theme colors should be applied to result elements
    const resultContainer = page.locator('[data-testid="result-container"]');
    const computedStyle = await resultContainer.evaluate(el => {
      return window.getComputedStyle(el).backgroundColor;
    });
    
    expect(computedStyle).toBeTruthy();
  });

  test('should handle network interruptions during result loading', async ({ page }) => {
    // Start loading the page
    const pagePromise = page.goto(`/play/result?sessionId=${mockSessionId}`);
    
    // Simulate network interruption
    await page.route('**/*', route => route.abort());
    
    try {
      await pagePromise;
    } catch (error) {
      // Network error is expected
    }
    
    // Restore network and retry
    await page.unroute('**/*');
    
    await page.reload();
    
    // Should eventually load successfully
    await expect(page.locator('[data-testid="result-container"]')).toBeVisible({ timeout: 10000 });
  });
});
