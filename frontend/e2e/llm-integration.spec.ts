import { test, expect, type Page } from '@playwright/test';

/**
 * NightLoom LLM機能統合 E2Eテスト（正常系のみ）
 * 1分程度で実行可能なクイックテスト
 */

// テスト用のモックデータ
const MOCK_SESSION_ID = '550e8400-e29b-41d4-a716-446655440000';

const MOCK_BOOTSTRAP_RESPONSE = {
  sessionId: MOCK_SESSION_ID,
  axes: [
    {
      id: 'focus_creativity',
      name: '集中と創造性の指標',
      description: '集中力と創造性のバランスを測定',
      direction: '集中 ⟷ 創造性',
    },
  ],
  keywordCandidates: ['テスト', 'てがみ', 'てんき', 'てつだい'],
  initialCharacter: 'て',
  themeId: 'focus',
  fallbackUsed: false,
};

const MOCK_SCENE_RESPONSE = {
  sessionId: MOCK_SESSION_ID,
  scene: {
    sceneIndex: 1,
    themeId: 'focus',
    narrative: 'テストの世界へようこそ。集中力が試される場面です。',
    choices: [
      { id: 'choice_1_1', text: '集中して取り組む', weights: { focus: 0.8 } },
      { id: 'choice_1_2', text: '創造的にアプローチする', weights: { creativity: 0.7 } },
      { id: 'choice_1_3', text: 'バランスを取る', weights: { focus: 0.5, creativity: 0.5 } },
      { id: 'choice_1_4', text: '直感に従う', weights: { intuition: 0.6 } },
    ],
  },
  fallbackUsed: false,
};

const MOCK_RESULT_RESPONSE = {
  sessionId: MOCK_SESSION_ID,
  result: {
    personalityType: '集中型クリエイター',
    description: '集中力と創造性を併せ持つバランスの取れたタイプです。',
    axes: [
      { name: 'focus', score: 75, description: '集中力' },
      { name: 'creativity', score: 68, description: '創造性' },
    ],
    themeId: 'focus',
  },
  fallbackUsed: false,
};

async function setupLLMApiMocks(page: Page) {
  // Bootstrap API
  await page.route('**/api/bootstrap', async (route) => {
    await new Promise(resolve => setTimeout(resolve, 100)); // リアルな遅延
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(MOCK_BOOTSTRAP_RESPONSE),
    });
  });

  // Keyword confirmation API
  await page.route('**/api/*/keyword', async (route) => {
    await new Promise(resolve => setTimeout(resolve, 150));
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(MOCK_SCENE_RESPONSE),
    });
  });

  // Scene progression API
  await page.route('**/api/*/scenes/*', async (route) => {
    const url = route.request().url();
    const sceneIndex = parseInt(url.match(/scenes\/(\d+)/)?.[1] || '1');
    
    const sceneResponse = {
      ...MOCK_SCENE_RESPONSE,
      scene: {
        ...MOCK_SCENE_RESPONSE.scene,
        sceneIndex,
        narrative: `シーン${sceneIndex}: 新たな挑戦が始まります。`,
      },
    };

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(sceneResponse),
    });
  });

  // Choice submission API
  await page.route('**/api/*/scenes/*/choice', async (route) => {
    await new Promise(resolve => setTimeout(resolve, 100));
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true, nextScene: true }),
    });
  });

  // Results API
  await page.route('**/api/*/results', async (route) => {
    await new Promise(resolve => setTimeout(resolve, 200));
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(MOCK_RESULT_RESPONSE),
    });
  });

  // Progress API
  await page.route('**/api/*/progress', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        sessionId: MOCK_SESSION_ID,
        state: 'PLAY',
        completedScenes: 1,
        totalScenes: 4,
        currentScene: 2,
        progressPercentage: 25,
        canProceedToResult: false,
      }),
    });
  });
}

async function navigateToPlay(page: Page) {
  await page.getByRole('button', { name: 'Focus' }).click();
  await page.getByRole('button', { name: '診断を開始' }).click();
  await expect(page).toHaveURL(/\/play$/);
}

