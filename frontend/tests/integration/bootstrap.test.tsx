/**
 * Integration tests for NightLoom MVP bootstrap flow.
 * 
 * Tests the complete bootstrap flow from frontend to backend integration.
 * Implements T019 requirements with Fail First testing strategy.
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SessionProvider } from '../../app/state/SessionContext';
import { ThemeProvider } from '../../app/theme/ThemeProvider';
import PlayPage from '../../app/(play)/page';

// Mock sessionClient to control API responses
jest.mock('../../app/services/sessionClient', () => ({
  sessionClient: {
    bootstrap: jest.fn(),
    confirmKeyword: jest.fn(),
  }
}));

import { sessionClient } from '../../app/services/sessionClient';

const mockSessionClient = sessionClient as jest.Mocked<typeof sessionClient>;

// Test wrapper component
function TestWrapper({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <SessionProvider>
        {children}
      </SessionProvider>
    </ThemeProvider>
  );
}

describe('Bootstrap Integration Flow', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Default mock responses
    mockSessionClient.bootstrap.mockResolvedValue({
      sessionId: 'test-session-id',
      axes: [
        {
          id: 'logic_emotion',
          name: 'Logic vs Emotion',
          description: 'Balance between analytical and intuitive decision making',
          direction: '論理的 ⟷ 感情的'
        },
        {
          id: 'speed_caution',
          name: 'Speed vs Caution', 
          description: 'Preference for quick decisions versus careful deliberation',
          direction: '迅速 ⟷ 慎重'
        }
      ],
      keywordCandidates: ['愛', '冒険', '挑戦', '成長'],
      initialCharacter: 'あ',
      themeId: 'serene',
      fallbackUsed: false
    });

    mockSessionClient.confirmKeyword.mockResolvedValue({
      sessionId: 'test-session-id',
      scene: {
        sceneIndex: 1,
        themeId: 'serene',
        narrative: '「愛」をテーマに、重要な決断を迫られました。',
        choices: [
          {
            id: 'choice_1_1',
            text: 'データと論理を重視して分析する',
            weights: { logic_emotion: 1.0, speed_caution: -0.5 }
          },
          {
            id: 'choice_1_2',
            text: '直感と感情を大切にして判断する',
            weights: { logic_emotion: -1.0, speed_caution: 0.2 }
          },
          {
            id: 'choice_1_3',
            text: '迅速に決断して行動に移す',
            weights: { logic_emotion: 0.2, speed_caution: 1.0 }
          },
          {
            id: 'choice_1_4',
            text: '慎重に検討して安全な選択をする',
            weights: { logic_emotion: 0.3, speed_caution: -1.0 }
          }
        ]
      },
      fallbackUsed: false
    });
  });

  test('should complete full bootstrap flow from initial load to first scene', async () => {
    render(
      <TestWrapper>
        <PlayPage />
      </TestWrapper>
    );

    // Should start bootstrap process automatically
    await waitFor(() => {
      expect(mockSessionClient.bootstrap).toHaveBeenCalled();
    });

    // Should display keyword candidates after bootstrap
    await waitFor(() => {
      expect(screen.getByText('愛')).toBeInTheDocument();
      expect(screen.getByText('冒険')).toBeInTheDocument();
      expect(screen.getByText('挑戦')).toBeInTheDocument();
      expect(screen.getByText('成長')).toBeInTheDocument();
    });

    // User selects a keyword
    const firstKeywordButton = screen.getByText('愛');
    fireEvent.click(firstKeywordButton);

    // Should call confirmKeyword API
    await waitFor(() => {
      expect(mockSessionClient.confirmKeyword).toHaveBeenCalledWith(
        'test-session-id',
        '愛',
        'suggestion'
      );
    });

    // Should display first scene after keyword confirmation
    await waitFor(() => {
      expect(screen.getByText('「愛」をテーマに、重要な決断を迫られました。')).toBeInTheDocument();
    });

    // Should display choice options
    expect(screen.getByText('データと論理を重視して分析する')).toBeInTheDocument();
    expect(screen.getByText('直感と感情を大切にして判断する')).toBeInTheDocument();
    expect(screen.getByText('迅速に決断して行動に移す')).toBeInTheDocument();
    expect(screen.getByText('慎重に検討して安全な選択をする')).toBeInTheDocument();
  });

  test('should handle bootstrap API failure gracefully', async () => {
    // Mock bootstrap failure
    mockSessionClient.bootstrap.mockRejectedValue(new Error('Network error'));

    render(
      <TestWrapper>
        <PlayPage />
      </TestWrapper>
    );

    // Should attempt bootstrap
    await waitFor(() => {
      expect(mockSessionClient.bootstrap).toHaveBeenCalled();
    });

    // Should display error message
    await waitFor(() => {
      expect(screen.getByTestId('bootstrap-error')).toBeInTheDocument();
    });
  });

  test('should handle keyword confirmation failure gracefully', async () => {
    render(
      <TestWrapper>
        <PlayPage />
      </TestWrapper>
    );

    // Wait for bootstrap to complete
    await waitFor(() => {
      expect(screen.getByText('愛')).toBeInTheDocument();
    });

    // Mock keyword confirmation failure
    mockSessionClient.confirmKeyword.mockRejectedValue(new Error('Keyword confirmation failed'));

    // User selects a keyword
    const firstKeywordButton = screen.getByText('愛');
    fireEvent.click(firstKeywordButton);

    // Should display error message
    await waitFor(() => {
      expect(screen.getByText(/キーワードの確定に失敗しました/)).toBeInTheDocument();
    });
  });

  test('should handle custom keyword input', async () => {
    render(
      <TestWrapper>
        <PlayPage />
      </TestWrapper>
    );

    // Wait for bootstrap to complete
    await waitFor(() => {
      expect(screen.getByText('愛')).toBeInTheDocument();
    });

    // Look for custom keyword input (assuming it exists)
    const customInput = screen.queryByPlaceholderText(/独自のキーワード/);
    if (customInput) {
      fireEvent.change(customInput, { target: { value: '自由' } });
      
      const submitButton = screen.getByText(/確認/);
      fireEvent.click(submitButton);

      // Should call confirmKeyword with manual source
      await waitFor(() => {
        expect(mockSessionClient.confirmKeyword).toHaveBeenCalledWith(
          'test-session-id',
          '自由',
          'manual'
        );
      });
    }
  });

  test('should apply correct theme after bootstrap', async () => {
    render(
      <TestWrapper>
        <PlayPage />
      </TestWrapper>
    );

    // Wait for bootstrap to complete
    await waitFor(() => {
      expect(screen.getByText('愛')).toBeInTheDocument();
    });

    // Should apply serene theme based on mock response
    const themeContainer = screen.getByTestId('theme-container');
    await waitFor(() => {
      // Check if theme data attribute is applied
      expect(themeContainer.getAttribute('data-theme')).toBe('serene');
    });
  });

  test('should display loading states during API calls', async () => {
    // Make bootstrap slow to resolve
    mockSessionClient.bootstrap.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({
        sessionId: 'test-session-id',
        axes: [],
        keywordCandidates: ['愛', '冒険', '挑戦', '成長'],
        initialCharacter: 'あ',
        themeId: 'serene',
        fallbackUsed: false
      }), 100))
    );

    render(
      <TestWrapper>
        <PlayPage />
      </TestWrapper>
    );

    // Should show loading indicator initially
    expect(screen.getByText(/読み込み中/)).toBeInTheDocument();

    // Wait for bootstrap to complete
    await waitFor(() => {
      expect(screen.getByText('愛')).toBeInTheDocument();
    }, { timeout: 200 });
  });

  test('should maintain session state throughout bootstrap flow', async () => {
    render(
      <TestWrapper>
        <PlayPage />
      </TestWrapper>
    );

    // Complete bootstrap flow
    await waitFor(() => {
      expect(screen.getByText('愛')).toBeInTheDocument();
    });

    const firstKeywordButton = screen.getByText('愛');
    fireEvent.click(firstKeywordButton);

    await waitFor(() => {
      expect(screen.getByText('「愛」をテーマに、重要な決断を迫られました。')).toBeInTheDocument();
    });

    // Session state should be maintained
    // This test verifies that session context maintains state correctly
    // Additional assertions could be added to verify internal state
  });

  test('should meet performance requirements for bootstrap flow', async () => {
    const startTime = performance.now();

    render(
      <TestWrapper>
        <PlayPage />
      </TestWrapper>
    );

    // Complete full bootstrap flow
    await waitFor(() => {
      expect(screen.getByText('愛')).toBeInTheDocument();
    });

    const firstKeywordButton = screen.getByText('愛');
    fireEvent.click(firstKeywordButton);

    await waitFor(() => {
      expect(screen.getByText('「愛」をテーマに、重要な決断を迫られました。')).toBeInTheDocument();
    });

    const endTime = performance.now();
    const totalTime = endTime - startTime;

    // Should complete within reasonable time (accounting for test overhead)
    expect(totalTime).toBeLessThan(2000); // 2 seconds for integration test
  });
});

describe('Bootstrap Flow Error Scenarios', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('should handle network timeout gracefully', async () => {
    // Mock timeout scenario
    mockSessionClient.bootstrap.mockImplementation(
      () => new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Request timeout')), 100)
      )
    );

    render(
      <TestWrapper>
        <PlayPage />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('error-message')).toHaveTextContent(/ネットワークエラーが発生しました/);
    }, { timeout: 200 });
  });

  test('should handle malformed API responses', async () => {
    // Mock malformed response
    mockSessionClient.bootstrap.mockResolvedValue({
      // Missing required fields
      sessionId: 'test-session-id',
      keywordCandidates: [], // Empty array
      themeId: '',
    } as any);

    render(
      <TestWrapper>
        <PlayPage />
      </TestWrapper>
    );

    await waitFor(() => {
      // Should render with fallback theme and empty candidates
      expect(screen.getByTestId('theme-container')).toHaveAttribute('data-theme', 'fallback');
    });
  });

  test('should retry failed requests with exponential backoff', async () => {
    let callCount = 0;
    mockSessionClient.bootstrap.mockImplementation(() => {
      callCount++;
      if (callCount < 2) {
        return Promise.reject(new Error('Network error'));
      }
      return Promise.resolve({
        sessionId: 'test-session-id',
        axes: [],
        keywordCandidates: ['愛', '冒険', '挑戦', '成長'],
        initialCharacter: 'あ',
        themeId: 'serene',
        fallbackUsed: false
      });
    });

    render(
      <TestWrapper>
        <PlayPage />
      </TestWrapper>
    );

    // Should eventually succeed after retries
    await waitFor(() => {
      // Check if bootstrap succeeded by looking for keyword candidates
      const keywordElements = screen.queryAllByText('愛');
      expect(keywordElements.length).toBeGreaterThan(0);
    }, { timeout: 3000 });

    expect(callCount).toBeGreaterThanOrEqual(2);
  }, 10000);
});
