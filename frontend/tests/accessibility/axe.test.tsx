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

describe('Accessibility Tests with axe-core', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Scene Component', () => {
    it('should not have accessibility violations', async () => {
      const { container } = render(
        <TestWrapper>
          <Scene 
            sessionId="test-session"
            sceneIndex={0}
            onChoiceSubmit={jest.fn()}
            onSceneComplete={jest.fn()}
          />
        </TestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('ChoiceOptions Component', () => {
    it('should not have accessibility violations', async () => {
      const { container } = render(
        <TestWrapper>
          <ChoiceOptions 
            choices={mockChoices}
            onChoiceSelect={jest.fn()}
            sceneIndex={0}
          />
        </TestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations when disabled', async () => {
      const { container } = render(
        <TestWrapper>
          <ChoiceOptions 
            choices={mockChoices}
            onChoiceSelect={jest.fn()}
            sceneIndex={0}
            disabled={true}
          />
        </TestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('ResultScreen Component', () => {
    it('should not have accessibility violations', async () => {
      const { container } = render(
        <TestWrapper>
          <ResultScreen 
            sessionId="test-session"
            apiClient={mockApiClient}
          />
        </TestWrapper>
      );

      // API呼び出しの完了を待つ
      await new Promise(resolve => setTimeout(resolve, 100));

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('AxesScores Component', () => {
    it('should not have accessibility violations', async () => {
      const { container } = render(
        <TestWrapper>
          <AxesScores axesScores={mockResult2Axes.axes} />
        </TestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('TypeCard Component', () => {
    it('should not have accessibility violations', async () => {
      const { container } = render(
        <TestWrapper>
          <TypeCard typeResult={mockResult2Axes.type} />
        </TestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('Color Contrast Tests', () => {
    it('should pass color contrast requirements', async () => {
      const { container } = render(
        <TestWrapper>
          <div className="bg-white text-black p-4">
            <h1 className="text-blue-600 text-xl font-bold">Primary Text</h1>
            <p className="text-gray-700">Secondary Text</p>
            <button className="bg-blue-600 text-white px-4 py-2 rounded">
              Button Text
            </button>
          </div>
        </TestWrapper>
      );

      const results = await axe(container, {
        rules: {
          'color-contrast': { enabled: true },
          'color-contrast-enhanced': { enabled: true }
        }
      });
      expect(results).toHaveNoViolations();
    });
  });

  describe('WCAG 2.1 AA Compliance Tests', () => {
    it('should pass WCAG 2.1 AA level tests for choice selection', async () => {
      const { container } = render(
        <TestWrapper>
          <main role="main">
            <h1>NightLoom 診断</h1>
            <ChoiceOptions 
              choices={mockChoices}
              onChoiceSelect={jest.fn()}
              sceneIndex={0}
            />
          </main>
        </TestWrapper>
      );

      const results = await axe(container, {
        tags: ['wcag2a', 'wcag2aa', 'wcag21aa']
      });
      expect(results).toHaveNoViolations();
    });

    it('should pass WCAG 2.1 AA level tests for result display', async () => {
      const { container } = render(
        <TestWrapper>
          <main role="main">
            <h1>診断結果</h1>
            <TypeCard typeResult={mockResult2Axes.type} />
            <AxesScores axesScores={mockResult2Axes.axes} />
          </main>
        </TestWrapper>
      );

      const results = await axe(container, {
        tags: ['wcag2a', 'wcag2aa', 'wcag21aa']
      });
      expect(results).toHaveNoViolations();
    });
  });

  describe('Keyboard Navigation Tests', () => {
    it('should support keyboard navigation for choice selection', async () => {
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
          'focus-order-semantics': { enabled: true },
          'tabindex': { enabled: true }
        }
      });
      expect(results).toHaveNoViolations();
    });
  });

  describe('Screen Reader Compatibility Tests', () => {
    it('should have proper ARIA labels and roles', async () => {
      const { container } = render(
        <TestWrapper>
          <main role="main" aria-label="診断結果画面">
            <TypeCard typeResult={mockResult2Axes.type} />
            <AxesScores axesScores={mockResult2Axes.axes} />
          </main>
        </TestWrapper>
      );

      const results = await axe(container, {
        rules: {
          'aria-roles': { enabled: true },
          'aria-allowed-attr': { enabled: true },
          'aria-required-attr': { enabled: true },
          'label': { enabled: true }
        }
      });
      expect(results).toHaveNoViolations();
    });
  });
});
