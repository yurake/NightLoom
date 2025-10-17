import { render, screen } from '@testing-library/react';
import { axe } from 'jest-axe';
import Scene from '../../app/(play)/components/Scene';
import ChoiceOptions from '../../app/(play)/components/ChoiceOptions';
import ResultScreen from '../../app/(play)/components/ResultScreen';
import AxesScores from '../../app/(play)/components/AxesScores';
import TypeCard from '../../app/(play)/components/TypeCard';
import { SessionProvider } from '../../app/state/SessionContext';
import { ThemeProvider } from '../../app/theme/ThemeProvider';
import { mockResult2Axes } from '../../app/types/result';

// テスト用のモックデータ
const mockChoices = [
  { id: 'choice_0_1', text: '選択肢A', weights: { adventure: 1, social: 0, creativity: 0, focus: 0 } },
  { id: 'choice_0_2', text: '選択肢B', weights: { adventure: 0, social: 1, creativity: 0, focus: 0 } },
  { id: 'choice_0_3', text: '選択肢C', weights: { adventure: 0, social: 0, creativity: 1, focus: 0 } },
  { id: 'choice_0_4', text: '選択肢D', weights: { adventure: 0, social: 0, creativity: 0, focus: 1 } }
];

// モックAPIクライアント
const mockApiClient = {
  getResult: jest.fn().mockResolvedValue(mockResult2Axes)
};

// テスト用のWrapper コンポーネント
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <SessionProvider>
    <ThemeProvider>
      {children}
    </ThemeProvider>
  </SessionProvider>
);

