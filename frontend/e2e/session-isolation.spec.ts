
import { test, expect } from '@playwright/test';

/**
 * NightLoom セッション分離・API整合性強化E2Eテストスイート
 * Week3: 高度なセッション分離とAPI整合性検証
 * 
 * 対象要件:
 * - マルチタブ環境での完全なデータ分離
 * - 同時進行セッション間の相互干渉防止
 * - メモリ空間の分離保証
 * - API仕様の統一性確保
 * - セッション状態の整合性維持
 * - エラー境界での安全な分離
 */

test.describe('セッション分離・API整合性強化E2Eテスト', () => {
  const testData = {
    session1: {
      keyword: '冒険と探求',
      choice: '未知の領域を探索する',
      result: 'explorer_type'
    },
    session2: {
      keyword: '平和と調和',
      choice: '安全な環境を維持する',
      result: 'harmonizer_type'
    },
    session3: {
      keyword: '創造と革新',
      choice: '新しいアイデアを生み出す',
      result: 'innovator_type'
    }
  };

  test.beforeEach(async ({ page }) => {
    // 動的なセッションIDに対応するAPIモック
    await page.route('/api/sessions/start', async (route) => {
      const sessionId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      
      await route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          sessionId: sessionId,
          axes: [
            { name: 'curiosity', displayName: '好奇心', weight: 0.0 },
            { name: 'logic', displayName: '論理性', weight: 0.0 },
            { name: 'creativity', displayName: '創造性', weight: 0.0 }
          ],
          keywordCandidates: ['冒険', '平和', '創造'],
          initialCharacter: 'あ',
          themeId: 'serene'
        })
      });
    });

    // キーワードエンドポイントモック
    await page.route('**/keyword', async (route) => {
      const sessionId = route.request().url().match(/sessions\/([^\/]+)\/keyword/)?.[1];
      const requestData = await route.request().postDataJSON();
      
      let responseData = {
        sessionId: sessionId,
        scene: {
          sceneIndex: 1,
          themeId: 'serene',
          narrative: '静かな物語が始まります。',
          choices: [
            {
              id: 'choice_1',
              text: '感情を重視する選択',
              weights: { curiosity: 0.3, logic: 0.2, creativity: 0.5 }
            },
            {
              id: 'choice_2',
              text: '論理を重視する選択',
              weights: { curiosity: 0.2, logic: 0.7, creativity: 0.1 }
            }
          ]
        }
      };

      // キーワードに基づいて異なるレスポンスを返す
      if (requestData.keyword?.includes('冒険')) {
        responseData.scene.choices[0].text = testData.session1.choice;
      } else if (requestData.keyword?.includes('平和')) {
        responseData.scene.choices[0].text = testData.session2.choice;
      } else if (requestData.keyword?.includes('創造')) {
        responseData.scene.choices[0].text = testData.session3.choice;
      }

      await route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify(responseData)
      });
    });

    // 結果エンドポイントモック
    await page.route('**/result', async (route) => {
      const sessionId = route.request().url().match(/sessions\/([^\/]+)\/result/)?.[1];
      
      await route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          sessionId: sessionId,
          result: {
            type: 'dynamic_type',
            title: `セッション${sessionId?.substr(-4) || 'Unknown'}の結果`,
            description: 'あなたは独特な個性を持つタイプです。',
            axes: [
              { name: 'curiosity', score: Math.random(), displayName: '好奇心' },
              { name: 'logic', score: Math.random(), displayName: '論理性' },
              { name: 'creativity', score: Math.random(), displayName: '創造性' }
            ]
          }
        })
      });
    });
  });

  test.describe('1. マルチタブ完全分離テスト', () => {
    test('5タブ同時実行での相互独立性確認', async ({ context }) => {
      // 5つの独立したタブを作成
      const pages = await Promise.all([
        context.newPage(),
        context.newPage(),
        context.newPage(),
        context.newPage(),
        context.newPage()
      ]);

      const keywords = [
        '冒険と探求の旅',
        '平和な日常生活',
        '創造的な表現',
        '論理的な思考',
        '感情豊かな体験'
      ];

      // 各タブで並行してセッション開始
      await Promise.all(pages.map(async (page, index) => {
        await page.goto('/');
        await expect(page.locator('[data-testid="bootstrap-complete"]')).toBeVisible({ timeout: 15000 });
        await page.fill('[data-testid="keyword-input"]', keywords[index]);
        await page.click('[data-testid="confirm-keyword"]');
      }));

      // 各タブのセッションIDが異なることを確認
      const sessionIds = await Promise.all(pages.map(async (page) => {
        return await page.evaluate(() => localStorage.getItem('currentSession'));
      }));

      // 全てのセッションIDが一意であることを確認
      const uniqueSessionIds = new Set(sessionIds);
      expect(uniqueSessionIds.size).toBe(5);
      sessionIds.forEach(id => expect(id).not.toBeNull());

      // 全タブクローズ
      await Promise.all(pages.map(page => page.close()));
    });

    test('タブ間メモリ空間の完全分離確認', async ({ context }) => {
      const page1 = await context.newPage();
      const page2 = await context.newPage();

      // タブ1でセッション実行
      await page1.goto('/');
      await page1.fill('[data-testid="keyword-input"]', testData.session1.keyword);
      await page1.click('[data-testid="confirm-keyword"]');
      
      // タブ1のグローバル変数設定
      await page1.evaluate(() => {
        (window as any).testVariable = 'tab1-data';
        (window as any).sessionContext = { tab: 'tab1', data: 'sensitive' };
      });

      // タブ2でセッション実行
      await page2.goto('/');
      await page2.fill('[data-testid="keyword-input"]', testData.session2.keyword);
      await page2.click('[data-testid="confirm-keyword"]');

      // タブ2でタブ1の変数にアクセスできないことを確認
      const tab2Variables = await page2.evaluate(() => {
        return {
          testVariable: (window as any).testVariable,
          sessionContext: (window as any).sessionContext
        };
      });

      expect(tab2Variables.testVariable).toBeUndefined();
      expect(tab2Variables.sessionContext).toBeUndefined();

      // タブ2独自の変数設定
      await page2.evaluate(() => {
        (window as any).testVariable = 'tab2-data';
      });

      // タブ1の変数が変更されていないことを確認
      const tab1Variables = await page1.evaluate(() => {
        return {
          testVariable: (window as any).testVariable,
          sessionContext: (window as any).sessionContext
        };
      });

      expect(tab1Variables.testVariable).toBe('tab1-data');
      expect(tab1Variables.sessionContext).toEqual({ tab: 'tab1',  'sensitive' });
    });
  });

  test.describe('2. 同時進行セッション干渉防止テスト', () => {
    test('競合状態での制御確認', async ({ context }) => {
      const page1 = await context.newPage();
      const page2 = await context.newPage();
      const page3 = await context.newPage();

      // 同時にセッション開始
      await Promise.all([
        page1.goto('/'),
        page2.goto('/'),
        page3.goto('/')
      ]);

      // 同時にキーワード入力（競合状態を作り出す）
      await Promise.all([
        page1.fill('[data-testid="keyword-input"]', testData.session1.keyword),
        page2.fill('[data-testid="keyword-input"]', testData.session2.keyword),
        page3.fill('[data-testid="keyword-input"]', testData.session3.keyword)
      ]);

      // 同時確認ボタンクリック
      await Promise.all([
        page1.click('[data-testid="confirm-keyword"]'),
        page2.click('[data-testid="confirm-keyword"]'),
        page3.click('[data-testid="confirm-keyword"]')
      ]);

      // 全ページで選択肢が正常に表示されることを確認
      await Promise.all([
        expect(page1.locator('[data-testid="choice-1"]')).toBeVisible({ timeout: 10000 }),
        expect(page2.locator('[data-testid="choice-1"]')).toBeVisible({ timeout: 10000 }),
        expect(page3.locator('[data-testid="choice-1"]')).toBeVisible({ timeout: 10000 })
      ]);

      // 各セッションの結果が独立していることを確認
      const sessionIds = await Promise.all([
        page1.evaluate(() => localStorage.getItem('currentSession')),
        page2.evaluate(() => localStorage.getItem('currentSession')),
        page3.evaluate(() => localStorage.getItem('currentSession'))
      ]);

      // 全セッションIDが異なることを確認
      expect(new Set(sessionIds).size).toBe(3);
      sessionIds.forEach(id => expect(id).not.toBeNull());
    });

    test('API呼び出しタイミング競合の処理確認', async ({ context }) => {
      const page1 = await context.newPage();
      const page2 = await context.newPage();

      // 両ページで同時にセッション開始
      await Promise.all([
        page1.goto('/'),
        page2.goto('/')
      ]);

      // 同じタイミングでキーワード送信
      await Promise.all([
        page1.fill('[data-testid="keyword-input"]', 'タイミング1'),
        page2.fill('[data-testid="keyword-input"]', 'タイミング2')
      ]);

      // 同時確認（APIコールタイミング競合）
      await Promise.all([
        page1.click('[data-testid="confirm-keyword"]'),
        page2.click('[data-testid="confirm-keyword"]')
      ]);

      // 両方のページで正常に次のステップに進むことを確認
      await Promise.all([
        expect(page1.locator('[data-testid="choice-1"]')).toBeVisible({ timeout: 10000 }),
        expect(page2.locator('[data-testid="choice-1"]')).toBeVisible({ timeout: 10000 })
      ]);

      // 異なる内容が表示されていることを確認
      const content1 = await page1.content();
      const content2 = await page2.content();
      
      expect(content1).not.toBe(content2);
    });
  });

  test.describe('3. メモリ干渉防止テスト', () => {
    test('JavaScript実行コンテキストの分離確認', async ({ context }) => {
      const page1 = await context.newPage();
      const page2 = await context.newPage();

      // タブ1でカスタム関数定義
      await page1.goto('/');
      await page1.evaluate(() => {
        (window as any).customFunction = () => 'tab1-function';
        (window as any).sharedData = { tab: 1, sensitive: 'secret1' };
      });

      // タブ2でアクセス試行
      await page2.goto('/');
      const accessResult = await page2.evaluate(() => {
        try {
          return {
            hasCustomFunction: typeof (window as any).customFunction === 'function',
            sharedData: (window as any).sharedData,
            canExecute: (window as any).customFunction ? (window as any).customFunction() : null
          };
        } catch (error) {
          return { error: (error as Error).message };
        }
      });

      // タブ2からタブ1の関数にアクセスできないことを確認
      expect(accessResult.hasCustomFunction).toBe(false);
      expect(accessResult.sharedData).toBeUndefined();
      expect(accessResult.canExecute).toBeNull();
    });

    test('DOMイベントリスナー干渉防止', async ({ context }) => {
      const page1 = await context.newPage();
      const page2 = await context.newPage();

      await page1.goto('/');
      await page2.goto('/');

      // タブ1でグローバルイベントリスナー設定
      await page1.evaluate(() => {
        (window as any).tab1EventTriggered = false;
        document.addEventListener('click', () => {
          (window as any).tab1EventTriggered = true;
        });
      });

      // タブ2でクリックイベント発生
      await page2.click('body');

      // タブ1のイベントリスナーが反応しないことを確認
      const tab1EventState = await page1.evaluate(() => (window as any).tab1EventTriggered);
      expect(tab1EventState).toBe(false);

      // タブ1でクリックして自身のイベントが動作することを確認
      await page1.click('body');
      const tab1EventAfterClick = await page1.evaluate(() => (window as any).tab1EventTriggered);
      expect(tab1EventAfterClick).toBe(true);
    });
  });

  test.describe('4. API整合性検証テスト', () => {
    test('RESTful API規約の統一性確認', async ({ page }) => {
      // セッション開始APIの確認
      const startResponse = await page.request.post('/api/sessions/start');
      expect(startResponse.status()).toBe(200);
      
      const startData = await startResponse.json();
      expect(startData).toHaveProperty('sessionId');
      expect(startData.sessionId).toMatch(/^[0-9a-f-]{36}$/); // UUID形式

      const sessionId = startData.sessionId;

      // キーワードAPI（POST）の確認
      const keywordResponse = await page.request.post(`/api/sessions/${sessionId}/keyword`, {
        data: { keyword: 'テスト', source: 'manual' }
      });
      expect(keywordResponse.status()).toBe(200);

      const keywordData = await keywordResponse.json();
      expect(keywordData).toHaveProperty('sessionId', sessionId);
      expect(keywordData).toHaveProperty('scene');
      expect(keywordData.scene).toHaveProperty('choices');
      expect(Array.isArray(keywordData.scene.choices)).toBe(true);

      // 結果API（POST）の確認  
      const resultResponse = await page.request.post(`/api/sessions/${sessionId}/result`);
      expect(resultResponse.status()).toBe(200);

      const resultData = await resultResponse.json();
      expect(resultData).toHaveProperty('sessionId', sessionId);
      expect(resultData).toHaveProperty('result');
      expect(resultData.result).toHaveProperty('type');
      expect(resultData.result).toHaveProperty('axes');
    });

    test('エラーレスポンス形式の統一確認', async ({ page }) => {
      // 不正なセッションIDでのアクセス
      const invalidSessionId = 'invalid-session-id';
      
      const errorResponses = await Promise.all([
        page.request.get(`/api/sessions/${invalidSessionId}/scenes/1`),
        page.request.post(`/api/sessions/${invalidSessionId}/keyword`, { data: {} }),
        page.request.post(`/api/sessions/${invalidSessionId}/result`)
      ]);

      // 全てのエラーレスポンスが統一された形式であることを確認
      for (const response of errorResponses) {
        expect(response.status()).toBeGreaterThanOrEqual(400);
        
        const errorData = await response.json();
        expect(errorData).toHaveProperty('error_code');
        expect(errorData).toHaveProperty('message');
        expect(typeof errorData.error_code).toBe('string');
        expect(typeof errorData.message).toBe('string');
      }
    });
  });

  test.describe('5. エラー境界での分離テスト', () => {
    test('JavaScript例外発生時の他セッションへの影響確認', async ({ context }) => {
      const page1 = await context.newPage();
      const page2 = await context.newPage();

      // 両ページでセッション開始
      await Promise.all([
        page1.goto('/'),
        page2.goto('/')
      ]);

      await Promise.all([
        page1.fill('[data-testid="keyword-input"]', 'エラーテスト1'),
        page2.fill('[data-testid="keyword-input"]', 'エラーテスト2')
      ]);

      // タブ1で意図的にJavaScriptエラーを発生
      await page1.evaluate(() => {
        throw new Error('Intentional error in tab1');
      }).catch(() => {
        // エラーは期待されている
      });

      // タブ2が正常に動作することを確認
      await page2.click('[data-testid="confirm-keyword"]');
      await expect(page2.locator('[data-testid="choice-1"]')).toBeVisible({ timeout: 10000 });

      // タブ2のセッションが正常に進行できることを確認
      await page2.click('[data-testid="choice-1"]');
      await expect(page2.locator('[data-testid="result-screen"]')).toBeVisible({ timeout: 10000 });
    });

    test('ネットワークエラー発生時の分離確認', async ({ context }) => {
      const page1 = await context.newPage();
      const page2 = await context.newPage();

      // タブ1でネットワークエラーをシミュレート
      await page1.route('**/keyword', async (route) => {
        await route.abort('failed');
      });

      await page1.goto('/');
      await page2.goto('/');

      // タブ1でエラーが発生
      await page1.fill('[data-testid="keyword-input"]', 'ネットワークエラー');
      await page1.click('[data-testid="confirm-keyword"]');

      // タブ2は正常に動作
      await page2.fill('[data-testid="keyword-input"]', '正常なセッション');
      await page2.click('[data-testid="confirm-keyword"]');
      
      // タブ2で選択肢が正常に表示されることを確認
      await expect(page2.locator('[data-testid="choice-1"]')).toBeVisible({ timeout: 10000 });
    });
  });
});