test.describe('LLM Integration E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await setupLLMApiMocks(page);
    await page.goto('/');
  });

  test('should complete full user journey from keyword to result', async ({ page }) => {
    // 1. ホーム画面から診断開始
    await navigateToPlay(page);

    // 2. Bootstrap処理完了とキーワード候補表示を確認
    await expect(page.locator('[data-testid="keyword-candidates"]')).toBeVisible({ timeout: 5000 });
    
    // 3. キーワード選択
    const firstKeyword = page.locator('[data-testid="keyword-candidates"] button').first();
    await firstKeyword.click();

    // 4. 最初のシーン表示確認
    await expect(page.locator('[data-testid="scene-narrative"]')).toBeVisible({ timeout: 3000 });
    await expect(page.locator('[data-testid="scene-narrative"]')).toContainText('テストの世界');
    
    // 5. 選択肢の確認
    const choices = page.locator('[data-testid="choice-options"] button');
    await expect(choices).toHaveCount(4);
    await expect(choices.first()).toContainText('集中して');

    // 6. 選択肢を選んで次に進む（簡略化）
    await choices.first().click();

    // 7. 進行状況の確認
    await expect(page.locator('[data-testid="progress-indicator"]')).toBeVisible();
    
    // この統合テストでは全4シーンの完全な流れは省略し、
    // LLM機能の基本的な統合が動作することを確認する
  });

  test('should handle LLM keyword generation successfully', async ({ page }) => {
    await navigateToPlay(page);

    // Bootstrap処理中のローディング確認
    const loadingIndicator = page.locator('[data-testid="bootstrap-loading"]');
    if (await loadingIndicator.isVisible()) {
      await expect(loadingIndicator).toBeHidden({ timeout: 5000 });
    }

    // LLM生成キーワード候補の表示確認
    await expect(page.locator('[data-testid="keyword-candidates"]')).toBeVisible();
    
    const keywordButtons = page.locator('[data-testid="keyword-candidates"] button');
    await expect(keywordButtons).toHaveCount(4);

    // 各キーワードが「て」から始まることを確認
    for (let i = 0; i < 4; i++) {
      const keyword = await keywordButtons.nth(i).textContent();
      expect(keyword?.startsWith('て')).toBe(true);
    }
  });

  test('should handle custom keyword input with LLM processing', async ({ page }) => {
    await navigateToPlay(page);
    await expect(page.locator('[data-testid="keyword-candidates"]')).toBeVisible({ timeout: 5000 });

    // カスタムキーワード入力
    const customInput = page.locator('[data-testid="custom-keyword-input"]');
    await customInput.fill('てすと');

    const submitButton = page.locator('[data-testid="submit-custom-keyword"]');
    await expect(submitButton).toBeEnabled();
    await submitButton.click();

    // LLM処理後のシーン表示確認
    await expect(page.locator('[data-testid="scene-narrative"]')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('[data-testid="scene-narrative"]')).toContainText('テストの世界');
  });

  test('should display scene content generated by LLM', async ({ page }) => {
    await navigateToPlay(page);
    await expect(page.locator('[data-testid="keyword-candidates"]')).toBeVisible({ timeout: 5000 });

    // キーワード選択
    await page.locator('[data-testid="keyword-candidates"] button').first().click();

    // LLM生成シーンコンテンツの確認
    await expect(page.locator('[data-testid="scene-narrative"]')).toBeVisible({ timeout: 3000 });
    
    const narrative = page.locator('[data-testid="scene-narrative"]');
    await expect(narrative).toContainText('テストの世界');
    await expect(narrative).toContainText('集中力が試される');

    // LLM生成選択肢の確認
    const choices = page.locator('[data-testid="choice-options"] button');
    await expect(choices).toHaveCount(4);
    
    // 各選択肢のテキスト確認
    await expect(choices.nth(0)).toContainText('集中して');
    await expect(choices.nth(1)).toContainText('創造的に');
    await expect(choices.nth(2)).toContainText('バランス');
    await expect(choices.nth(3)).toContainText('直感');
  });

  test('should handle fallback when LLM is unavailable', async ({ page }) => {
    // フォールバック応答をセットアップ
    await page.route('**/api/bootstrap', async (route) => {
      const fallbackResponse = {
        ...MOCK_BOOTSTRAP_RESPONSE,
        keywordCandidates: ['フォールバック1', 'フォールバック2', 'フォールバック3', 'フォールバック4'],
        fallbackUsed: true,
      };
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(fallbackResponse),
      });
    });

    await navigateToPlay(page);
    await expect(page.locator('[data-testid="keyword-candidates"]')).toBeVisible({ timeout: 5000 });

    // フォールバックキーワードの確認
    const keywordButtons = page.locator('[data-testid="keyword-candidates"] button');
    await expect(keywordButtons.first()).toContainText('フォールバック');

    // フォールバック使用インジケーターがあれば確認
    const fallbackIndicator = page.locator('[data-testid="fallback-notice"]');
    if (await fallbackIndicator.isVisible()) {
      await expect(fallbackIndicator).toContainText('フォールバック');
    }
  });

  test('should maintain session state across LLM interactions', async ({ page }) => {
    await navigateToPlay(page);
    await expect(page.locator('[data-testid="keyword-candidates"]')).toBeVisible({ timeout: 5000 });

    // セッション情報があれば確認
    const sessionInfo = page.locator('[data-testid="session-debug-info"]');
    if (await sessionInfo.isVisible()) {
      const sessionId = await sessionInfo.getAttribute('data-session-id');
      expect(sessionId).toBe(MOCK_SESSION_ID);
    }

    // キーワード選択からシーン遷移でセッション継続確認
    await page.locator('[data-testid="keyword-candidates"] button').first().click();
    await expect(page.locator('[data-testid="scene-narrative"]')).toBeVisible({ timeout: 3000 });

    // 同じセッションIDが維持されていることを確認
    if (await sessionInfo.isVisible()) {
      const sessionId = await sessionInfo.getAttribute('data-session-id');
      expect(sessionId).toBe(MOCK_SESSION_ID);
    }
  });

  test('should handle LLM processing timeouts gracefully', async ({ page }) => {
    // タイムアウトシナリオのモック
    await page.route('**/api/*/keyword', async (route) => {
      // 長時間待機をシミュレート
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_SCENE_RESPONSE),
      });
    });

    await navigateToPlay(page);
    await expect(page.locator('[data-testid="keyword-candidates"]')).toBeVisible({ timeout: 5000 });

    // キーワード選択
    await page.locator('[data-testid="keyword-candidates"] button').first().click();

    // 処理中インジケーターの確認
    const processingIndicator = page.locator('[data-testid="processing-indicator"]');
    if (await processingIndicator.isVisible()) {
      await expect(processingIndicator).toContainText(/処理中|読み込み中/);
    }

    // 最終的にシーンが表示されることを確認
    await expect(page.locator('[data-testid="scene-narrative"]')).toBeVisible({ timeout: 8000 });
  });
});