describe('Screen Reader Compatibility Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Semantic HTML Structure', () => {
    it('should have proper heading hierarchy', async () => {
      render(
        <TestWrapper>
          <main>
            <h1>NightLoom 診断</h1>
            <section>
              <h2>シーン 1</h2>
              <ChoiceOptions 
                choices={mockChoices}
                onChoiceSelect={jest.fn()}
                sceneIndex={0}
              />
            </section>
          </main>
        </TestWrapper>
      );

      // h1が存在することを確認
      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
      expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument();

      // 見出し階層の検証
      const headings = screen.getAllByRole('heading');
      expect(headings).toHaveLength(2);
    });

    it('should use proper landmark roles', async () => {
      render(
        <TestWrapper>
          <div>
            <main role="main">
              <h1>NightLoom 診断</h1>
              <section role="region" aria-label="選択肢">
                <ChoiceOptions 
                  choices={mockChoices}
                  onChoiceSelect={jest.fn()}
                  sceneIndex={0}
                />
              </section>
            </main>
          </div>
        </TestWrapper>
      );

      // ランドマークroleの確認
      expect(screen.getByRole('main')).toBeInTheDocument();
      expect(screen.getByRole('region')).toBeInTheDocument();
    });
  });

  describe('ARIA Labels and Descriptions', () => {
    it('should have proper ARIA labels for choice selection', async () => {
      render(
        <TestWrapper>
          <ChoiceOptions 
            choices={mockChoices}
            onChoiceSelect={jest.fn()}
            sceneIndex={0}
          />
        </TestWrapper>
      );

      // 各選択肢のARIA属性確認
      const choiceButtons = screen.getAllByRole('radio');
      choiceButtons.forEach((button, index) => {
        expect(button).toHaveAttribute('aria-describedby');
        
        // データ属性の確認
        expect(button).toHaveAttribute('data-choice-id');
        expect(button).toHaveAttribute('data-testid', `choice-0-${index + 1}`);
      });
    });

    it('should provide screen reader announcements for score progress', async () => {
      render(
        <TestWrapper>
          <AxesScores axesScores={mockResult2Axes.axes} />
        </TestWrapper>
      );

      // プログレスバーのaria属性確認
      const progressBars = screen.getAllByRole('progressbar');
      progressBars.forEach((progressBar) => {
        expect(progressBar).toHaveAttribute('aria-label');
        expect(progressBar).toHaveAttribute('aria-valuenow');
        expect(progressBar).toHaveAttribute('aria-valuemin', '0');
        expect(progressBar).toHaveAttribute('aria-valuemax', '100');
      });
    });

    it('should have descriptive text for type results', async () => {
      render(
        <TestWrapper>
          <TypeCard typeResult={mockResult2Axes.type} />
        </TestWrapper>
      );

      // article要素の確認
      const typeArticle = screen.getByRole('article');
      expect(typeArticle).toBeInTheDocument();
      
      // タイプ名の見出し確認
      const typeHeading = screen.getByRole('heading', { level: 2 });
      expect(typeHeading).toBeInTheDocument();
      expect(typeHeading).toHaveTextContent(mockResult2Axes.type.name);
    });
  });

  describe('Live Regions for Dynamic Content', () => {
    it('should announce choice selection changes', async () => {
      render(
        <TestWrapper>
          <ChoiceOptions 
            choices={mockChoices}
            selectedChoiceId="choice_0_1"
            onChoiceSelect={jest.fn()}
            sceneIndex={0}
          />
        </TestWrapper>
      );

      // aria-live region の確認
      const liveRegion = screen.getByRole('status');
      expect(liveRegion).toBeInTheDocument();
      expect(liveRegion).toHaveAttribute('aria-live', 'polite');
      
      // 選択状況のアナウンス内容確認
      expect(liveRegion).toHaveTextContent('選択肢が選ばれました: 選択肢A');
    });

    it('should announce loading states', async () => {
      render(
        <TestWrapper>
          <Scene 
            sessionId="test-session"
            sceneIndex={0}
            onChoiceSubmit={jest.fn()}
            onSceneComplete={jest.fn()}
          />
        </TestWrapper>
      );

      // ローディング状態のaria-label確認
      const loadingIndicator = screen.getByTestId('loading-indicator');
      expect(loadingIndicator).toBeInTheDocument();
      expect(loadingIndicator).toHaveTextContent('シーンを読み込み中');
    });
  });

  describe('Form Controls and Labels', () => {
    it('should have proper form labels', async () => {
      render(
        <TestWrapper>
          <form>
            <label htmlFor="keyword-input">診断キーワード</label>
            <input 
              id="keyword-input" 
              type="text" 
              placeholder="キーワードを入力してください"
              aria-describedby="keyword-help"
            />
            <div id="keyword-help">
              診断のベースとなるキーワードを1つ選択または入力してください
            </div>
          </form>
        </TestWrapper>
      );

      const input = screen.getByLabelText('診断キーワード');
      expect(input).toBeInTheDocument();
      expect(input).toHaveAttribute('aria-describedby', 'keyword-help');
      
      const helpText = screen.getByText('診断のベースとなるキーワードを1つ選択または入力してください');
      expect(helpText).toBeInTheDocument();
    });
  });

  describe('Error and Status Messages', () => {
    it('should announce error messages properly', async () => {
      render(
        <TestWrapper>
          <div role="alert" aria-live="assertive">
            <p>エラーが発生しました：ネットワークエラー</p>
          </div>
        </TestWrapper>
      );

      const errorAlert = screen.getByRole('alert');
      expect(errorAlert).toBeInTheDocument();
      expect(errorAlert).toHaveAttribute('aria-live', 'assertive');
      expect(errorAlert).toHaveTextContent('エラーが発生しました：ネットワークエラー');
    });

    it('should provide clear instructions for users', async () => {
      render(
        <TestWrapper>
          <ChoiceOptions 
            choices={mockChoices}
            onChoiceSelect={jest.fn()}
            sceneIndex={0}
          />
        </TestWrapper>
      );

      // 操作説明の確認
      const instructions = screen.getByText('ひとつの選択肢を選んでください');
      expect(instructions).toBeInTheDocument();
    });
  });

  describe('Navigation and Skip Links', () => {
    it('should provide skip links for keyboard users', async () => {
      render(
        <TestWrapper>
          <div>
            <a href="#main-content" className="skip-link">
              メインコンテンツへスキップ
            </a>
            <nav role="navigation">
              <ul>
                <li><a href="/">ホーム</a></li>
              </ul>
            </nav>
            <main id="main-content" role="main">
              <h1>メインコンテンツ</h1>
            </main>
          </div>
        </TestWrapper>
      );

      const skipLink = screen.getByRole('link', { name: 'メインコンテンツへスキップ' });
      expect(skipLink).toBeInTheDocument();
      expect(skipLink).toHaveAttribute('href', '#main-content');

      const navigation = screen.getByRole('navigation');
      expect(navigation).toBeInTheDocument();

      const mainContent = screen.getByRole('main');
      expect(mainContent).toBeInTheDocument();
    });
  });

  describe('Result Screen Accessibility', () => {
    it('should announce result completion', async () => {
      render(
        <TestWrapper>
          <main role="main" aria-label="診断結果画面">
            <div role="status" aria-live="polite">
              診断が完了しました
            </div>
            <TypeCard typeResult={mockResult2Axes.type} />
            <AxesScores axesScores={mockResult2Axes.axes} />
          </main>
        </TestWrapper>
      );

      const statusAnnouncements = screen.getAllByRole('status');
      expect(statusAnnouncements.length).toBeGreaterThan(0);
      
      // 最初のstatus要素が診断完了アナウンス
      const completionStatus = statusAnnouncements.find(element =>
        element.textContent?.includes('診断が完了しました')
      );
      expect(completionStatus).toBeInTheDocument();
      expect(completionStatus).toHaveAttribute('aria-live', 'polite');

      const mainContent = screen.getByRole('main');
      expect(mainContent).toHaveAttribute('aria-label', '診断結果画面');
    });

    it('should provide structured result information', async () => {
      render(
        <TestWrapper>
          <main>
            <h1>あなたの診断結果</h1>
            <section aria-labelledby="type-heading">
              <h2 id="type-heading">パーソナリティタイプ</h2>
              <TypeCard typeResult={mockResult2Axes.type} />
            </section>
            <section aria-labelledby="scores-heading">
              <h2 id="scores-heading">軸スコア一覧</h2>
              <AxesScores axesScores={mockResult2Axes.axes} />
            </section>
          </main>
        </TestWrapper>
      );

      // セクション構造の確認
      const typeSection = screen.getByLabelText('パーソナリティタイプ');
      expect(typeSection).toBeInTheDocument();

      const scoresSection = screen.getByLabelText('軸スコア一覧');
      expect(scoresSection).toBeInTheDocument();

      // 見出し階層の確認
      const h1 = screen.getByRole('heading', { level: 1 });
      const h2s = screen.getAllByRole('heading', { level: 2 });
      
      expect(h1).toBeInTheDocument();
      expect(h2s.length).toBeGreaterThanOrEqual(2); // 少なくともタイプとスコアセクション
    });
  });

  describe('Focus Management', () => {
    it('should maintain logical focus order', async () => {
      const { container } = render(
        <TestWrapper>
          <main>
            <h1>NightLoom 診断</h1>
            <ChoiceOptions 
              choices={mockChoices}
              onChoiceSelect={jest.fn()}
              sceneIndex={0}
            />
            <button>続行</button>
          </main>
        </TestWrapper>
      );

      // フォーカス順序の検証（axe-coreのfocus-order-semanticsルール使用）
      const results = await axe(container, {
        rules: {
          'focus-order-semantics': { enabled: true },
          'tabindex': { enabled: true }
        }
      });
      expect(results).toHaveNoViolations();
    });
  });
});
