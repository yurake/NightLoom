import * as fs from 'fs';
import * as path from 'path';

// 実装されたユーティリティ関数をインポート
import checklistVerification from '../../scripts/utils/checklist-verification';

describe('チェックリスト検証ユーティリティ', () => {
  const mockChecklistContent = `
# NightLoom結果画面表示機能 実装進捗チェックリスト

## 🏗️ Phase 1: コンポーネント基盤とコア型定義（30分）

### 1.1 環境準備
- [ ] ブランチ作成・切り替え (\`git checkout -b 002-nightloom-kekka-gamen-hyoji\`)
- [x] 依存関係確認 (\`cd frontend && pnpm install\`)

## 🔌 Phase 2: API統合とResultScreenコンポーネント実装（20分）

### 2.1 APIクライアント実装
- [ ] [\`frontend/app/services/session-api.ts\`](frontend/app/services/session-api.ts) 作成
`;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('parseChecklistFromMarkdown', () => {
    it('Markdownからチェックリストデータを正しく解析する', () => {
      const result = checklistVerification.parseChecklistFromMarkdown(mockChecklistContent);
      
      expect(result.sections).toHaveLength(2);
      expect(result.totalItems).toBeGreaterThan(0);
      expect(result.completedItems).toBeLessThanOrEqual(result.totalItems);
      expect(result.progressPercentage).toBeGreaterThanOrEqual(0);
      expect(result.progressPercentage).toBeLessThanOrEqual(100);
    });

    it('チェックボックスの状態を正しく判定する', () => {
      const contentWithMixedStates = `
- [ ] 未完了タスク1
- [x] 完了タスク1
- [ ] 未完了タスク2
`;

      const result = checklistVerification.parseChecklistFromMarkdown(contentWithMixedStates);
      const items = result.sections[0]?.items || [];
      const completedItems = items.filter(item => item.completed);
      expect(completedItems).toHaveLength(1);
    });

    it('ファイルパスリンクを正しく抽出する', () => {
      const contentWithFileLinks = `
- [ ] [\`frontend/app/types/result.ts\`](frontend/app/types/result.ts) 作成
- [ ] [\`frontend/tests/components/result/ResultScreen.test.tsx\`](frontend/tests/components/result/ResultScreen.test.tsx) 作成
`;

      const result = checklistVerification.parseChecklistFromMarkdown(contentWithFileLinks);
      const items = result.sections[0]?.items || [];
      expect(items[0]?.filePath).toBe('frontend/app/types/result.ts');
      expect(items[1]?.filePath).toBe('frontend/tests/components/result/ResultScreen.test.tsx');
    });
  });

  describe('verifyImplementationStatus', () => {
    it('存在するファイルのコンポーネントを実装済みと判定する', async () => {
      const mockItem = {
        id: 'result-screen-component',
        task: 'ResultScreen.tsx 作成',
        completed: false,
        filePath: 'frontend/app/(play)/components/ResultScreen.tsx'
      };

      const status = await checklistVerification.verifyImplementationStatus(mockItem);
      expect(status).toBe('implemented');
    });

    it('存在しないファイルを未実装と判定する', async () => {
      const mockItem = {
        id: 'non-existent-file',
        task: '存在しないファイル作成',
        completed: false,
        filePath: 'frontend/app/non-existent-file.tsx'
      };

      const status = await checklistVerification.verifyImplementationStatus(mockItem);
      expect(status).toBe('not-implemented');
    });
  });

  describe('updateChecklistItem', () => {
    it('項目を完了状態に更新する', () => {
      const mockItem = {
        id: 'update-test-1',
        task: 'テスト項目1',
        completed: false
      };

      const updatedItem = checklistVerification.updateChecklistItem(mockItem, true);
      expect(updatedItem.completed).toBe(true);
      expect(updatedItem.id).toBe(mockItem.id);
      expect(updatedItem.task).toBe(mockItem.task);
    });
  });

  describe('analyzeFileImplementation', () => {
    it('TypeScriptファイルの実装品質を分析する', async () => {
      const filePath = 'frontend/app/(play)/components/ResultScreen.tsx';
      const analysis = await checklistVerification.analyzeFileImplementation(filePath);
      
      expect(analysis).toHaveProperty('exists');
      expect(analysis).toHaveProperty('hasTests');
      expect(analysis).toHaveProperty('hasTypes');
      expect(analysis).toHaveProperty('hasImplementation');
      expect(analysis).toHaveProperty('codeQuality');
      expect(['good', 'partial', 'poor']).toContain(analysis.codeQuality);
    });

    it('存在しないファイルの分析結果を返す', async () => {
      const filePath = 'frontend/app/non-existent-file.tsx';
      const analysis = await checklistVerification.analyzeFileImplementation(filePath);
      
      expect(analysis.exists).toBe(false);
      expect(analysis.hasTests).toBe(false);
      expect(analysis.hasTypes).toBe(false);
      expect(analysis.hasImplementation).toBe(false);
      expect(analysis.codeQuality).toBe('poor');
    });
  });

  describe('calculateProgressMetrics', () => {
    it('全体の進捗率を正しく計算する', () => {
      const mockSections = [
        {
          title: 'Phase 1',
          phase: 'Phase 1',
          estimatedTime: '30分',
          items: [
            { id: '1', task: 'タスク1', completed: true },
            { id: '2', task: 'タスク2', completed: false },
            { id: '3', task: 'タスク3', completed: true }
          ]
        }
      ];

      const metrics = checklistVerification.calculateProgressMetrics(mockSections);
      expect(metrics.totalItems).toBe(3);
      expect(metrics.completedItems).toBe(2);
      expect(metrics.progressPercentage).toBe(67);
      expect(metrics.phaseProgress).toHaveLength(1);
    });
  });

  describe('updateChecklistMarkdown', () => {
    it('Markdownファイルの完了状態を正しく更新する', () => {
      const originalMarkdown = `
## Phase 1
- [ ] タスク1
- [x] タスク2
- [ ] タスク3
`;

      const updates = [
        { id: 'item-1', completed: true },
        { id: 'item-3', completed: true }
      ];

      const updatedMarkdown = checklistVerification.updateChecklistMarkdown(originalMarkdown, updates);
      expect(updatedMarkdown).toContain('- [x] タスク1');
      expect(updatedMarkdown).toContain('- [x] タスク2');
      expect(updatedMarkdown).toContain('- [x] タスク3');
    });
  });

  describe('統合テスト', () => {
    it('実際のspec 002チェックリストファイルを読み込み解析する', async () => {
      const checklistPath = 'specs/002-nightloom-kekka-gamen-hyoji/checklists/implementation-progress.md';

      if (fs.existsSync(checklistPath)) {
        const content = fs.readFileSync(checklistPath, 'utf-8');
        const parsed = checklistVerification.parseChecklistFromMarkdown(content);
        
        expect(parsed.sections.length).toBeGreaterThan(0);
        expect(parsed.totalItems).toBeGreaterThan(0);
        
        const phase1Section = parsed.sections.find(s => s.title.includes('Phase 1'));
        expect(phase1Section).toBeDefined();
        expect(phase1Section?.items.length).toBeGreaterThan(0);
      }
    });
  });
});
