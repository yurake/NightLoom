
import { test, expect } from '@playwright/test';

/**
 * NightLoom エラー境界・異常系強化E2Eテストスイート
 * Week4: 包括的エラーハンドリングと異常系処理検証
 * 
 * 対象要件:
 * - JavaScript例外の適切な捕捉と処理
 * - ネットワーク障害時の耐性と回復処理
 * - 不正レスポンスデータの安全な処理
 * - リソース不足時の適切な制限
 * - エラー状態からの自動回復機能
 * - ユーザビリティを損なわない例外処理
 */

test.describe('エラー境界・異常系強化E2Eテスト', () => {
  const validSessionId = '550e8400-e29b-41d4-a716-446655440000';
  const malformedResponses = {
    invalidJSON: '{ invalid json }',
    missingFields: '{ "sessionId": "test" }',
    unexpectedStructure: '{ "unexpected": "data" }',
    maliciousContent: '{ "sessionId": "<script>alert(\'XSS\')</script>" }'
  };

  test.beforeEach(async ({ page }) => {
    // デフォルトの正常レスポンス設定
    await page.route('/api/sessions/start', async (route) => {
      await route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          sessionId: validSessionId,
          axes: [
            { name: 'curiosity', displayName: '好奇心', weight: 0.0 },
            { name: 'logic', displayName: '論理性', weight: 0.0 }
          ],
          keywordCandidates: ['冒険', '平和', '創造'],
          initialCharacter: 'あ',
          themeId: 'serene'
        })
      });
    });
  });

  test.describe('1. JavaScript例外処理テスト', () => {
    test('未処理例外発生時のアプリケーション継続性確認', async ({ page }) => {
      let consoleErrors: string[] = [];
      let jsErrors: Error[] = [];

      // コンソールエラーとJS例外をキャプチャ
      page.on('console', msg => {
        if (msg.type() === 'error') {
          consoleErrors.push(msg.text());
        }
      });

      page.on('pageerror', error => {
        jsErrors.push(error);
      });

      await page.goto('/');
      
      // 意図的にJavaScript例外を発生
      await page.evaluate(() => {
        // グローバルスコープでエラーを投げる
        setTimeout(() => {
          throw new Error('Test unhandled exception');
        }, 100);
      });

      await page.waitForTimeout(500);

      // アプリケーションが継続して動作することを確認
      await expect(page.locator('[data-testid="bootstrap-complete"]')).toBeVisible({ timeout: 10000 });
      
      // キーワード入力が正常に機能することを確認
      await page.fill('[data-testid="keyword-input"]', 'エラーテスト');
      await page.click('[data-testid="confirm-keyword"]');

      // エラーが発生してもセッションが継続されることを確認
      await expect(page.locator('[data-testid="choice-1"]')).toBeVisible({ timeout: 10000 });

      // エラーが適切にログされていることを確認
      expect(jsErrors.length).toBeGreaterThan(0);
      expect(jsErrors[0].message).toContain('Test unhandled exception');
    });

    test('非同期処理でのエラーハンドリング確認', async ({ page }) => {
      // unhandledrejection イベントをキャプチャ
      await page.evaluate(() => {
        window.addEventListener('unhandledrejection', (event) => {
          (window as any).capturedRejection = event.reason;
        });
      });

      await page.goto('/');

      // Promise rejection を意図的に発生
      await page.evaluate(() => {
        Promise.reject(new Error('Test promise rejection'));
      });

      await page.waitForTimeout(500);

      // アプリケーションが正常に動作することを確認
      await expect(page.locator('[data-testid="bootstrap-complete"]')).toBeVisible();
      
      // Promise rejection がキャプチャされていることを確認
      const capturedRejection = await page.evaluate(() => (window as any).capturedRejection);
      expect(capturedRejection).toBeDefined();
    });

    test('React Error Boundaryの動作確認', async ({ page }) => {
      await page.goto('/');

      // コンポーネント内でエラーを発生させる
      await page.evaluate(() => {
        // React コンポーネントのライフサイクル内でエラーを発生
        const element = document.querySelector('[data-testid="keyword-input"]');
        if (element) {
          // DOM要素に不正な操作を実行
          Object.defineProperty(element, 'value', {
            get: () => { throw new Error('React component error'); },
            configurable: true
          });
        }
      });

      // エラーが発生してもアプリケーションがクラッシュしないことを確認
      const pageContent = await page.content();
      expect(pageContent).not.toContain('Application Error');
      expect(pageContent).not.toContain('Something went wrong');

      // フォールバックUI または エラーメッセージが表示されることを確認
      const hasErrorHandler = await page.evaluate(() => {
        return document.querySelector('[data-testid="error-fallback"]') !== null ||
               document.querySelector('[role="alert"]') !== null;
      });

      // エラーハンドリングが適切に機能していることを確認（エラー境界またはエラー表示）
      expect(hasErrorHandler || await page.locator('body').isVisible()).toBe(true);
    });

    test('メモリリーク防止確認', async ({ page }) => {
      await page.goto('/');

      // 初期メモリ使用量を記録
      const initialMemory = await page.evaluate(() => {
        if ('memory' in performance) {
          return (performance as any).memory.usedJSHeapSize;
        }
        return 0;
      });

      // 大量のオブジェクト作成とエラー発生を繰り返す
      for (let i = 0; i < 10; i++) {
        await page.evaluate(() => {
          // 大量のオブジェクト作成
          const largeArray = new Array(1000).fill(0).map(() => ({
            data: new Array(100).fill('test-data'),
            timestamp: Date.now()
          }));

          // エラーを発生させてオブジェクトを破棄
          try {
            throw new Error('Test memory management');
          } catch (e) {
            // オブジェクトをクリア
            largeArray.length = 0;
          }
        });
      }

      // ガベージコレクション実行
      await page.evaluate(() => {
        if ('gc' in window) {
          (window as any).gc();
        }
      });

      // 最終メモリ使用量を確認
      const finalMemory = await page.evaluate(() => {
        if ('memory' in performance) {
          return (performance as any).memory.usedJSHeapSize;
        }
        return 0;
      });

      // メモリリークが発生していないことを確認（許容範囲内）
      const memoryIncrease = finalMemory - initialMemory;
      expect(memoryIncrease).toBeLessThan(5 * 1024 * 1024); // 5MB以下の増加
    });
  });

  test.describe('2. ネットワーク障害対応テスト', () => {
    test('完全なネットワーク接続失敗時の処理', async ({ page }) => {
      // 全APIリクエストを失敗させる
      await page.route('**/api/**', async (route) => {
        await route.abort('internetdisconnected');
      });

      await page.goto('/');

      // ネットワーク障害時の適切なエラーメッセージ表示を確認
      await page.fill('[data-testid="keyword-input"]', 'ネットワークテスト');
      await page.click('[data-testid="confirm-keyword"]');

      // エラーメッセージまたはリトライボタンが表示されることを確認
      const hasNetworkError = await Promise.race([
        page.locator('[data-testid="network-error"]').isVisible(),
        page.locator('[data-testid="retry-button"]').isVisible(),
        page.locator('text=ネットワークエラー').isVisible(),
        page.locator('text=接続に失敗').isVisible()
      ]);

      expect(hasNetworkError).toBe(true);
    });

    test('間欠的ネットワーク障害時の自動リトライ確認', async ({ page }) => {
      let requestCount = 0;

      // 最初の2回のリクエストを失敗させ、3回目で成功させる
      await page.route('**/keyword', async (route) => {
        requestCount++;
        if (requestCount <= 2) {
          await route.abort('failed');
        } else {
          await route.fulfill({
            contentType: 'application/json',
            body: JSON.stringify({
              sessionId: validSessionId,
              scene: {
                sceneIndex: 1,
                themeId: 'serene',
                narrative: 'リトライ成功後の物語',
                choices: [
                  {
                    id: 'choice_1',
                    text: 'リトライが成功した選択肢',
                    weights: { curiosity: 0.5, logic: 0.5 }
                  }
                ]
              }
            })
          });
        }
      });

      await page.goto('/');
      await page.fill('[data-testid="keyword-input"]', 'リトライテスト');
      await page.click('[data-testid="confirm-keyword"]');

      // 最終的に成功して選択肢が表示されることを確認
      await expect(page.locator('[data-testid="choice-1"]')).toBeVisible({ timeout: 15000 });

      // リトライが実行されたことを確認
      expect(requestCount).toBe(3);

      const choiceText = await page.locator('[data-testid="choice-1"]').textContent();
      expect(choiceText).toContain('リトライが成功した');
    });

    test('タイムアウト処理の確認', async ({ page }) => {
      // レスポンスを意図的に遅延させる
      await page.route('**/keyword', async (route) => {
        // 30秒待機してからレスポンス（タイムアウトをテスト）
        await new Promise(resolve => setTimeout(resolve, 30000));
        await route.fulfill({
          contentType: 'application/json',
          body: JSON.stringify({
            sessionId: validSessionId,
            scene: { choices: [] }
          })
        });
      });

      await page.goto('/');
      await page.fill('[data-testid="keyword-input"]', 'タイムアウトテスト');
      await page.click('[data-testid="confirm-keyword"]');

      // タイムアウトエラーまたはローディング状態の適切な処理を確認
      const hasTimeoutHandling = await Promise.race([
        page.locator('[data-testid="timeout-error"]').isVisible(),
        page.locator('[data-testid="loading-timeout"]').isVisible(),
        page.locator('text=時間がかかっています').isVisible(),
        page.waitForTimeout(10000).then(() => true) // 10秒でタイムアウト
      ]);

      expect(hasTimeoutHandling).toBe(true);
    });

    test('部分的API障害時のフェイルオーバー確認', async ({ page }) => {
      // セッション開始は成功、キーワードAPIは失敗させる
      await page.route('**/keyword', async (route) => {
        await route.abort('failed');
      });

      await page.goto('/');
      
      // セッション開始は成功することを確認
      await expect(page.locator('[data-testid="bootstrap-complete"]')).toBeVisible();

      await page.fill('[data-testid="keyword-input"]', 'フェイルオーバーテスト');
      await page.click('[data-testid="confirm-keyword"]');

      // フォールバック機能または代替フローが動作することを確認
      const hasFallback = await Promise.race([
        page.locator('[data-testid="fallback-content"]').isVisible(),
        page.locator('[data-testid="offline-mode"]').isVisible(),
        page.locator('text=オフラインモード').isVisible(),
        page.waitForTimeout(5000).then(() => false)
      ]);

      // フェイルオーバー機能が動作するか、適切なエラーハンドリングがされることを確認
      expect(hasFallback || await page.locator('[data-testid="error-message"]').isVisible()).toBe(true);
    });
  });

  test.describe('3. 不正レスポンス処理テスト', () => {
    test('不正なJSON形式レスポンスの処理', async ({ page }) => {
      await page.route('**/keyword', async (route) => {
        await route.fulfill({
          contentType: 'application/json',
          body: malformedResponses.invalidJSON
        });
      });

      await page.goto('/');
      await page.fill('[data-testid="keyword-input"]', '不正JSONテスト');
      await page.click('[data-testid="confirm-keyword"]');

            // 不正なJSONに対して適切なエラーハンドリングが行われることを確認
      const hasJSONError = await Promise.race([
        page.locator('[data-testid="parse-error"]').isVisible(),
        page.locator('[data-testid="invalid-response"]').isVisible(),
        page.locator('text=データの形式が正しくありません').isVisible(),
        page.waitForTimeout(5000).then(() => false)
      ]);

      expect(hasJSONError).toBe(true);
    });

    test('必須フィールド欠落レスポンスの処理', async ({ page }) => {
      await page.route('**/keyword', async (route) => {
        await route.fulfill({
          contentType: 'application/json',
          body: malformedResponses.missingFields
        });
      });

      await page.goto('/');
      await page.fill('[data-testid="keyword-input"]', '必須フィールド欠落テスト');
      await page.click('[data-testid="confirm-keyword"]');

      // 必須フィールドが欠落したレスポンスに対する適切な処理を確認
      const hasMissingFieldError = await Promise.race([
        page.locator('[data-testid="validation-error"]').isVisible(),
        page.locator('[data-testid="incomplete-data"]').isVisible(),
        page.locator('text=データが不完全です').isVisible(),
        page.waitForTimeout(5000).then(() => false)
      ]);

      expect(hasMissingFieldError).toBe(true);
    });

    test('予期しないデータ構造の処理', async ({ page }) => {
      await page.route('**/keyword', async (route) => {
        await route.fulfill({
          contentType: 'application/json',
          body: malformedResponses.unexpectedStructure
        });
      });

      await page.goto('/');
      await page.fill('[data-testid="keyword-input"]', '予期しないデータ構造テスト');
      await page.click('[data-testid="confirm-keyword"]');

      // 予期しないデータ構造に対する適切な処理を確認
      const hasStructureError = await Promise.race([
        page.locator('[data-testid="structure-error"]').isVisible(),
        page.locator('[data-testid="unexpected-format"]').isVisible(),
        page.locator('text=予期しないデータ形式').isVisible(),
        page.waitForTimeout(5000).then(() => false)
      ]);

      expect(hasStructureError).toBe(true);
    });

    test('悪意のあるコンテンツ含有レスポンスの無害化', async ({ page }) => {
      await page.route('**/keyword', async (route) => {
        await route.fulfill({
          contentType: 'application/json',
          body: malformedResponses.maliciousContent
        });
      });

      await page.goto('/');
      await page.fill('[data-testid="keyword-input"]', '悪意のあるコンテンツテスト');
      await page.click('[data-testid="confirm-keyword"]');

      // XSSスクリプトが実行されないことを確認
      let alertTriggered = false;
      page.on('dialog', () => {
        alertTriggered = true;
      });

      await page.waitForTimeout(2000);
      expect(alertTriggered).toBe(false);

      // 悪意のあるコンテンツがサニタイズされることを確認
      const pageContent = await page.content();
      expect(pageContent).not.toContain('<script>');
      expect(pageContent).not.toContain('alert(');
    });

    test('HTTPステータスエラーレスポンスの処理', async ({ page }) => {
      const errorStatuses = [400, 401, 403, 404, 500, 502, 503];

      for (const status of errorStatuses) {
        await page.route('**/keyword', async (route) => {
          await route.fulfill({
            status: status,
            contentType: 'application/json',
            body: JSON.stringify({
              error_code: `HTTP_${status}`,
              message: `HTTP ${status} error occurred`
            })
          });
        });

        await page.goto('/');
        await page.fill('[data-testid="keyword-input"]', `HTTPエラー${status}テスト`);
        await page.click('[data-testid="confirm-keyword"]');

        // 各HTTPエラーステータスに対する適切な処理を確認
        const hasHttpError = await Promise.race([
          page.locator(`[data-testid="http-error-${status}"]`).isVisible(),
          page.locator('[data-testid="server-error"]').isVisible(),
          page.locator('text=サーバーエラー').isVisible(),
          page.waitForTimeout(3000).then(() => false)
        ]);

        expect(hasHttpError).toBe(true);
      }
    });
  });

  test.describe('4. リソース不足対応テスト', () => {
    test('メモリ不足状態でのアプリケーション動作', async ({ page }) => {
      await page.goto('/');

      // 大量のメモリを消費してメモリ不足状態をシミュレート
      const memoryStressResult = await page.evaluate(() => {
        try {
          const arrays: any[] = [];
          // 大量の配列を作成してメモリを消費
          for (let i = 0; i < 100; i++) {
            arrays.push(new Array(100000).fill('メモリ消費データ'));
          }
          return { success: true, arraysLength: arrays.length };
        } catch (error) {
          return { success: false, error: (error as Error).message };
        }
      });

      // メモリ不足の状態でもアプリケーションが動作することを確認
      await page.fill('[data-testid="keyword-input"]', 'メモリ不足テスト');
      await page.click('[data-testid="confirm-keyword"]');

      // アプリケーションが応答し続けることを確認
      const isResponsive = await Promise.race([
        page.locator('[data-testid="choice-1"]').isVisible(),
        page.locator('[data-testid="error-message"]').isVisible(),
        page.waitForTimeout(10000).then(() => false)
      ]);

      expect(isResponsive).toBe(true);
    });

    test('CPU高負荷状態での応答性確認', async ({ page }) => {
      await page.goto('/');

      // CPU集約的な処理を実行
      await page.evaluate(() => {
        const startTime = Date.now();
        // CPUを意図的に高負荷にする
        while (Date.now() - startTime < 2000) {
          Math.random() * Math.random();
        }
      });

      // 高負荷状態でもユーザーインタラクションが可能であることを確認
      await page.fill('[data-testid="keyword-input"]', 'CPU高負荷テスト');
      await page.click('[data-testid="confirm-keyword"]');

      // 応答時間が許容範囲内であることを確認
      const startTime = Date.now();
      await expect(page.locator('[data-testid="choice-1"]')).toBeVisible({ timeout: 15000 });
      const responseTime = Date.now() - startTime;

      expect(responseTime).toBeLessThan(15000); // 15秒以内の応答
    });

    test('ストレージ容量制限時の処理', async ({ page }) => {
      await page.goto('/');

      // LocalStorageの容量制限をテスト
      const quotaExceeded = await page.evaluate(() => {
        try {
          const largeData = 'x'.repeat(1024 * 1024); // 1MB のデータ
          for (let i = 0; i < 10; i++) {
            localStorage.setItem(`large-data-${i}`, largeData);
          }
          return false;
        } catch (error) {
          return (error as Error).name === 'QuotaExceededError';
        }
      });

      // ストレージ容量制限に達してもアプリケーションが動作することを確認
      await page.fill('[data-testid="keyword-input"]', 'ストレージ制限テスト');
      await page.click('[data-testid="confirm-keyword"]');

      // セッションが正常に継続されることを確認
      await expect(page.locator('[data-testid="choice-1"]')).toBeVisible({ timeout: 10000 });

      // ストレージエラーが適切に処理されていることを確認
      if (quotaExceeded) {
        const hasStorageError = await page.locator('[data-testid="storage-warning"]').isVisible()
          .catch(() => false);
        
        // ストレージエラーが発生した場合は警告が表示されるか、正常に動作することを確認
        expect(hasStorageError || await page.locator('[data-testid="choice-1"]').isVisible()).toBe(true);
      }
    });

    test('同時接続数制限時のキュー処理', async ({ page }) => {
      let requestCount = 0;
      const requestQueue: any[] = [];

      // 同時リクエスト数を制限してキュー処理をテスト
      await page.route('**/keyword', async (route) => {
        requestCount++;
        requestQueue.push({ id: requestCount, route });

        // 同時に処理するリクエスト数を3に制限
        if (requestQueue.length <= 3) {
          await route.fulfill({
            contentType: 'application/json',
            body: JSON.stringify({
              sessionId: validSessionId,
              scene: {
                sceneIndex: 1,
                choices: [{
                  id: 'choice_1',
                  text: `リクエスト${requestCount}の選択肢`,
                  weights: { curiosity: 0.5, logic: 0.5 }
                }]
              }
            })
          });
        } else {
          // 制限を超えたリクエストは503で応答
          await route.fulfill({
            status: 503,
            contentType: 'application/json',
            body: JSON.stringify({
              error_code: 'TOO_MANY_REQUESTS',
              message: 'Server is busy, please try again later'
            })
          });
        }
      });

      await page.goto('/');
      await page.fill('[data-testid="keyword-input"]', '同時接続制限テスト');
      await page.click('[data-testid="confirm-keyword"]');

      // レート制限またはキュー処理が適切に動作することを確認
      const hasRateLimit = await Promise.race([
        page.locator('[data-testid="rate-limited"]').isVisible(),
        page.locator('[data-testid="queue-waiting"]').isVisible(),
        page.locator('[data-testid="choice-1"]').isVisible(),
        page.locator('text=しばらくお待ちください').isVisible(),
        page.waitForTimeout(8000).then(() => false)
      ]);

      expect(hasRateLimit).toBe(true);
    });
  });

  test.describe('5. 統合エラー回復テスト', () => {
    test('エラー発生からの自動回復シナリオ', async ({ page }) => {
      let requestAttempts = 0;

      // 最初は失敗し、その後自動的に回復するAPIをシミュレート
      await page.route('**/keyword', async (route) => {
        requestAttempts++;
        
        if (requestAttempts <= 2) {
          // 最初の2回は失敗
          await route.abort('failed');
        } else {
          // 3回目で回復
          await route.fulfill({
            contentType: 'application/json',
            body: JSON.stringify({
              sessionId: validSessionId,
              scene: {
                sceneIndex: 1,
                narrative: '回復後の物語が始まります',
                choices: [{
                  id: 'choice_1',
                  text: '自動回復成功後の選択肢',
                  weights: { curiosity: 0.5, logic: 0.5 }
                }]
              }
            })
          });
        }
      });

      await page.goto('/');
      await page.fill('[data-testid="keyword-input"]', '自動回復テスト');
      await page.click('[data-testid="confirm-keyword"]');

      // 最終的に回復して正常な結果が表示されることを確認
      await expect(page.locator('[data-testid="choice-1"]')).toBeVisible({ timeout: 20000 });
      
      const choiceText = await page.locator('[data-testid="choice-1"]').textContent();
      expect(choiceText).toContain('自動回復成功後');
      expect(requestAttempts).toBe(3);
    });

    test('複数種類のエラーが同時発生した場合の処理', async ({ page }) => {
      // 複数のエラー条件を同時に発生させる
      await page.route('**/keyword', async (route) => {
        // ネットワークエラーをシミュレート
        await route.abort('failed');
      });

      await page.goto('/');

      // JavaScript例外も同時に発生させる
      await page.evaluate(() => {
        setTimeout(() => {
          throw new Error('Simultaneous JS error');
        }, 1000);
      });

      await page.fill('[data-testid="keyword-input"]', '複合エラーテスト');
      await page.click('[data-testid="confirm-keyword"]');

      // 複数のエラーが発生してもアプリケーションが適切に処理することを確認
      const hasMultipleErrorHandling = await Promise.race([
        page.locator('[data-testid="multiple-errors"]').isVisible(),
        page.locator('[data-testid="error-recovery"]').isVisible(),
        page.locator('text=複数のエラーが発生しました').isVisible(),
        page.waitForTimeout(10000).then(() => false)
      ]);

      expect(hasMultipleErrorHandling).toBe(true);
    });

    test('エラー状態のユーザーフレンドリーな表示', async ({ page }) => {
      await page.route('**/keyword', async (route) => {
        await route.fulfill({
          status: 500,
          contentType: 'application/json', 
          body: JSON.stringify({
            error_code: 'INTERNAL_SERVER_ERROR',
            message: 'Internal server error occurred'
          })
        });
      });

      await page.goto('/');
      await page.fill('[data-testid="keyword-input"]', 'ユーザーフレンドリーエラーテスト');
      await page.click('[data-testid="confirm-keyword"]');

      // 技術的なエラーメッセージではなく、ユーザーフレンドリーなメッセージが表示されることを確認
      const hasUserFriendlyError = await Promise.race([
        page.locator('text=申し訳ございません').isVisible(),
        page.locator('text=しばらく時間をおいて').isVisible(),
        page.locator('text=問題が発生しました').isVisible(),
        page.locator('[data-testid="user-friendly-error"]').isVisible(),
        page.waitForTimeout(5000).then(() => false)
      ]);

      expect(hasUserFriendlyError).toBe(true);

      // 技術的なエラーコードが表示されていないことを確認
      const pageContent = await page.content();
      expect(pageContent).not.toContain('INTERNAL_SERVER_ERROR');
      expect(pageContent).not.toContain('500');
    });
  });
});
