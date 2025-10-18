import { test, expect, type Page } from '@playwright/test';

type BootstrapFixture = {
  sessionId: string;
  axes: Array<{
    id: string;
    name: string;
    description: string;
    direction: string;
  }>;
  keywordCandidates: string[];
  initialCharacter: string;
  themeId: string;
  fallbackUsed?: boolean;
};

type SceneChoice = {
  id: string;
  text: string;
  weights: Record<string, number>;
};

const DEFAULT_BOOTSTRAP_RESPONSE: BootstrapFixture = {
  sessionId: '550e8400-e29b-41d4-a716-446655440000',
  axes: [
    {
      id: 'curiosity_focus',
      name: '好奇心と集中のバランス',
      description: '探求心と集中力のバランスを測定する指標',
      direction: '好奇心 ⟷ 集中力',
    },
  ],
  keywordCandidates: ['冒険', '創造', '調和', '探求'],
  initialCharacter: 'あ',
  themeId: 'adventure',
};

const SCENE_CHOICE_TEMPLATES: SceneChoice[] = [
  { id: 'choice-1', text: '星明かりの道を進む', weights: { curiosity: 0.6, harmony: 0.4 } },
  { id: 'choice-2', text: '静寂に耳を傾ける', weights: { harmony: 0.7, logic: 0.3 } },
  { id: 'choice-3', text: '光の方へ進む', weights: { creativity: 0.5, curiosity: 0.5 } },
  { id: 'choice-4', text: 'いったん立ち止まる', weights: { logic: 0.7, resilience: 0.3 } },
];

const cloneBootstrapFixture = (fixture: BootstrapFixture): BootstrapFixture => ({
  ...fixture,
  axes: fixture.axes.map((axis) => ({ ...axis })),
  keywordCandidates: [...fixture.keywordCandidates],
});

const cloneSceneChoices = (): SceneChoice[] =>
  SCENE_CHOICE_TEMPLATES.map((choice) => ({
    id: choice.id,
    text: choice.text,
    weights: { ...choice.weights },
  }));

const jsonResponse = (data: unknown) => ({
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify(data),
});

let lastBootstrapResponse: BootstrapFixture = cloneBootstrapFixture(DEFAULT_BOOTSTRAP_RESPONSE);

const setBootstrapFixture = (fixture: BootstrapFixture) => {
  lastBootstrapResponse = cloneBootstrapFixture(fixture);
};

const createSceneResponse = (keyword: string) => ({
  sessionId: lastBootstrapResponse.sessionId,
  scene: {
    sceneIndex: 1,
    themeId: lastBootstrapResponse.themeId,
    narrative: `${keyword}の世界が始まります`,
    choices: cloneSceneChoices(),
  },
  fallbackUsed: lastBootstrapResponse.fallbackUsed ?? false,
});

async function setupDefaultApiMocks(page: Page) {
  setBootstrapFixture(DEFAULT_BOOTSTRAP_RESPONSE);

  await page.route('**/api/sessions/start', async (route) => {
    setBootstrapFixture(DEFAULT_BOOTSTRAP_RESPONSE);
    await new Promise((resolve) => setTimeout(resolve, 150));
    await route.fulfill(jsonResponse(lastBootstrapResponse));
  });

  await page.route('**/api/sessions/*/keyword', async (route) => {
    let keyword = lastBootstrapResponse.keywordCandidates[0];

    try {
      const parsedBody = route.request().postDataJSON();
      if (parsedBody && typeof parsedBody.keyword === 'string') {
        keyword = parsedBody.keyword;
      }
    } catch {
      const rawBody = route.request().postData();
      if (rawBody) {
        try {
          const parsed = JSON.parse(rawBody);
          if (parsed && typeof parsed.keyword === 'string') {
            keyword = parsed.keyword;
          }
        } catch {
          // no-op
        }
      }
    }

    const responseBody = createSceneResponse(keyword);
    await route.fulfill(jsonResponse(responseBody));
  });
}

async function navigateToPlay(page: Page) {
  await page.getByRole('button', { name: 'Adventure' }).click();
  await page.getByRole('button', { name: '診断を開始' }).click();
  await expect(page).toHaveURL(/\/play$/);
}

async function waitForKeywordCandidates(page: Page) {
  await expect(page.locator('[data-testid="keyword-candidates"]')).toBeVisible({
    timeout: 10_000,
  });
}

