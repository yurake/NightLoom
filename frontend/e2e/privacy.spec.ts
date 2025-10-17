
import { test, expect } from '@playwright/test';

/**
 * NightLoom プライバシー・データ削除検証E2Eテストスイート
 * Week2: プライバシー保護要件の包括的検証
 * 
 * 対象要件:
 * - 30秒自動削除機能
 * - ブラウザストレージの完全クリア
 * - 履歴・キャッシュからの情報漏洩防止
 * - データ完全削除の実動作確認
 * - セッション終了時の痕跡除去
 * - プライバシー規制準拠
 */

test.describe('プライバシー・データ削除検証E2Eテスト', () => {
  const testSessionId = '550e8400-e29b-41d4-a716-446655440000';
  const sensitiveData = {
    keyword: '秘密の思い出',
    personalChoice: '家族との時間を大切にする',
    diagnosticResult: '内向的で創造性豊かなタイプ'
  };

  test.beforeEach(async ({ page }) => {
    // テスト用APIモックの設定
    await page.route('/api/sessions/start', async (route) => {
      await route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          sessionId: testSessionId,
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

    await page.route(`/api/sessions/${testSessionId}/keyword`, async (route) => {
      await route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          sessionId: testSessionId,
          scene: {
            sceneIndex: 1,
            themeId: 'serene',
            narrative: 'あなたの心の中に、静かな湖があります。',
            choices: [
              {
                id: 'choice_1',
                text: sensitiveData.personalChoice,
                weights: { curiosity: 0.3, logic: 0.7 }
              },
              {
                id: 'choice_2', 
                text: '論理的に状況を分析する',
                weights: { curiosity: 0.1, logic: 0.9 }
              }
            ]
          }
        })
      });
    });

    await page.route(`/api/sessions/${testSessionId}/result`, async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          contentType: 'application/json',
          body: JSON.stringify({
            sessionId: testSessionId,
            result: {
              type: 'creative_introvert',
              title: '創造的内向者',
              description: sensitiveData.diagnosticResult,
              axes: [
                { name: 'curiosity', score: 0.7, displayName: '好奇心' },
                { name: 'logic', score: 0.6, displayName: '論理性' }
              ]
            }
          })
        });
      }
    });
  });

  test.describe('1. 30秒自動削除機能テスト', () => {
    test('セッション完了から30秒後の自動データ削除', async ({ page }) => {
      // セッション開始から完了まで実行
      await page.goto('/');
      await expect(page.locator('[data-testid="bootstrap-complete"]')).toBeVisible({ timeout: 10000 });
      
      // キーワード入力とセッション進行
      await page.fill('[data-testid="keyword-input"]', sensitiveData.keyword);
      await page.click('[data-testid="confirm-keyword"]');
      
      // 選択肢選択
      await expect(page.locator('[data-testid="choice-1"]')).toBeVisible({ timeout: 5000 });
      await page.click('[data-testid="choice-1"]');
      
      // 結果画面表示
      await expect(page.locator('[data-testid="result-screen"]')).toBeVisible({ timeout: 5000 });
      
      // セッション完了時刻を記録
      const completionTime = Date.now();
      
      // 結果表示中はデータが存在することを確認
      const resultTitle = await page.locator('[data-testid="result-title"]').textContent();
      expect(resultTitle).toContain('創造的内向者');
      
      // 30秒経過を待機
      await page.waitForTimeout(32000); // 余裕を持って32秒
      
      // ブラウザのローカルストレージ確認
      const localStorage = await page.evaluate(() => JSON.stringify(window.localStorage));
      const sessionStorage = await page.evaluate(() => JSON.stringify(window.sessionStorage));
      
      // 30秒後にセッションデータが削除されていることを確認
      expect(localStorage).not.toContain(testSessionId);
      expect(localStorage).not.toContain(sensitiveData.keyword);
      expect(localStorage).not.toContain(sensitiveData.personalChoice);
      expect(sessionStorage).not.toContain(testSessionId);
      
      // バックエンドAPIでセッション削除を確認
      const response = await page.request.get(`/api/sessions/${testSessionId}/scenes/1`);
      expect(response.status()).toBe(404); // セッションが削除されているため404
    });

    test('自動削除タイマーの正確性検証', async ({ page }) => {
      await page.goto('/');
      await page.fill('[data-testid="keyword-input"]', 'テスト');
      await page.click('[data-testid="confirm-keyword"]');
      await page.click('[data-testid="choice-1"]');
      
      // 結果表示完了
      await expect(page.locator('[data-testid="result-screen"]')).toBeVisible();
      const startTime = Date.now();
      
      // 29秒後：まだデータが存在することを確認
      await page.waitForTimeout(29000);
      const midCheck = await page.evaluate(() => window.localStorage.getItem('currentSession'));
      expect(midCheck).not.toBeNull();
      
      // 追加で3秒待機（合計32秒）
      await page.waitForTimeout(3000);
      
      // 32秒後：データが削除されていることを確認
      const finalCheck = await page.evaluate(() => window.localStorage.getItem('currentSession'));
      expect(finalCheck).toBeNull();
      
      const totalTime = Date.now() - startTime;
      expect(totalTime).toBeGreaterThan(29000); // 最低29秒は経過
      expect(totalTime).toBeLessThan(35000);    // 35秒以内で削除完了
    });
  });

  test.describe('2. ブラウザストレージ完全クリアテスト', () => {
    test('LocalStorage完全削除の確認', async ({ page }) => {
      // セッション実行
      await page.goto('/');
      await page.fill('[data-testid="keyword-input"]', sensitiveData.keyword);
      await page.click('[data-testid="confirm-keyword"]');
      await page.click('[data-testid="choice-1"]');
      
      // LocalStorageにデータが保存されることを確認
      const beforeStorage = await page.evaluate(() => Object.keys(window.localStorage));
      expect(beforeStorage.length).toBeGreaterThan(0);
      
      // セッション完了から30秒経過後
      await page.waitForTimeout(32000);
      
      // LocalStorageが完全にクリアされていることを確認
      const afterStorage = await page.evaluate(() => Object.keys(window.localStorage));
      const storageValues = await page.evaluate(() => 
        Object.values(window.localStorage).join('')
      );
      
      // NightLoom関連のデータが完全に削除されていることを確認
      expect(storageValues).not.toContain(sensitiveData.keyword);
      expect(storageValues).not.toContain(sensitiveData.personalChoice);
      expect(storageValues).not.toContain(testSessionId);
      
      // セッション関連のキーが削除されていることを確認
      expect(afterStorage).not.toContain('currentSession');
      expect(afterStorage).not.toContain('sessionData');
      expect(afterStorage).not.toContain('userChoices');
    });

    test('SessionStorage完全削除の確認', async ({ page }) => {
      await page.goto('/');
      await page.fill('[data-testid="keyword-input"]', sensitiveData.keyword);
      await page.click('[data-testid="confirm-keyword"]');
      
      // SessionStorageの内容確認
      const beforeSession = await page.evaluate(() => Object.keys(window.sessionStorage));
      
      // セッション完了
      await page.click('[data-testid="choice-1"]');
      await page.waitForTimeout(32000);
      
      // SessionStorageが完全にクリアされていることを確認
      const afterSession = await page.evaluate(() => Object.keys(window.sessionStorage));
      const sessionValues = await page.evaluate(() => 
        Object.values(window.sessionStorage).join('')
      );
      
      expect(sessionValues).not.toContain(sensitiveData.keyword);
      expect(sessionValues).not.toContain(testSessionId);
    });

    test('IndexedDB完全削除の確認', async ({ page }) => {
      await page.goto('/');
      await page.fill('[data-testid="keyword-input"]', sensitiveData.keyword);
      await page.click('[data-testid="confirm-keyword"]');
      await page.click('[data-testid="choice-1"]');
      
      // セッション完了から30秒経過後
      await page.waitForTimeout(32000);
      
      // IndexedDBからNightLoom関連データが削除されていることを確認
      const dbNames = await page.evaluate(async () => {
        if ('indexedDB' in window) {
          // IndexedDBの存在確認とデータベース一覧取得
          const databases = await indexedDB.databases?.() || [];
          return databases.map(db => db.name);
        }
        return [];
      });
      
      // NightLoom関連のデータベースが残っていないことを確認
      expect(dbNames).not.toContain('nightloom');
      expect(dbNames).not.toContain('session-data');
    });
  });

  test.describe('3. 履歴・キャッシュ漏洩防止テスト', () => {
    test('ブラウザ履歴からの機密情報漏洩防止', async ({ page }) => {
      await page.goto('/');
      await page.fill('[data-testid="keyword-input"]', sensitiveData.keyword);
      await page.click('[data-testid="confirm-keyword"]');
      await page.click('[data-testid="choice-1"]');
      
      // 結果画面のURLを確認
      const resultUrl = await page.url();
      
      // URLに機密情報が含まれていないことを確認
      expect(resultUrl).not.toContain(sensitiveData.keyword);
      expect(resultUrl).not.toContain(sensitiveData.personalChoice);
      expect(resultUrl).not.toContain(testSessionId);
      
      // セッション完了後30秒経過
      await page.waitForTimeout(32000);
      
      // ブラウザ履歴確認
      const historyLength = await page.evaluate(() => window.history.length);
      expect(historyLength).toBeDefined();
      
      // 戻るボタンで前のページに戻っても機密情報が表示されないことを確認
      await page.goBack();
      const pageContent = await page.content();
      expect(pageContent).not.toContain(sensitiveData.keyword);
    });

    test('HTTP Refererヘッダーからの情報漏洩防止', async ({ page }) => {
      // Refererポリシーの確認
      await page.goto('/');
      
      // メタタグでRefererポリシーが設定されていることを確認
      const refererPolicy = await page.locator('meta[name="referrer"]').getAttribute('content');
      expect(refererPolicy).toBe('no-referrer');
      
      // 外部リンクでのReferer漏洩確認
      await page.setContent(`
        <html>
          <head><meta name="referrer" content="no-referrer"></head>
          <body><a href="https://example.com" target="_blank" id="external-link">External</a></body>
        </html>
      `);
      
      // 外部リンククリック時のRefererヘッダー確認
      const [newPage] = await Promise.all([
        page.waitForEvent('popup'),
        page.click('#external-link')
      ]);
      
      // 新しいページでRefererが送信されていないことを確認
      const refererHeader = await newPage.evaluate(() => document.referrer);
      expect(refererHeader).toBe('');
    });

    test('ブラウザキャッシュからの機密情報除去', async ({ page }) => {
      await page.goto('/');
      await page.fill('[data-testid="keyword-input"]', sensitiveData.keyword);
      await page.click('[data-testid="confirm-keyword"]');
      
      // Cache-Controlヘッダーの確認
      const response = await page.request.get('/');
      const cacheControl = response.headers()['cache-control'];
      expect(cacheControl).toContain('no-cache');
      expect(cacheControl).toContain('no-store');
      
      // Pragma: no-cacheヘッダーの確認
      const pragma = response.headers()['pragma'];
      expect(pragma).toBe('no-cache');
      
      // セッション完了後のキャッシュクリア確認
      await page.click('[data-testid="choice-1"]');
      await page.waitForTimeout(32000);
      
      // ページを再読み込みして機密情報が残っていないことを確認
      await page.reload();
      const pageContent = await page.content();
      expect(pageContent).not.toContain(sensitiveData.keyword);
      expect(pageContent).not.toContain(sensitiveData.personalChoice);
    });
  });

  test.describe('4. データ完全削除の実動作確認テスト', () => {
    test('メモリ内データの完全削除確認', async ({ page }) => {
      await page.goto('/');
      await page.fill('[data-testid="keyword-input"]', sensitiveData.keyword);
      await page.click('[data-testid="confirm-keyword"]');
      await page.click('[data-testid="choice-1"]');
      
      // メモリ内に機密データが存在することを確認
      const beforeDeletion = await page.evaluate(() => {
        // DOM内のテキストコンテンツ確認
        return document.body.textContent || '';
      });
      expect(beforeDeletion).toContain('創造的内向者');
      
      // セッション完了から30秒経過
      await page.waitForTimeout(32000);
      
      // DOM から機密情報が完全に削除されていることを確認
      const afterDeletion = await page.evaluate(() => {
        return document.body.textContent || '';
      });
      expect(afterDeletion).not.toContain(sensitiveData.keyword);
      expect(afterDeletion).not.toContain(sensitiveData.personalChoice);
      expect(afterDeletion).not.toContain(sensitiveData.diagnosticResult);
      
      // JavaScript変数からも削除されていることを確認
      const jsVariables = await page.evaluate(() => {
        // グローバル変数の確認
        const globalVars = Object.keys(window).filter(key =>
          key.toLowerCase().includes('session') ||
          key.toLowerCase().includes('nightloom')
        );
        return globalVars.length;
      });
      expect(jsVariables).toBe(0);
    });

    test('ネットワークリクエストキャッシュからの削除確認', async ({ page }) => {
      // ネットワークリクエストの監視開始
      const requests: string[] = [];
      page.on('request', request => {
        requests.push(request.url());
      });
      
      await page.goto('/');
      await page.fill('[data-testid="keyword-input"]', sensitiveData.keyword);
      await page.click('[data-testid="confirm-keyword"]');
      await page.click('[data-testid="choice-1"]');
      
      // セッション完了から30秒経過
      await page.waitForTimeout(32000);
      
      // ブラウザのネットワークキャッシュ確認
      const cacheEntries = await page.evaluate(async () => {
        if ('caches' in window) {
          const cacheNames = await caches.keys();
          const allEntries: string[] = [];
          
          for (const cacheName of cacheNames) {
            const cache = await caches.open(cacheName);
            const requests = await cache.keys();
            allEntries.push(...requests.map(req => req.url));
          }
          
          return allEntries;
        }
        return [];
      });
      
      // キャッシュから機密情報を含むリクエストが削除されていることを確認
      const sensitiveRequests = cacheEntries.filter(url =>
        url.includes(testSessionId) ||
        url.includes(encodeURIComponent(sensitiveData.keyword))
      );
      expect(sensitiveRequests).toHaveLength(0);
    });

    test('ガベージコレクション後のメモリリーク確認', async ({ page }) => {
      await page.goto('/');
      
      // メモリ使用量の初期値取得
      const initialMemory = await page.evaluate(() => {
        if ('memory' in performance) {
          return (performance as any).memory.usedJSHeapSize;
        }
        return 0;
      });
      
      // セッション実行
      await page.fill('[data-testid="keyword-input"]', sensitiveData.keyword);
      await page.click('[data-testid="confirm-keyword"]');
      await page.click('[data-testid="choice-1"]');
      
      // セッション完了から30秒経過
      await page.waitForTimeout(32000);
      
      // ガベージコレクションを強制実行
      await page.evaluate(() => {
        if ('gc' in window) {
          (window as any).gc();
        }
      });
      
      // メモリ使用量の最終値取得
      const finalMemory = await page.evaluate(() => {
        if ('memory' in performance) {
          return (performance as any).memory.usedJSHeapSize;
        }
        return 0;
      });
      
      // メモリリークが発生していないことを確認（初期値との差が許容範囲内）
      const memoryDifference = finalMemory - initialMemory;
      expect(memoryDifference).toBeLessThan(1024 * 1024); // 1MB以下の差であること
    });
  });

  test.describe('5. セッション分離基本テスト', () => {
    test('複数タブ間でのデータ分離確認', async ({ context }) => {
      // 第1タブでセッション開始
      const page1 = await context.newPage();
      await page1.goto('/');
      await page1.fill('[data-testid="keyword-input"]', 'タブ1のキーワード');
      await page1.click('[data-testid="confirm-keyword"]');
      
      // 第2タブでセッション開始
      const page2 = await context.newPage();
      await page2.goto('/');
      await page2.fill('[data-testid="keyword-input"]', 'タブ2のキーワード');
      await page2.click('[data-testid="confirm-keyword"]');
      
      // 各タブのセッションIDが異なることを確認
      const sessionId1 = await page1.evaluate(() =>
        localStorage.getItem('currentSession')
      );
      const sessionId2 = await page2.evaluate(() =>
        localStorage.getItem('currentSession')
      );
      
      expect(sessionId1).not.toBe(sessionId2);
      expect(sessionId1).not.toBeNull();
      expect(sessionId2).not.toBeNull();
      
      // タブ1のデータがタブ2に影響しないことを確認
      const tab1Content = await page1.content();
      const tab2Content = await page2.content();
      
      expect(tab1Content).toContain('タブ1のキーワード');
      expect(tab1Content).not.toContain('タブ2のキーワード');
      expect(tab2Content).toContain('タブ2のキーワード');
      expect(tab2Content).not.toContain('タブ1のキーワード');
      
      // セッション完了後の独立削除確認
      await page1.click('[data-testid="choice-1"]');
      await page1.waitForTimeout(32000);
      
      // タブ1のデータは削除されているが、タブ2のデータは残っていることを確認
      const tab1AfterDeletion = await page1.evaluate(() =>
        localStorage.getItem('currentSession')
      );
      const tab2AfterDeletion = await page2.evaluate(() =>
        localStorage.getItem('currentSession')
      );
      
      expect(tab1AfterDeletion).toBeNull();
      expect(tab2AfterDeletion).not.toBeNull();
    });

    test('同時進行セッション間の干渉防止', async ({ context }) => {
      const page1 = await context.newPage();
      const page2 = await context.newPage();
      
      // 両タブで同時にセッション開始
      await Promise.all([
        page1.goto('/'),
        page2.goto('/')
      ]);
      
      // 両タブで同時にキーワード入力
      await Promise.all([
        page1.fill('[data-testid="keyword-input"]', '同時セッション1'),
        page2.fill('[data-testid="keyword-input"]', '同時セッション2')
      ]);
      
      await Promise.all([
        page1.click('[data-testid="confirm-keyword"]'),
        page2.click('[data-testid="confirm-keyword"]')
      ]);
      
      // 両タブで同時に選択肢クリック
      await Promise.all([
        page1.click('[data-testid="choice-1"]'),
        page2.click('[data-testid="choice-1"]')
      ]);
      
      // 結果が正しく分離されていることを確認
      const result1 = await page1.locator('[data-testid="result-title"]').textContent();
      const result2 = await page2.locator('[data-testid="result-title"]').textContent();
      
      expect(result1).toBeDefined();
      expect(result2).toBeDefined();
      
      // 同じ結果タイプでも、セッションが独立していることを確認
      const sessionId1 = await page1.evaluate(() =>
        document.querySelector('[data-session-id]')?.getAttribute('data-session-id')
      );
      const sessionId2 = await page2.evaluate(() =>
        document.querySelector('[data-session-id]')?.getAttribute('data-session-id')
      );
      
      expect(sessionId1).not.toBe(sessionId2);
    });
  });

  test.describe('6. API仕様不整合修正テスト', () => {
    test('結果取得エンドポイントのPOST対応確認', async ({ page }) => {
      await page.goto('/');
      await page.fill('[data-testid="keyword-input"]', sensitiveData.keyword);
      await page.click('[data-testid="confirm-keyword"]');
      await page.click('[data-testid="choice-1"]');
      
      // 結果取得にPOSTメソッドが使用されていることを確認
      const requests: any[] = [];
      page.on('request', request => {
        if (request.url().includes('/result')) {
          requests.push({
            method: request.method(),
            url: request.url()
          });
        }
      });
      
      // 結果画面の表示を待機
      await expect(page.locator('[data-testid="result-screen"]')).toBeVisible();
      
      // 結果取得リクエストがPOSTメソッドで実行されていることを確認
      const resultRequests = requests.filter(req => req.url.includes('/result'));
      expect(resultRequests.length).toBeGreaterThan(0);
      expect(resultRequests[0].method).toBe('POST');
    });

    test('GETメソッドでの結果取得アクセス拒否確認', async ({ page }) => {
      // 直接GETメソッドで結果エンドポイントにアクセス
      const response = await page.request.get(`/api/sessions/${testSessionId}/result`);
      
      // 405 Method Not Allowedが返されることを確認
      expect(response.status()).toBe(405);
      
      const responseBody = await response.json();
      expect(responseBody.error_code).toBe('METHOD_NOT_ALLOWED');
    });

    test('不正なHTTPメソッドでのアクセス拒否', async ({ page }) => {
      const invalidMethods = ['PUT', 'DELETE', 'PATCH'];
      
      for (const method of invalidMethods) {
        const response = await page.request.fetch(`/api/sessions/${testSessionId}/result`, {
          method: method
        });
        
        // 405 Method Not Allowedが返されることを確認
        expect(response.status()).toBe(405);
      }
    });

    test('APIレスポンス一貫性の確認', async ({ page }) => {
      await page.goto('/');
      await page.fill('[data-testid="keyword-input"]', sensitiveData.keyword);
      await page.click('[data-testid="confirm-keyword"]');
      
      // シーン取得のレスポンス形式確認
      const sceneResponse = await page.request.get(`/api/sessions/${testSessionId}/scenes/1`);
      const sceneData = await sceneResponse.json();
      
      expect(sceneData).toHaveProperty('sessionId');
      expect(sceneData).toHaveProperty('scene');
      expect(sceneData.scene).toHaveProperty('sceneIndex');
      expect(sceneData.scene).toHaveProperty('choices');
      
      await page.click('[data-testid="choice-1"]');
      
      // 結果取得のレスポンス形式確認
      const resultResponse = await page.request.post(`/api/sessions/${testSessionId}/result`);
      const resultData = await resultResponse.json();
      
      expect(resultData).toHaveProperty('sessionId');
      expect(resultData).toHaveProperty('result');
      expect(resultData.result).toHaveProperty('type');
      expect(resultData.result).toHaveProperty('title');
      expect(resultData.result).toHaveProperty('axes');
      
      // セッションIDの一貫性確認
      expect(sceneData.sessionId).toBe(resultData.sessionId);
    });
  });
});
