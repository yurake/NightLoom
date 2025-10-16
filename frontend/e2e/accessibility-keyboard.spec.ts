import { test, expect } from '@playwright/test';

test.describe('Keyboard Navigation Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    // モックサーバーの起動（必要に応じて）
    await page.goto('/');
  });

  test('should support Tab navigation through diagnosis flow', async ({ page }) => {
    // ランディングページでのTab順序確認
    await page.keyboard.press('Tab');
    await expect(page.locator(':focus')).toBeVisible();
    
    // キーワード入力フィールドへのフォーカス確認
    const keywordInput = page.locator('input[type="text"]').first();
    if (await keywordInput.isVisible()) {
      await keywordInput.focus();
      await expect(keywordInput).toBeFocused();
      
      // Enterキーでの送信確認
      await keywordInput.fill('テスト');
      await page.keyboard.press('Enter');
    }
  });

  test('should support keyboard navigation in choice selection', async ({ page }) => {
    // シーン画面への遷移（モック環境で）
    await page.goto('/?scene=0');
    
    // 選択肢への順次フォーカス確認
    await page.keyboard.press('Tab');
    
    let focusedChoiceIndex = 0;
    const maxChoices = 4;
    
    // 各選択肢にTabで移動できることを確認
    for (let i = 0; i < maxChoices; i++) {
      const choiceButton = page.locator(`[data-testid^="choice-0-"]`).nth(i);
      if (await choiceButton.isVisible()) {
        await choiceButton.focus();
        await expect(choiceButton).toBeFocused();
        
        // Enterキーまたはスペースキーで選択可能か確認
        await page.keyboard.press('Enter');
        
        // 選択状態の確認
        await expect(choiceButton).toHaveAttribute('aria-pressed', 'true');
        
        // 次の選択肢に移動
        if (i < maxChoices - 1) {
          await page.keyboard.press('Tab');
        }
      }
    }
  });

  test('should support Enter and Space key for choice selection', async ({ page }) => {
    await page.goto('/?scene=0');
    
    const firstChoice = page.locator('[data-testid="choice-0-1"]');
    if (await firstChoice.isVisible()) {
      await firstChoice.focus();
      
      // Enterキーでの選択
      await page.keyboard.press('Enter');
      await expect(firstChoice).toHaveAttribute('aria-pressed', 'true');
      
      // 別の選択肢をスペースキーで選択
      const secondChoice = page.locator('[data-testid="choice-0-2"]');
      if (await secondChoice.isVisible()) {
        await secondChoice.focus();
        await page.keyboard.press('Space');
        await expect(secondChoice).toHaveAttribute('aria-pressed', 'true');
        await expect(firstChoice).toHaveAttribute('aria-pressed', 'false');
      }
    }
  });

  test('should support keyboard navigation to continue button', async ({ page }) => {
    await page.goto('/?scene=0');
    
    // 選択肢を選択
    const firstChoice = page.locator('[data-testid="choice-0-1"]');
    if (await firstChoice.isVisible()) {
      await firstChoice.click();
    }
    
    // 続行ボタンにTabで移動
    await page.keyboard.press('Tab');
    const continueButton = page.locator('[data-testid="continue-button"]');
    
    if (await continueButton.isVisible()) {
      await expect(continueButton).toBeFocused();
      
      // Enterキーで続行
      await page.keyboard.press('Enter');
      
      // 次のシーンまたは結果画面への遷移を確認
      await page.waitForTimeout(1000);
      // 遷移後の要素が表示されることを確認
      await expect(page.locator('main')).toBeVisible();
    }
  });

  test('should support Escape key for canceling actions', async ({ page }) => {
    await page.goto('/');
    
    // モーダルやダイアログが表示された場合のEscapeキー動作を確認
    // （実際のモーダル実装に依存）
    
    // 現在はキーワード入力での動作を確認
    const keywordInput = page.locator('input[type="text"]').first();
    if (await keywordInput.isVisible()) {
      await keywordInput.focus();
      await keywordInput.fill('テストキーワード');
      
      // Escapeキーでクリア（実装依存）
      await page.keyboard.press('Escape');
      
      // フォーカスが維持されることを確認
      await expect(keywordInput).toBeFocused();
    }
  });

  test('should support Arrow keys for choice navigation', async ({ page }) => {
    await page.goto('/?scene=0');
    
    const choices = page.locator('[data-testid^="choice-0-"]');
    const choiceCount = await choices.count();
    
    if (choiceCount > 0) {
      // 最初の選択肢にフォーカス
      await choices.first().focus();
      await expect(choices.first()).toBeFocused();
      
      // Arrow Downで次の選択肢に移動
      if (choiceCount > 1) {
        await page.keyboard.press('ArrowDown');
        await expect(choices.nth(1)).toBeFocused();
        
        // Arrow Upで前の選択肢に戻る
        await page.keyboard.press('ArrowUp');
        await expect(choices.first()).toBeFocused();
      }
    }
  });

  test('should have visible focus indicators', async ({ page }) => {
    await page.goto('/');
    
    // フォーカス可能な要素を順次確認
    const focusableElements = [
      'input[type="text"]',
      'button',
      '[role="button"]',
      '[tabindex="0"]'
    ];
    
    for (const selector of focusableElements) {
      const elements = page.locator(selector);
      const count = await elements.count();
      
      for (let i = 0; i < count; i++) {
        const element = elements.nth(i);
        if (await element.isVisible()) {
          await element.focus();
          
          // フォーカススタイルの確認（outline、box-shadow等）
          const styles = await element.evaluate((el) => {
            const computed = window.getComputedStyle(el);
            return {
              outline: computed.outline,
              boxShadow: computed.boxShadow,
              borderColor: computed.borderColor
            };
          });
          
          // 少なくとも1つのフォーカス表示が適用されていることを確認
          const hasFocusIndicator = 
            styles.outline !== 'none' || 
            styles.boxShadow !== 'none' || 
            styles.borderColor !== 'initial';
          
          expect(hasFocusIndicator).toBeTruthy();
        }
      }
    }
  });

  test('should support skip links for main content', async ({ page }) => {
    await page.goto('/');
    
    // Skip linkの確認（実装されている場合）
    const skipLink = page.locator('a[href="#main-content"], a[href="#main"]');
    
    if (await skipLink.count() > 0) {
      // Tabキーで最初にSkip linkにフォーカスが当たることを確認
      await page.keyboard.press('Tab');
      await expect(skipLink).toBeFocused();
      
      // Enterキーでメインコンテンツにジャンプ
      await page.keyboard.press('Enter');
      
      const mainContent = page.locator('#main-content, #main, main');
      await expect(mainContent).toBeFocused();
    }
  });

  test('should maintain focus order in result screen', async ({ page }) => {
    // 結果画面への直接アクセス（モック環境）
    await page.goto('/result?session=test-session-id');
    
    // 結果画面でのTab順序確認
    await page.keyboard.press('Tab');
    
    const focusableElements = page.locator(
      'button, [tabindex="0"], a[href], input, select, textarea, [role="button"]'
    );
    
    const count = await focusableElements.count();
    
    for (let i = 0; i < count; i++) {
      const element = focusableElements.nth(i);
      if (await element.isVisible()) {
        await expect(element).toBeFocused();
        
        if (i < count - 1) {
          await page.keyboard.press('Tab');
        }
      }
    }
  });

  test('should support restart diagnosis via keyboard', async ({ page }) => {
    await page.goto('/result?session=test-session-id');
    
    // 「もう一度診断する」ボタンの確認
    const restartButton = page.locator('button:has-text("もう一度"), button:has-text("診断")');
    
    if (await restartButton.count() > 0) {
      await restartButton.focus();
      await expect(restartButton).toBeFocused();
      
      // Enterキーで再診断開始
      await page.keyboard.press('Enter');
      
      // トップページへの遷移確認
      await page.waitForURL('/');
      await expect(page).toHaveURL('/');
    }
  });
});