test.describe('NightLoom Bootstrap Flow', () => {
  test.beforeEach(async ({ page }) => {
    await setupDefaultApiMocks(page);
    await page.goto('/');
  });

  test('should complete bootstrap flow with suggested keyword', async ({ page }) => {
    await navigateToPlay(page);
    await waitForKeywordCandidates(page);

    await expect(page.locator('[data-testid="initial-character"]')).toBeVisible();

    const keywordButtons = page.locator('[data-testid="keyword-candidates"] button');
    await expect(keywordButtons).toHaveCount(4);

    for (let i = 0; i < 4; i += 1) {
      await expect(keywordButtons.nth(i)).toBeVisible();
      await expect(keywordButtons.nth(i)).toHaveText(/^.+$/);
    }

    const firstKeywordButton = keywordButtons.first();
    const selectedKeyword =
      (await firstKeywordButton.locator('span').textContent())?.trim() ?? '';
    await firstKeywordButton.click();

    await expect(page.locator('[data-testid="scene-narrative"]')).toBeVisible({ timeout: 5000 });
    if (selectedKeyword) {
      await expect(page.locator('[data-testid="scene-narrative"]')).toContainText(selectedKeyword);
    }

    await expect(page.locator('[data-testid="scene-index"]')).toHaveText('1');
    await expect(page.locator('[data-testid="choice-options"] button')).toHaveCount(4);
    await expect(page.locator('[data-testid="progress-indicator"]')).toBeVisible();
    await expect(page.locator('[data-testid="progress-text"]')).toContainText('1/4');
  });

  test('should complete bootstrap flow with custom keyword', async ({ page }) => {
    await navigateToPlay(page);
    await waitForKeywordCandidates(page);

    const customInput = page.locator('[data-testid="custom-keyword-input"]');
    await expect(customInput).toBeVisible();

    const customKeyword = 'テスト';
    await customInput.fill(customKeyword);

    const submitButton = page.locator('[data-testid="submit-custom-keyword"]');
    await expect(submitButton).toBeEnabled();
    await submitButton.click();

    await expect(page.locator('[data-testid="scene-narrative"]')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('[data-testid="scene-narrative"]')).toContainText(customKeyword);
  });

  test('should handle bootstrap loading states', async ({ page }) => {
    await navigateToPlay(page);

    await page.waitForSelector('[data-testid="bootstrap-loading"]', { state: 'visible' });

    const loader = page.locator('[data-testid="bootstrap-loading"]');
    await expect(loader).toBeHidden({ timeout: 10_000 });

    await waitForKeywordCandidates(page);
  });

  test('should validate custom keyword input', async ({ page }) => {
    await navigateToPlay(page);
    await waitForKeywordCandidates(page);

    const customInput = page.locator('[data-testid="custom-keyword-input"]');
    const submitButton = page.locator('[data-testid="submit-custom-keyword"]');

    await customInput.fill('');
    await expect(submitButton).toBeDisabled();

    await customInput.fill('有効');
    await expect(submitButton).toBeEnabled();

    await customInput.fill('あ'.repeat(21));
    const truncatedValue = await customInput.inputValue();
    expect(Array.from(truncatedValue).length).toBe(20);
    await expect(submitButton).toBeEnabled();

    await customInput.fill('あ'.repeat(20));
    await expect(submitButton).toBeEnabled();
  });

  test('should handle network errors gracefully', async ({ page }) => {
    let attempts = 0;
    await page.route('**/api/sessions/start', (route) => {
      attempts += 1;
      if (attempts <= 4) {
        route.abort('failed');
        return;
      }
      route.fallback();
    });

    await navigateToPlay(page);

    await expect(page.locator('[data-testid="bootstrap-error"]')).toBeVisible({ timeout: 10_000 });
    const retryButton = page.locator('[data-testid="retry-button"]');
    await expect(retryButton).toBeVisible();
    await retryButton.click();

    await waitForKeywordCandidates(page);
  });

  test('should maintain theme consistency', async ({ page }) => {
    await navigateToPlay(page);
    await waitForKeywordCandidates(page);

    const themeContainer = page.locator('[data-testid="theme-container"]');
    const initialTheme = await themeContainer.getAttribute('data-theme');
    expect(initialTheme).toBe('adventure');

    await page.locator('[data-testid="keyword-candidates"] button').first().click();

    await expect(page.locator('[data-testid="scene-container"]')).toBeVisible({ timeout: 5000 });
    const sceneTheme = await page.locator('[data-testid="scene-container"]').getAttribute('data-theme');
    expect(sceneTheme).toBe(initialTheme);
  });

  test('should meet performance requirements', async ({ page }) => {
    const startTime = Date.now();

    await navigateToPlay(page);
    await waitForKeywordCandidates(page);

    const bootstrapTime = Date.now() - startTime;
    expect(bootstrapTime).toBeLessThan(2000);

    const logs = await page.evaluate(() => (window as any).performanceLogs || []);
    const performanceErrors = logs.filter(
      (log: any) => log?.level === 'error' && typeof log.message === 'string' && log.message.includes('performance'),
    );
    expect(performanceErrors).toHaveLength(0);
  });

  test('should support keyboard navigation', async ({ page }) => {
    await navigateToPlay(page);
    await waitForKeywordCandidates(page);

    const buttons = page.locator('[data-testid="keyword-candidates"] button');
    await buttons.first().focus();

    await page.keyboard.press('ArrowRight');
    await expect(buttons.nth(1)).toBeFocused();

    await page.keyboard.press('Enter');
    await expect(page.locator('[data-testid="scene-narrative"]')).toBeVisible({ timeout: 5000 });
  });

  test('should handle fallback scenarios', async ({ page }) => {
    await page.route('**/api/sessions/start', async (route) => {
      const fallbackResponse: BootstrapFixture = {
        sessionId: '123e4567-e89b-12d3-a456-426614174001',
        axes: [
          {
            id: 'stability_imagination',
            name: '安定と想像力の指標',
            description: '安定志向と想像力のバランスを測定する指標',
            direction: '安定志向 ⟷ 想像力',
          },
        ],
        keywordCandidates: ['希望', '挑戦', '成長', '発見'],
        initialCharacter: 'き',
        themeId: 'fallback',
        fallbackUsed: true,
      };

      setBootstrapFixture(fallbackResponse);
      await route.fulfill(jsonResponse(fallbackResponse));
    });

    await navigateToPlay(page);
    await waitForKeywordCandidates(page);

    await expect(page.locator('[data-testid="keyword-candidates"] button')).toHaveCount(4);

    const themeContainer = page.locator('[data-testid="theme-container"]');
    await expect(themeContainer).toHaveAttribute('data-theme', 'fallback');

    await page.locator('[data-testid="keyword-candidates"] button').first().click();
    await expect(page.locator('[data-testid="scene-narrative"]')).toBeVisible({ timeout: 5000 });
  });

  test('should display session ID for debugging', async ({ page }) => {
    await navigateToPlay(page);
    await waitForKeywordCandidates(page);

    const sessionInfo = page.locator('[data-testid="session-debug-info"]');
    if (await sessionInfo.isVisible()) {
      const sessionId = await sessionInfo.getAttribute('data-session-id');
      expect(sessionId).toMatch(
        /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i,
      );
    }
  });
});

