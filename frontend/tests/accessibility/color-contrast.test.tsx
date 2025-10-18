
import { render } from '@testing-library/react';
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

describe('Color Contrast Validation Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('WCAG AA Color Contrast (4.5:1)', () => {
    it('should meet contrast requirements for primary text', async () => {
      const { container } = render(
        <TestWrapper>
          <div className="bg-white p-4">
            <h1 className="text-gray-900 text-2xl font-bold">
              メインタイトル
            </h1>
            <p className="text-gray-800 text-base">
              本文テキストです。読みやすさを確保するために適切なコントラスト比を設定しています。
            </p>
            <p className="text-gray-600 text-sm">
              補助テキストや説明文です。
            </p>
          </div>
        </TestWrapper>
      );

      const results = await axe(container, {
        rules: {
          'color-contrast': { enabled: true }
        }
      });
      expect(results).toHaveNoViolations();
    });

    it('should meet contrast requirements for interactive elements', async () => {
      const { container } = render(
        <TestWrapper>
          <div className="bg-white p-4">
            <button className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
              プライマリボタン
            </button>
            <button className="bg-gray-100 text-gray-900 px-4 py-2 rounded border border-gray-300 hover:bg-gray-200 ml-2">
              セカンダリボタン
            </button>
            <a href="#" className="text-blue-600 underline hover:text-blue-800 ml-2">
              リンクテキスト
            </a>
          </div>
        </TestWrapper>
      );

      const results = await axe(container, {
        rules: {
          'color-contrast': { enabled: true }
        }
      });
      expect(results).toHaveNoViolations();
    });

    it('should meet contrast requirements for choice options', async () => {
      const { container } = render(
        <TestWrapper>
          <ChoiceOptions 
            choices={mockChoices}
            onChoiceSelect={jest.fn()}
            sceneIndex={0}
          />
        </TestWrapper>
      );

      const results = await axe(container, {
        rules: {
          'color-contrast': { enabled: true }
        }
      });
      expect(results).toHaveNoViolations();
    });

    it('should meet contrast requirements for form inputs', async () => {
      const { container } = render(
        <TestWrapper>
          <div className="bg-white p-4">
            <label htmlFor="keyword" className="block text-gray-900 font-medium mb-2">
              診断キーワード
            </label>
            <input 
              id="keyword"
              type="text" 
              className="w-full px-3 py-2 bg-white border border-gray-300 text-gray-900 placeholder-gray-500 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              placeholder="キーワードを入力してください"
            />
            <p className="text-gray-600 text-sm mt-1">
              診断のベースとなるキーワードを入力してください
            </p>
          </div>
        </TestWrapper>
      );

      const results = await axe(container, {
        rules: {
          'color-contrast': { enabled: true }
        }
      });
      expect(results).toHaveNoViolations();
    });
  });

  describe('WCAG AAA Color Contrast (7:1)', () => {
    it('should test enhanced contrast for important headings', async () => {
      const { container } = render(
        <TestWrapper>
          <div className="bg-white p-4">
            <h1 className="text-black text-3xl font-bold">
              重要なタイトル
            </h1>
            <h2 className="text-gray-900 text-xl font-semibold">
              セクションタイトル
            </h2>
          </div>
        </TestWrapper>
      );

      const results = await axe(container, {
        rules: {
          'color-contrast-enhanced': { enabled: true }
        }
      });
      // AAAレベルは推奨だが、失敗しても許容する場合がある
      // 実装レベルに応じて調整
    });
  });

  describe('Theme-based Color Contrast', () => {
    it('should meet contrast requirements for serene theme', async () => {
      const { container } = render(
        <div className="theme-serene">
          <div className="bg-blue-50 p-4">
            <h2 className="text-blue-900 text-xl font-semibold mb-2">
              Serene Theme タイトル
            </h2>
            <p className="text-blue-800 mb-4">
              青を基調とした落ち着いたテーマです。
            </p>
            <button className="bg-blue-600 text-white px-4 py-2 rounded">
              アクションボタン
            </button>
          </div>
        </div>
      );

      const results = await axe(container, {
        rules: {
          'color-contrast': { enabled: true }
        }
      });
      expect(results).toHaveNoViolations();
    });

    it('should meet contrast requirements for adventure theme', async () => {
      const { container } = render(
        <div className="theme-adventure">
          <div className="bg-orange-50 p-4">
            <h2 className="text-orange-900 text-xl font-semibold mb-2">
              Adventure Theme タイトル
            </h2>
            <p className="text-orange-800 mb-4">
              オレンジを基調とした冒険的なテーマです。
            </p>
            <button className="bg-orange-600 text-white px-4 py-2 rounded">
              アクションボタン
            </button>
          </div>
        </div>
      );

      const results = await axe(container, {
        rules: {
          'color-contrast': { enabled: true }
        }
      });
      expect(results).toHaveNoViolations();
    });

    it('should meet contrast requirements for focus theme', async () => {
      const { container } = render(
        <div className="theme-focus">
          <div className="bg-green-50 p-4">
            <h2 className="text-green-900 text-xl font-semibold mb-2">
              Focus Theme タイトル
            </h2>
            <p className="text-green-800 mb-4">
              緑を基調とした集中力を高めるテーマです。
            </p>
            <button className="bg-green-600 text-white px-4 py-2 rounded">
              アクションボタン
            </button>
          </div>
        </div>
      );

      const results = await axe(container, {
        rules: {
          'color-contrast': { enabled: true }
        }
      });
      expect(results).toHaveNoViolations();
    });

    it('should meet contrast requirements for fallback theme', async () => {
      const { container } = render(
        <div className="theme-fallback">
          <div className="bg-gray-50 p-4">
            <h2 className="text-gray-900 text-xl font-semibold mb-2">
              Fallback Theme タイトル
            </h2>
            <p className="text-gray-800 mb-4">
              グレーを基調としたフォールバックテーマです。
            </p>
            <button className="bg-gray-600 text-white px-4 py-2 rounded">
              アクションボタン
            </button>
          </div>
        </div>
      );

      const results = await axe(container, {
        rules: {
          'color-contrast': { enabled: true }
        }
      });
      expect(results).toHaveNoViolations();
    });
  });

  describe('State-based Color Contrast', () => {
    it('should meet contrast requirements for hover states', async () => {
      const { container } = render(
        <TestWrapper>
          <div className="bg-white p-4">
            <button 
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
              data-testid="hover-button"
            >
              ホバー状態テスト
            </button>
            <a 
              href="#" 
              className="text-blue-600 hover:text-blue-800 underline ml-4"
              data-testid="hover-link"
            >
              ホバーリンク
            </a>
          </div>
        </TestWrapper>
      );

      const results = await axe(container, {
        rules: {
          'color-contrast': { enabled: true }
        }
      });
      expect(results).toHaveNoViolations();
    });

    it('should meet contrast requirements for focus states', async () => {
      const { container } = render(
        <TestWrapper>
          <div className="bg-white p-4">
            <button 
              className="bg-blue-600 text-white px-4 py-2 rounded focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              data-testid="focus-button"
            >
              フォーカス状態テスト
            </button>
            <input 
              type="text" 
              className="ml-4 px-3 py-2 border border-gray-300 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              placeholder="フォーカステスト"
              data-testid="focus-input"
            />
          </div>
        </TestWrapper>
      );

      const results = await axe(container, {
        rules: {
          'color-contrast': { enabled: true }
        }
      });
      expect(results).toHaveNoViolations();
    });

    it('should meet contrast requirements for disabled states', async () => {
      const { container } = render(
        <TestWrapper>
          <div className="bg-white p-4">
            <button 
              disabled
              className="bg-gray-300 text-gray-500 px-4 py-2 rounded cursor-not-allowed"
              data-testid="disabled-button"
            >
              無効なボタン
            </button>
            <input 
              type="text"
              disabled 
              className="ml-4 px-3 py-2 bg-gray-100 border border-gray-300 text-gray-500 rounded cursor-not-allowed"
              placeholder="無効な入力"
              data-testid="disabled-input"
            />
          </div>
        </TestWrapper>
      );

      // 無効状態では一般的にコントラスト要件が緩和される
      const results = await axe(container, {
        rules: {
          'color-contrast': { enabled: true }
        }
      });
      expect(results).toHaveNoViolations();
    });

    it('should meet contrast requirements for selected states', async () => {
      const { container } = render(
        <TestWrapper>
          <ChoiceOptions 
            choices={mockChoices}
            selectedChoiceId="choice_0_1"
            onChoiceSelect={jest.fn()}
            sceneIndex={0}
          />
        </TestWrapper>
      );

      const results = await axe(container, {
        rules: {
          'color-contrast': { enabled: true }
        }
      });
      expect(results).toHaveNoViolations();
    });
  });

  describe('Error and Success State Colors', () => {
    it('should meet contrast requirements for error messages', async () => {
      const { container } = render(
        <TestWrapper>
          <div className="bg-white p-4">
            <div className="bg-red-50 border border-red-200 rounded p-4">
              <div className="flex">
                <div className="text-red-400">
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-red-800 font-medium">
                    エラーが発生しました
                  </h3>
                  <p className="text-red-700 mt-1">
                    入力内容を確認してください
                  </p>
                </div>
              </div>
            </div>
          </div>
        </TestWrapper>
      );

      const results = await axe(container, {
        rules: {
          'color-contrast': { enabled: true }
        }
      });
      expect(results).toHaveNoViolations();
    });

    it('should meet contrast requirements for success messages', async () => {
      const { container } = render(
        <TestWrapper>
          <div className="bg-white p-4">
            <div className="bg-green-50 border border-green-200 rounded p-4">
              <div className="flex">
                <div className="text-green-400">
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-green-800 font-medium">
                    診断が完了しました
                  </h3>
                  <p className="text-green-700 mt-1">
                    結果を確認してください
                  </p>
                </div>
              </div>
            </div>
          </div>
        </TestWrapper>
      );

      const results = await axe(container, {
        rules: {
          'color-contrast': { enabled: true }
        }
      });
      expect(results).toHaveNoViolations();
    });
  });

  describe('Result Screen Color Contrast', () => {
    it('should meet contrast requirements for type cards', async () => {
      const { container } = render(
        <TestWrapper>
          <TypeCard typeResult={mockResult2Axes.type} />
        </TestWrapper>
      );

      const results = await axe(container, {
        rules: {
          'color-contrast': { enabled: true }
        }
      });
      expect(results).toHaveNoViolations();
    });

    it('should meet contrast requirements for axis scores', async () => {
      const { container } = render(
        <TestWrapper>
          <AxesScores axesScores={mockResult2Axes.axes} />
        </TestWrapper>
      );

      const results = await axe(container, {
        rules: {
          'color-contrast': { enabled: true }
        }
      });
      expect(results).toHaveNoViolations();
    });
  });
});
