import { test, expect } from '@playwright/test';

/**
 * NightLoom 診断結果フロー E2E テスト
 * 現状、結果画面の多くの機能が未実装のため、
 * 実装待ちのケースには pending (fixme) を付与する。
 */

const markPending = (code: string, message: string) => {
  test.info().annotations.push({ type: 'fixme', description: `${code}: ${message}` });
};

const mockSessionId = '550e8400-e29b-41d4-a716-446655440000';
const mockKeyword = '成長';

const mockResultData = {
  sessionId: mockSessionId,
  keyword: mockKeyword,
  axes: [
    { axisId: 'growth', score: 82.5, rawScore: 3.1 },
    { axisId: 'stability', score: 45.8, rawScore: -0.6 },
    { axisId: 'innovation', score: 76.2, rawScore: 2.4 },
  ],
  type: {
    dominantAxes: ['growth', 'innovation'],
    profiles: [
      {
        name: 'Developer',
        description: '継続的に成長し、新しいスキルを習得する',
        keywords: ['成長', '学習', '向上'],
        dominantAxes: ['growth', 'innovation'],
        polarity: 'Hi-Hi',
      },
    ],
    fallbackUsed: false,
  },
  completedAt: '2024-01-15T10:35:00Z',
  fallbackFlags: [],
};

test.describe('Complete Diagnosis Flow E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('/api/sessions/*/result', async (route, request) => {
      const url = request.url();

      if (url.includes('llm-failure-session')) {
        await route.fulfill({
          status: 503,
          contentType: 'application/json',
          body: JSON.stringify({
            error_code: 'LLM_SERVICE_UNAVAILABLE',
            message: 'LLM service is currently unavailable',
            details: { retry_after: 30 },
          }),
        });
        return;
      }

      await route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify(mockResultData),
      });
    });
  });

  test('should complete full diagnosis flow and display results', async () => {
    markPending('NL-RES-001', '結果画面UIの骨組みが未実装');
    test.skip();
  });

  test('should display fallback results with appropriate indicators', async () => {
    markPending('NL-RES-002', 'フォールバック表示の処理が未実装');
    test.skip();
  });

  test('should handle incomplete session appropriately', async () => {
    markPending('NL-RES-003', '未完了セッション時のガイドが未実装');
    test.skip();
  });

  test('should handle expired session gracefully', async () => {
    markPending('NL-RES-004', '期限切れセッション時のエラーメッセージが未実装');
    test.skip();
  });

  test('should handle LLM service failure with appropriate messaging', async ({ page }) => {
    await page.goto(`/play/result?sessionId=llm-failure-session`);

    await expect(page.locator('[data-testid="error-message"]')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('[data-testid="error-message"]')).toContainText('サービス');
    await expect(page.locator('[data-testid="error-message"]')).toContainText('利用できません');
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
  });

  test('should support restart functionality', async () => {
    markPending('NL-RES-005', '再スタートボタンの導線が未実装');
    test.skip();
  });

  test('should display results with proper visual hierarchy', async () => {
    markPending('NL-RES-006', '結果画面の見出し/レイアウト整備が未完了');
    test.skip();
  });

  test('should meet accessibility requirements', async () => {
    markPending('NL-RES-007', '結果画面のアクセシビリティ改善が必要');
    test.skip();
  });

  test('should meet performance requirements for result loading', async ({ page }) => {
    const start = Date.now();

    await page.goto(`/play/result?sessionId=${mockSessionId}`);
    await expect(page.locator('[data-testid="result-container"]')).toBeVisible({ timeout: 10000 });

    const elapsed = Date.now() - start;
    expect(elapsed).toBeLessThan(2000);
  });

  test('should handle responsive design on mobile viewports', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto(`/play/result?sessionId=${mockSessionId}`);

    await expect(page.locator('[data-testid="result-container"]')).toBeVisible({ timeout: 10000 });
    const layoutClass = await page.locator('[data-testid="result-container"]').getAttribute('class');
    expect(layoutClass).toBeTruthy();
    expect(layoutClass).toContain('result-page');
  });

  test('should maintain theme consistency in results', async () => {
    markPending('NL-RES-008', '結果画面へのテーマ適用が未実装');
    test.skip();
  });

  test('should handle network interruptions during result loading', async () => {
    markPending('NL-RES-009', '結果ロード時の自動リトライが未実装');
    test.skip();
  });
});