test.describe('Bootstrap Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await setupDefaultApiMocks(page);
    await page.goto('/');
  });

  test('should meet accessibility standards', async ({ page }) => {
    await navigateToPlay(page);
    await waitForKeywordCandidates(page);

    const container = page.locator('[data-testid="keyword-candidates"]');
    await expect(container).toHaveAttribute('role', 'radiogroup');
    await expect(container).toHaveAttribute('aria-label', /キーワード/);

    const buttons = page.locator('[data-testid="keyword-candidates"] button');
    for (let i = 0; i < 4; i += 1) {
      const button = buttons.nth(i);
      await expect(button).toHaveAttribute('aria-label', /キーワード候補/);
      await expect(button).toHaveAttribute('type', 'button');
    }

    const customInput = page.locator('[data-testid="custom-keyword-input"]');
    await expect(customInput).toHaveAttribute('aria-label', /キーワード/);
    await expect(customInput).toHaveAttribute('maxlength', '20');
  });

  test('should support screen reader announcements', async ({ page }) => {
    await navigateToPlay(page);

    const politeRegion = page.locator('[aria-live="polite"]');
    const liveRegionsCount = await politeRegion.count();
    expect(liveRegionsCount).toBeGreaterThan(0);

    const loader = page.locator('[data-testid="bootstrap-loading"]');
    if (await loader.isVisible()) {
      const loadingText = (await loader.textContent()) ?? '';
      expect(loadingText).toContain('読み込み中');
    }

    await waitForKeywordCandidates(page);
  });
});
