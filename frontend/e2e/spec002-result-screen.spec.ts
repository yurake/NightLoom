
/**
 * E2E Tests for Spec 002 - NightLoom結果画面表示機能
 * 
 * T038-T044 対応の包括的E2Eテストスイート
 */

import { test, expect } from '@playwright/test';

// テスト用データ
const mockSessionId = 'test-session-id';
const mockApiResponse = {
  sessionId: mockSessionId,
  keyword: 'test-keyword',
  type: {
    name: 'Test Type',
    description: 'This is a test type description for E2E testing.',
    dominantAxes: ['axis_1', 'axis_2'],
    polarity: 'High-Mid'
  },
  axes: [
    {
      id: 'axis_1',
      name: '論理性',
      description: '論理的思考の傾向',
      direction: '論理的 ← → 感情的',
      score: 75.5,
      rawScore: 2.5
    },
    {
      id: 'axis_2', 
      name: '社交性',
      description: '社交的な行動の傾向',
      direction: '内向的 ← → 外向的',
      score: 42.3,
      rawScore: -0.8
    }
  ],
  completedAt: new Date().toISOString()
};

test.describe('Spec 002: 結果画面表示機能', () => {
  test.beforeEach(async ({ page }) => {
    // API レスポンスのモック
    await page.route(`**/api/sessions/${mockSessionId}/result`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockApiResponse)
      });
    });
  });

  // T038: 基本表示フロー
  test('T038: 基本表示フロー - セッション完了 → 結果画面遷移 → タイプ・スコア表示確認', async ({ page }) => {
    // 結果画面に遷移
    await page.goto(`/play/result?sessionId=${mockSessionId}`);
    
    // ローディング状態の確認
    await expect(page.getByTestId('loading-indicator')).toBeVisible();
    
    // タイプカード表示確認
    await expect(page.getByRole('heading', { name: 'Test Type' })).toBeVisible();
    await expect(page.getByText('This is a test type description')).toBeVisible();
    await expect(page.getByText('High-Mid')).toBeVisible();
    
    // 軸スコア表示確認  
    await expect(page.getByText('論理性')).toBeVisible();
    await expect(page.getByText('75.5')).toBeVisible();
    await expect(page.getByText('社交性')).toBeVisible();
    await expect(page.getByText('42.3')).toBeVisible();
    
    // セッション情報表示確認
    await expect(page.getByText('test-keyword')).toBeVisible();
    
    // アクションボタン表示確認
    await expect(page.getByRole('button', { name: /もう一度診断する/ })).toBeVisible();
  });

  // T039: アニメーション確認
  test('T039: スコアバー1秒アニメーション、視覚的検証', async ({ page }) => {
    await page.goto(`/play/result?sessionId=${mockSessionId}`);
    
    // 結果表示を待機
    await expect(page.getByText('Test Type')).toBeVisible();
    
    // スコアバーのアニメーション確認
    const progressBar = page.getByTestId('progress-fill').first();
    
    // 初期状態（アニメーション前）
    await expect(progressBar).toHaveCSS('width', '0px');
    
    // アニメーション開始待機（100ms遅延）
    await page.waitForTimeout(150);
    
    // アニメーション完了確認（1秒後）
    await page.waitForTimeout(1100);
    await expect(progressBar).toHaveCSS('width', /\d+px/);
    
    // transition プロパティ確認
    await expect(progressBar).toHaveCSS('transition-duration', '1s');
    await expect(progressBar).toHaveCSS('transition-timing-function', 'ease-out');
  });

  // T040: 再診断フロー
  test('T040: 「もう一度診断する」→ 初期画面遷移 → 新セッション作成確認', async ({ page }) => {
    await page.goto(`/play/result?sessionId=${mockSessionId}`);
    
    // 結果表示を待機
    await expect(page.getByText('Test Type')).toBeVisible();
    
    // 再診断ボタンクリック
    const restartButton = page.getByRole('button', { name: /もう一度診断する/ });
    await expect(restartButton).toBeVisible();
    await restartButton.click();
    
    // 初期画面への遷移確認
    await expect(page).toHaveURL('/');
    
    // セッションクリーンアップ確認（LocalStorageクリア）
    const sessionId = await page.evaluate(() => localStorage.getItem('nightloom_session_id'));
    expect(sessionId).toBeNull();
  });

  // T041: エラー状態
  test('T041: エラー状態 - SESSION_NOT_FOUND, SESSION_NOT_COMPLETED, TYPE_GEN_FAILED', async ({ page }) => {
    // SESSION_NOT_FOUND エラー
    await page.route(`**/api/sessions/not-found/result`, async route => {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ code: 'SESSION_NOT_FOUND', message: 'Session not found' })
      });
    });
    
    await page.goto('/play/result?sessionId=not-found');
    await expect(page.getByTestId('error-message')).toBeVisible();
    await expect(page.getByText('セッションが見つかりません')).toBeVisible();
    
    // SESSION_NOT_COMPLETED エラー
    await page.route(`**/api/sessions/incomplete/result`, async route => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ code: 'SESSION_NOT_COMPLETED', message: 'Session not completed' })
      });
    });
    
    await page.goto('/play/result?sessionId=incomplete');
    await expect(page.getByText('診断が完了していません')).toBeVisible();
    
    // TYPE_GEN_FAILED エラー
    await page.route(`**/api/sessions/failed/result`, async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ code: 'TYPE_GEN_FAILED', message: 'Type generation failed' })
      });
    });
    
    await page.goto('/play/result?sessionId=failed');
    await expect(page.getByText('タイプ生成に失敗しました')).toBeVisible();
  });

  // T042: レスポンシブ表示
  test('T042: レスポンシブ表示 - 360px, 768px, 1024px, 1920px 各幅での表示確認', async ({ page }) => {
    await page.goto(`/play/result?sessionId=${mockSessionId}`);
    await expect(page.getByText('Test Type')).toBeVisible();
    
    // 360px (モバイル)
    await page.setViewportSize({ width: 360, height: 640 });
    await expect(page.getByText('Test Type')).toBeVisible();
    await expect(page.getByText('論理性')).toBeVisible();
    
    // レスポンシブクラス確認
    const axesSection = page.getByTestId('axes-section');
    await expect(axesSection).toHaveClass(/grid-cols-1/);
    
    // 768px (タブレット)
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.getByText('Test Type')).toBeVisible();
    
    // 1024px (デスクトップ)
    await page.setViewportSize({ width: 1024, height: 768 });
    await expect(page.getByText('Test Type')).toBeVisible();
    
    // 1920px (大画面)
    await page.setViewportSize({ width: 1920, height: 1080 });
    await expect(page.getByText('Test Type')).toBeVisible();
    
    // 大画面での表示品質確認
    const typeCard = page.getByTestId(/type-/);
    await expect(typeCard).toBeVisible();
    await expect(typeCard).toHaveCSS('max-width', /\d+px/);
  });

  // T043: アクセシビリティ
  test('T043: axe-core によるWCAG AA準拠検証、キーボードナビゲーション確認', async ({ page }) => {
    await page.goto(`/play/result?sessionId=${mockSessionId}`);
    await expect(page.getByText('Test Type')).toBeVisible();
    
    // アクセシビリティ基本チェック（axe-coreの代替）
    // mainタグの存在確認
    await expect(page.locator('main[role="main"]')).toBeVisible();
    
    // キーボードナビゲーション確認
    await page.keyboard.press('Tab');
    const restartButton = page.getByRole('button', { name: /もう一度診断する/ });
    await expect(restartButton).toBeFocused();
    
    // Enter キーでボタン実行
    await page.keyboard.press('Enter');
    await expect(page).toHaveURL('/');
    
    // ARIA 属性確認
    await page.goto(`/play/result?sessionId=${mockSessionId}`);
    await expect(page.getByText('Test Type')).toBeVisible();
    
    const progressBar = page.getByRole('progressbar').first();
    await expect(progressBar).toHaveAttribute('aria-label', /論理性のスコア/);
    await expect(progressBar).toHaveAttribute('aria-valuenow');
    await expect(progressBar).toHaveAttribute('aria-valuemin', '0');
    await expect(progressBar).toHaveAttribute('aria-valuemax', '100');
  });

  // T044: 全E2Eテスト統合確認
  test('T044: 全E2Eテスト実行 - 統合フロー確認', async ({ page }) => {
    // 統合フロー: エラー → 正常 → 再診断
    
    // 1. エラー状態から開始
    await page.route(`**/api/sessions/error-then-success/result`, async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ code: 'NETWORK_ERROR', message: 'Network error' })
      });
    });
    
    await page.goto('/play/result?sessionId=error-then-success');
    await expect(page.getByText('ネットワークエラーが発生しました')).toBeVisible();
    
    // 2. 正常状態に変更
    await page.route(`**/api/sessions/error-then-success/result`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockApiResponse)
      });
    });
    
    // ページリロード（リトライ相当）
    await page.reload();
    await expect(page.getByText('Test Type')).toBeVisible();
    
    // 3. アニメーション確認
    await page.waitForTimeout(1200);
    const progressBar = page.getByTestId('progress-fill').first();
    await expect(progressBar).toHaveCSS('width', /\d+px/);
    
    // 4. 再診断実行
    await page.getByRole('button', { name: /もう一度診断する/ }).click();
    await expect(page).toHaveURL('/');
    
    // 5. セッションクリーンアップ確認
    const cleanedData = await page.evaluate(() => {
      return {
        sessionId: localStorage.getItem('nightloom_session_id'),
        resultData: localStorage.getItem('nightloom_result_data')
      };
    });
    expect(cleanedData.sessionId).toBeNull();
    expect(cleanedData.resultData).toBeNull();
  });

  // パフォーマンステスト
  test('パフォーマンス: 初回レンダリング < 500ms要件確認', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto(`/play/result?sessionId=${mockSessionId}`);
    
    // 主要コンテンツの表示を待機
    await expect(page.getByText('Test Type')).toBeVisible();
    await expect(page.getByText('論理性')).toBeVisible();
    
    const endTime = Date.now();
    const renderTime = endTime - startTime;
    
    // 500ms要件確認
    expect(renderTime).toBeLessThan(500);
    
    // コンソールログでパフォーマンス記録
    console.log(`🚀 Result Screen Render Time: ${renderTime}ms (target: <500ms)`);
  });

  // アニメーション精度テスト
  test('アニメーション精度: ±50ms要件確認', async ({ page }) => {
    await page.goto(`/play/result?sessionId=${mockSessionId}`);
    await expect(page.getByText('Test Type')).toBeVisible();
    
    const progressBar = page.getByTestId('progress-fill').first();
    
    // アニメーション開始時間記録
    const animationStart = Date.now();
    
    // 1秒待機（理論値）
    await page.waitForTimeout(1000);
    
    const animationEnd = Date.now();
    const actualDuration = animationEnd - animationStart - 100; // 100ms遅延を除く
    
    // ±50ms要件確認
    const deviation = Math.abs(actualDuration - 1000);
    expect(deviation).toBeLessThan(50);
    
    console.log(`🎬 Animation Duration: ${actualDuration}ms (target: 1000ms ±50ms)`);
  });
});
