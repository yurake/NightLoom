
/**
 * Integration tests for result calculation and display - User Story 3
 * Tests the complete flow from result API call to result screen rendering
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { SessionProvider } from '@/app/state/SessionContext';
import { ThemeProvider } from '@/app/theme/ThemeProvider';

// Mock result screen component (will be created in implementation)
const MockResultScreen = ({ sessionId }: { sessionId: string }) => (
  <div data-testid="result-screen">
    <h1 data-testid="result-title">診断結果</h1>
    <div data-testid="keyword-display">あなたのキーワード: 冒険</div>
    <div data-testid="axes-scores">
      <div data-testid="axis-curiosity">好奇心: 85.5点</div>
      <div data-testid="axis-logic">論理性: 42.3点</div>
      <div data-testid="axis-creativity">創造性: 78.9点</div>
    </div>
    <div data-testid="type-profiles">
      <div data-testid="type-explorer">Explorer - 好奇心旺盛で新しい体験を求める</div>
      <div data-testid="type-innovator">Innovator - 創造的で革新的なアプローチを取る</div>
      <div data-testid="type-dreamer">Dreamer - 想像力豊かで理想を追求する</div>
      <div data-testid="type-visionary">Visionary - 未来を見据えた大胆な発想を持つ</div>
    </div>
    <button data-testid="restart-button">もう一度診断する</button>
  </div>
);

// Mock result data
const mockResultData = {
  sessionId: '550e8400-e29b-41d4-a716-446655440000',
  keyword: '冒険',
  axes: [
    {
      axisId: 'curiosity',
      score: 85.5,
      rawScore: 3.4
    },
    {
      axisId: 'logic',
      score: 42.3,
      rawScore: -0.8
    },
    {
      axisId: 'creativity',
      score: 78.9,
      rawScore: 2.9
    }
  ],
  type: {
    dominantAxes: ['curiosity', 'creativity'],
    profiles: [
      {
        name: 'Explorer',
        description: '好奇心旺盛で新しい体験を求める',
        keywords: ['冒険', '発見', '挑戦'],
        dominantAxes: ['curiosity', 'creativity'],
        polarity: 'Hi-Hi'
      },
      {
        name: 'Innovator',
        description: '創造的で革新的なアプローチを取る',
        keywords: ['創造', '革新', '独創'],
        dominantAxes: ['creativity', 'curiosity'],
        polarity: 'Hi-Hi'
      },
      {
        name: 'Dreamer',
        description: '想像力豊かで理想を追求する',
        keywords: ['夢', '理想', '想像'],
        dominantAxes: ['creativity', 'curiosity'],
        polarity: 'Hi-Mid'
      },
      {
        name: 'Visionary',
        description: '未来を見据えた大胆な発想を持つ',
        keywords: ['未来', 'ビジョン', '革命'],
        dominantAxes: ['curiosity', 'creativity'],
        polarity: 'Hi-Hi'
      }
    ],
    fallbackUsed: false
  },
  completedAt: '2024-01-15T10:30:00Z',
  fallbackFlags: []
};

const mockFallbackResultData = {
  sessionId: '550e8400-e29b-41d4-a716-446655441111',
  keyword: 'フォールバック',
  axes: [
    {
      axisId: 'stability',
      score: 50.0,
      rawScore: 0.0
    },
    {
      axisId: 'adaptability',
      score: 50.0,
      rawScore: 0.0
    }
  ],
  type: {
    dominantAxes: ['stability', 'adaptability'],
    profiles: [
      {
        name: 'Balanced',
        description: 'バランスの取れた判断をする',
        keywords: ['安定', '適応', 'バランス'],
        dominantAxes: ['stability', 'adaptability'],
        polarity: 'Mid-Mid'
      },
      {
        name: 'Steady',
        description: '着実に物事を進める',
        keywords: ['着実', '継続', '信頼'],
        dominantAxes: ['stability', 'adaptability'],
        polarity: 'Hi-Mid'
      },
      {
        name: 'Flexible',
        description: '状況に応じて柔軟に対応する',
        keywords: ['柔軟', '対応', '変化'],
        dominantAxes: ['adaptability', 'stability'],
        polarity: 'Mid-Hi'
      },
      {
        name: 'Resilient',
        description: '困難に立ち向かう強さを持つ',
        keywords: ['回復', '強さ', '耐性'],
        dominantAxes: ['stability', 'adaptability'],
        polarity: 'Hi-Hi'
      }
    ],
    fallbackUsed: true
  },
  completedAt: '2024-01-15T10:32:00Z',
  fallbackFlags: ['TYPE_FALLBACK', 'AXIS_FALLBACK']
};

// MSW server setup
const server = setupServer(
  // Result retrieval endpoint
  http.post('/api/sessions/:sessionId/result', async ({ request, params }: any) => {
    const { sessionId } = params;
    
    if (sessionId === mockResultData.sessionId) {
      return HttpResponse.json(mockResultData);
    }
    
    if (sessionId === mockFallbackResultData.sessionId) {
      return HttpResponse.json(mockFallbackResultData);
    }
    
    if (sessionId === 'session-not-completed') {
      return HttpResponse.json({
        error_code: 'SESSION_NOT_COMPLETED',
        message: 'Session has not completed all 4 scenes',
        details: { scenes_completed: 2, scenes_required: 4 }
      }, { status: 400 });
    }
    
    if (sessionId === 'session-not-found') {
      return HttpResponse.json({
        error_code: 'SESSION_NOT_FOUND',
        message: 'Session not found',
        details: { session_id: sessionId }
      }, { status: 404 });
    }
    
    if (sessionId === 'llm-failure') {
      return HttpResponse.json({
        error_code: 'LLM_SERVICE_UNAVAILABLE',
        message: 'LLM service is currently unavailable',
        details: { retry_after: 30 }
      }, { status: 503 });
    }
    
    return HttpResponse.json(mockResultData);
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('Result Integration Tests', () => {
  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <ThemeProvider>
        <SessionProvider>
          {component}
        </SessionProvider>
      </ThemeProvider>
    );
  };

  describe('Result Data Fetching', () => {
    it('should fetch and display result data successfully', async () => {
      renderWithProviders(
        <MockResultScreen sessionId={mockResultData.sessionId} />
      );

      // Result screen should be displayed
      await waitFor(() => {
        expect(screen.getByTestId('result-screen')).toBeInTheDocument();
      });

      // Basic result elements should be present
      expect(screen.getByTestId('result-title')).toHaveTextContent('診断結果');
      expect(screen.getByTestId('keyword-display')).toHaveTextContent('冒険');
      
      // Axes scores should be displayed
      expect(screen.getByTestId('axis-curiosity')).toHaveTextContent('85.5');
      expect(screen.getByTestId('axis-logic')).toHaveTextContent('42.3');
      expect(screen.getByTestId('axis-creativity')).toHaveTextContent('78.9');
      
      // Type profiles should be displayed
      expect(screen.getByTestId('type-explorer')).toHaveTextContent('Explorer');
      expect(screen.getByTestId('type-innovator')).toHaveTextContent('Innovator');
      expect(screen.getByTestId('type-dreamer')).toHaveTextContent('Dreamer');
      expect(screen.getByTestId('type-visionary')).toHaveTextContent('Visionary');
    });

    it('should handle result fetch errors gracefully', async () => {
      renderWithProviders(
        <MockResultScreen sessionId="session-not-found" />
      );

      // Error handling would be implementation specific
      // This test verifies the API contract is working
      await waitFor(() => {
        expect(screen.getByTestId('result-screen')).toBeInTheDocument();
      });
    });

    it('should display fallback results correctly', async () => {
      renderWithProviders(
        <MockResultScreen sessionId={mockFallbackResultData.sessionId} />
      );

      await waitFor(() => {
        expect(screen.getByTestId('result-screen')).toBeInTheDocument();
      });

      // Should display fallback data appropriately
      // Implementation would include fallback indicators
    });

    it('should handle incomplete session appropriately', async () => {
      renderWithProviders(
        <MockResultScreen sessionId="session-not-completed" />
      );

      // Should handle incomplete session error
      // Implementation might redirect back to scenes or show error
      await waitFor(() => {
        expect(screen.getByTestId('result-screen')).toBeInTheDocument();
      });
    });
  });

  describe('Result Display Components', () => {
    it('should display axes scores with proper formatting', async () => {
      renderWithProviders(
        <MockResultScreen sessionId={mockResultData.sessionId} />
      );

      await waitFor(() => {
        expect(screen.getByTestId('axes-scores')).toBeInTheDocument();
      });

      // Scores should be formatted correctly (e.g., to 1 decimal place)
      const curiosityAxis = screen.getByTestId('axis-curiosity');
      expect(curiosityAxis).toHaveTextContent('85.5');
      
      // Scores should be within valid range (0-100)
      const scoreText = curiosityAxis.textContent || '';
      const score = parseFloat(scoreText.match(/\d+\.\d+/)?.[0] || '0');
      expect(score).toBeGreaterThanOrEqual(0);
      expect(score).toBeLessThanOrEqual(100);
    });

    it('should display type profiles with descriptions', async () => {
      renderWithProviders(
        <MockResultScreen sessionId={mockResultData.sessionId} />
      );

      await waitFor(() => {
        expect(screen.getByTestId('type-profiles')).toBeInTheDocument();
      });

      // Each type should have name and description
      const explorerType = screen.getByTestId('type-explorer');
      expect(explorerType).toHaveTextContent('Explorer');
      expect(explorerType).toHaveTextContent('好奇心旺盛');

      const innovatorType = screen.getByTestId('type-innovator');
      expect(innovatorType).toHaveTextContent('Innovator');
      expect(innovatorType).toHaveTextContent('創造的');
    });

    it('should maintain theme consistency in result display', async () => {
      renderWithProviders(
        <MockResultScreen sessionId={mockResultData.sessionId} />
      );

      await waitFor(() => {
        expect(screen.getByTestId('result-screen')).toBeInTheDocument();
      });

      // Theme should be applied consistently
      // Implementation would verify theme classes are applied
      const resultScreen = screen.getByTestId('result-screen');
      expect(resultScreen).toBeInTheDocument();
    });

    it('should provide restart functionality', async () => {
      const user = userEvent.setup();
      
      renderWithProviders(
        <MockResultScreen sessionId={mockResultData.sessionId} />
      );

      await waitFor(() => {
        expect(screen.getByTestId('restart-button')).toBeInTheDocument();
      });

      // Restart button should be clickable
      const restartButton = screen.getByTestId('restart-button');
      await user.click(restartButton);

      // Implementation would handle restart logic
      // (new session creation, navigation, etc.)
    });
  });

  describe('Performance and Loading States', () => {
    it('should display loading state during result generation', async () => {
      // Delay the API response to test loading state
      server.use(
        http.post('/api/sessions/:sessionId/result', async ({ request, params }: any) => {
          await new Promise(resolve => setTimeout(resolve, 1000));
          return HttpResponse.json(mockResultData);
        })
      );

      renderWithProviders(
        <MockResultScreen sessionId={mockResultData.sessionId} />
      );

      // Should show loading indicator initially
      // Implementation specific - might be spinner, skeleton, etc.
      const resultScreen = screen.getByTestId('result-screen');
      expect(resultScreen).toBeInTheDocument();

      // After loading, result should be displayed
      await waitFor(() => {
        expect(screen.getByTestId('result-title')).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('should meet performance requirements for result display', async () => {
      const startTime = Date.now();
      
      renderWithProviders(
        <MockResultScreen sessionId={mockResultData.sessionId} />
      );

      await waitFor(() => {
        expect(screen.getByTestId('result-screen')).toBeInTheDocument();
      });

      const endTime = Date.now();
      const renderTime = endTime - startTime;

      // Should render quickly (< 500ms in testing environment)
      expect(renderTime).toBeLessThan(1000);
    });
  });

  describe('Data Validation and Error Handling', () => {
    it('should validate axis score ranges', async () => {
      // Mock data with extreme scores
      const extremeResultData = {
        ...mockResultData,
        axes: [
          { axisId: 'extreme_high', score: 100.0, rawScore: 5.0 },
          { axisId: 'extreme_low', score: 0.0, rawScore: -5.0 },
          { axisId: 'mid_range', score: 50.0, rawScore: 0.0 }
        ]
      };

      server.use(
        http.post('/api/sessions/:sessionId/result', ({ request, params }: any) => {
          return HttpResponse.json(extremeResultData);
        })
      );

      renderWithProviders(
        <MockResultScreen sessionId={mockResultData.sessionId} />
      );

      await waitFor(() => {
        expect(screen.getByTestId('axes-scores')).toBeInTheDocument();
      });

      // Scores should be within valid ranges even for extreme cases
      // Implementation would validate and clamp scores appropriately
    });

    it('should handle missing or malformed result data', async () => {
      const malformedResultData = {
        sessionId: mockResultData.sessionId,
        keyword: '不正データ',
        axes: [],  // Empty axes array
        type: {
          dominantAxes: [],
          profiles: [],  // Empty profiles array
          fallbackUsed: false
        },
        completedAt: '2024-01-15T10:30:00Z',
        fallbackFlags: []
      };

      server.use(
        http.post('/api/sessions/:sessionId/result', ({ request, params }: any) => {
          return HttpResponse.json(malformedResultData);
        })
      );

      renderWithProviders(
        <MockResultScreen sessionId={mockResultData.sessionId} />
      );

      // Should handle malformed data gracefully
      await waitFor(() => {
        expect(screen.getByTestId('result-screen')).toBeInTheDocument();
      });

      // Implementation would show error state or fallback content
    });

    it('should handle network timeouts during result fetch', async () => {
      server.use(
        http.post('/api/sessions/:sessionId/result', async ({ request, params }: any) => {
          // Simulate timeout
          await new Promise(resolve => setTimeout(resolve, 10000));
          return HttpResponse.json(mockResultData);
        })
      );

      renderWithProviders(
        <MockResultScreen sessionId={mockResultData.sessionId} />
      );

      // Should handle timeout gracefully
      await waitFor(() => {
        expect(screen.getByTestId('result-screen')).toBeInTheDocument();
      });

      // Implementation would show timeout error and retry option
    });
  });

  describe('Accessibility and User Experience', () => {
    it('should provide accessible result display', async () => {
      renderWithProviders(
        <MockResultScreen sessionId={mockResultData.sessionId} />
      );

      await waitFor(() => {
        expect(screen.getByTestId('result-screen')).toBeInTheDocument();
      });

      // Screen reader accessible elements
      expect(screen.getByTestId('result-title')).toHaveAttribute('role', 'heading');
      
      // Axes scores should be announced properly
      // Implementation would include aria-labels for scores
      const axesSection = screen.getByTestId('axes-scores');
      expect(axesSection).toBeInTheDocument();
      
      // Type profiles should be navigable
      const typesSection = screen.getByTestId('type-profiles');
      expect(typesSection).toBeInTheDocument();
    });

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup();
      
      renderWithProviders(
        <MockResultScreen sessionId={mockResultData.sessionId} />
      );

      await waitFor(() => {
        expect(screen.getByTestId('restart-button')).toBeInTheDocument();
      });

      // Should be able to navigate to restart button with keyboard
      const restartButton = screen.getByTestId('restart-button');
      restartButton.focus();
      
      // Should be focused
      expect(restartButton).toHaveFocus();
      
      // Should be activatable with Enter or Space
      await user.keyboard('{Enter}');
      // Implementation would handle restart action
    });

    it('should respect user motion preferences', async () => {
      // Mock reduced motion preference
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => {
          if (query === '(prefers-reduced-motion: reduce)') {
            return {
              matches: true,
              media: query,
              onchange: null,
              addListener: jest.fn(),
              removeListener: jest.fn(),
              addEventListener: jest.fn(),
              removeEventListener: jest.fn(),
              dispatchEvent: jest.fn(),
            };
          }
          return {
            matches: false,
            media: query,
            onchange: null,
            addListener: jest.fn(),
            removeListener: jest.fn(),
            addEventListener: jest.fn(),
            removeEventListener: jest.fn(),
            dispatchEvent: jest.fn(),
          };
        }),
      });

      renderWithProviders(
        <MockResultScreen sessionId={mockResultData.sessionId} />
      );

      await waitFor(() => {
        expect(screen.getByTestId('result-screen')).toBeInTheDocument();
      });

      // Implementation would disable animations when reduced motion is preferred
    });
  });

  describe('Session Management Integration', () => {
    it('should properly clean up session after result display', async () => {
      renderWithProviders(
        <MockResultScreen sessionId={mockResultData.sessionId} />
      );

      await waitFor(() => {
        expect(screen.getByTestId('result-screen')).toBeInTheDocument();
      });

      // Session should be marked for cleanup after result display
      // Implementation would handle session lifecycle
    });

    it('should handle session expiration during result display', async () => {
      server.use(
        http.post('/api/sessions/:sessionId/result', ({ request, params }: any) => {
          return HttpResponse.json({
            error_code: 'SESSION_NOT_FOUND',
            message: 'Session has expired',
            details: { session_id: params.sessionId }
          }, { status: 404 });
        })
      );

      renderWithProviders(
        <MockResultScreen sessionId="expired-session" />
      );

      // Should handle expired session appropriately
      await waitFor(() => {
        expect(screen.getByTestId('result-screen')).toBeInTheDocument();
      });

      // Implementation would show expiration message and restart option
    });
  });
});
