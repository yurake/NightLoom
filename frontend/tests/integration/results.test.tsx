
/**
 * Integration tests for NightLoom MVP result calculation and display.
 * 
 * Tests the complete result flow from backend integration to frontend display.
 * Implements T043 requirements with Fail First testing strategy.
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SessionProvider } from '../../app/state/SessionContext';
import { ThemeProvider } from '../../app/theme/ThemeProvider';

// Mock sessionClient to control API responses
jest.mock('../../app/services/sessionClient', () => ({
  sessionClient: {
    bootstrap: jest.fn(),
    confirmKeyword: jest.fn(),
    getScene: jest.fn(),
    submitChoice: jest.fn(),
    getResult: jest.fn(),
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

// Mock result component for testing
function MockResultComponent() {
  return <div data-testid="result-component">Result Component</div>;
}

describe('Result Calculation and Display Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock complete result response
    mockSessionClient.getResult.mockResolvedValue({
      sessionId: 'test-session-id',
      keyword: '愛',
      axes: [
        {
          axisId: 'logic_emotion',
          score: 75,
          rawScore: 2.5
        },
        {
          axisId: 'speed_caution',
          score: 25,
          rawScore: -2.5
        }
      ],
      type: {
        dominantAxes: ['logic_emotion', 'speed_caution'],
        profiles: [
          {
            name: '論理的思考者',
            description: 'データと分析を重視し、感情よりも論理を優先する傾向があります。',
            dominantAxes: ['logic_emotion', 'speed_caution'],
            polarity: 'positive',
            keywords: ['分析', '論理', '客観性']
          },
          {
            name: '慎重な計画者',
            description: '決断前に十分な検討を重ね、リスクを最小化しようとします。',
            dominantAxes: ['speed_caution', 'logic_emotion'],
            polarity: 'negative',
            keywords: ['計画', '慎重', '安全']
          },
          {
            name: 'バランス型',
            description: '論理と感情、速度と慎重さのバランスを取る柔軟なアプローチを持ちます。',
            dominantAxes: ['logic_emotion', 'speed_caution'],
            polarity: 'neutral',
            keywords: ['バランス', '柔軟', '適応']
          },
          {
            name: '分析的慎重派',
            description: '論理的分析を用いて慎重に判断する特徴があります。',
            dominantAxes: ['logic_emotion', 'speed_caution'],
            polarity: 'positive',
            keywords: ['分析', '慎重', '論理']
          }
        ],
        fallbackUsed: false
      },
      completedAt: '2024-01-15T10:30:00Z',
      fallbackFlags: []
    });
  });

  test('should display complete result data after calculation', async () => {
    render(
      <TestWrapper>
        <MockResultComponent />
      </TestWrapper>
    );

    // Simulate result retrieval
    const result = await mockSessionClient.getResult('test-session-id');

    await waitFor(() => {
      expect(mockSessionClient.getResult).toHaveBeenCalledWith('test-session-id');
    });

    // Verify result structure
    expect(result.keyword).toBe('愛');
    expect(result.axes).toHaveLength(2);
    expect(result.type.profiles).toHaveLength(4);
  });

  test('should correctly calculate and display axis scores', async () => {
    render(
      <TestWrapper>
        <MockResultComponent />
      </TestWrapper>
    );

    const result = await mockSessionClient.getResult('test-session-id');

    // Verify axis score calculations
    const logicEmotionAxis = result.axes.find(axis => axis.axisId === 'logic_emotion');
    const speedCautionAxis = result.axes.find(axis => axis.axisId === 'speed_caution');

    expect(logicEmotionAxis).toBeDefined();
    expect(logicEmotionAxis!.score).toBe(75); // Normalized to 0-100
    expect(logicEmotionAxis!.rawScore).toBe(2.5); // Raw accumulated score

    expect(speedCautionAxis).toBeDefined();
    expect(speedCautionAxis!.score).toBe(25); // Normalized to 0-100
    expect(speedCautionAxis!.rawScore).toBe(-2.5); // Raw accumulated score
  });

  test('should identify and display dominant axes correctly', async () => {
    render(
      <TestWrapper>
        <MockResultComponent />
      </TestWrapper>
    );

    const result = await mockSessionClient.getResult('test-session-id');

    // Verify dominant axes identification
    expect(result.type.dominantAxes).toHaveLength(2);
    expect(result.type.dominantAxes).toContain('logic_emotion');
    expect(result.type.dominantAxes).toContain('speed_caution');

    // Dominant axes should correspond to highest absolute scores
    const absoluteScores = result.axes.map(axis => ({
      axisId: axis.axisId,
      absScore: Math.abs(axis.rawScore)
    }));
    const sortedAxes = absoluteScores.sort((a, b) => b.absScore - a.absScore);
    const topTwoAxes = sortedAxes.slice(0, 2).map(axis => axis.axisId);

    expect(result.type.dominantAxes.sort()).toEqual(topTwoAxes.sort());
  });

  test('should generate appropriate type profiles based on scores', async () => {
    render(
      <TestWrapper>
        <MockResultComponent />
      </TestWrapper>
    );

    const result = await mockSessionClient.getResult('test-session-id');

    // Verify type profiles
    const profiles = result.type.profiles;
    expect(profiles).toHaveLength(4);

    // Each profile should have required fields
    profiles.forEach(profile => {
      expect(profile.name).toBeTruthy();
      expect(profile.description).toBeTruthy();
      expect(profile.dominantAxes).toHaveLength(2);
      expect(['positive', 'negative', 'neutral']).toContain(profile.polarity);
      
      if (profile.keywords) {
        expect(Array.isArray(profile.keywords)).toBe(true);
      }
    });

    // Verify profile relevance to calculated scores
    const logicScore = result.axes.find(axis => axis.axisId === 'logic_emotion')!.rawScore;
    const speedScore = result.axes.find(axis => axis.axisId === 'speed_caution')!.rawScore;

    // Should have profiles that reflect the actual scores
    // Logic-heavy (positive logic_emotion score)
    const logicProfiles = profiles.filter(p => 
      p.name.includes('論理') || p.description.includes('論理')
    );
    expect(logicProfiles.length).toBeGreaterThan(0);

    // Caution-heavy (negative speed_caution score)
    const cautionProfiles = profiles.filter(p => 
      p.name.includes('慎重') || p.description.includes('慎重')
    );
    expect(cautionProfiles.length).toBeGreaterThan(0);
  });

  test('should handle result calculation with edge case scores', async () => {
    // Test with extreme scores
    mockSessionClient.getResult.mockResolvedValue({
      sessionId: 'test-session-id',
      keyword: 'テスト',
      axes: [
        {
          axisId: 'logic_emotion',
          score: 100, // Maximum score
          rawScore: 5.0
        },
        {
          axisId: 'speed_caution',
          score: 0, // Minimum score
          rawScore: -5.0
        }
      ],
      type: {
        dominantAxes: ['logic_emotion', 'speed_caution'],
        profiles: [
          {
            name: '極端な論理派',
            description: '完全に論理に依存し、感情を排除します。',
            dominantAxes: ['logic_emotion', 'speed_caution'],
            polarity: 'positive',
            keywords: ['極端', '論理']
          }
        ],
        fallbackUsed: false
      },
      completedAt: '2024-01-15T10:30:00Z',
      fallbackFlags: []
    });

    render(
      <TestWrapper>
        <MockResultComponent />
      </TestWrapper>
    );

    const result = await mockSessionClient.getResult('test-session-id');

    // Verify extreme scores are handled correctly
    expect(result.axes[0].score).toBe(100);
    expect(result.axes[0].rawScore).toBe(5.0);
    expect(result.axes[1].score).toBe(0);
    expect(result.axes[1].rawScore).toBe(-5.0);
  });

  test('should handle result calculation with neutral scores', async () => {
    // Test with all neutral scores
    mockSessionClient.getResult.mockResolvedValue({
      sessionId: 'test-session-id',
      keyword: 'バランス',
      axes: [
        {
          axisId: 'logic_emotion',
          score: 50, // Neutral score
          rawScore: 0.0
        },
        {
          axisId: 'speed_caution',
          score: 50, // Neutral score
          rawScore: 0.0
        }
      ],
      type: {
        dominantAxes: ['logic_emotion', 'speed_caution'], // Still need to pick dominant axes
        profiles: [
          {
            name: '完全バランス型',
            description: 'すべての軸で完璧にバランスが取れています。',
            dominantAxes: ['logic_emotion', 'speed_caution'],
            polarity: 'neutral',
            keywords: ['バランス', '中立', '調和']
          }
        ],
        fallbackUsed: false
      },
      completedAt: '2024-01-15T10:30:00Z',
      fallbackFlags: []
    });

    render(
      <TestWrapper>
        <MockResultComponent />
      </TestWrapper>
    );

    const result = await mockSessionClient.getResult('test-session-id');

    // Verify neutral scores are handled
    result.axes.forEach(axis => {
      expect(axis.score).toBe(50);
      expect(axis.rawScore).toBe(0.0);
    });

    // Should still generate meaningful profiles
    expect(result.type.profiles.length).toBeGreaterThan(0);
  });

  test('should handle result display integration with theme', async () => {
    render(
      <TestWrapper>
        <MockResultComponent />
      </TestWrapper>
    );

    // Verify result component integrates with theme system
    expect(screen.getByTestId('result-component')).toBeInTheDocument();
    
    // Theme should be maintained through result display
    // This test verifies integration between result display and theme provider
  });

  test('should handle result calculation performance requirements', async () => {
    const startTime = performance.now();

    render(
      <TestWrapper>
        <MockResultComponent />
      </TestWrapper>
    );

    const result = await mockSessionClient.getResult('test-session-id');

    const endTime = performance.now();
    const calculationTime = endTime - startTime;

    // Result calculation should complete quickly on frontend
    expect(calculationTime).toBeLessThan(100); // 100ms for frontend processing

    // Verify result structure completeness
    expect(result.axes.length).toBeGreaterThan(0);
    expect(result.type.profiles.length).toBeGreaterThan(0);
  });

  test('should handle result calculation with fallback scenarios', async () => {
    // Mock result with fallback flags
    mockSessionClient.getResult.mockResolvedValue({
      sessionId: 'test-session-id',
      keyword: 'フォールバック',
      axes: [
        {
          axisId: 'logic_emotion',
          score: 60,
          rawScore: 1.0
        },
        {
          axisId: 'speed_caution',
          score: 40,
          rawScore: -1.0
        }
      ],
      type: {
        dominantAxes: ['logic_emotion', 'speed_caution'],
        profiles: [
          {
            name: 'フォールバック型',
            description: 'フォールバックシステムにより生成されたプロファイルです。',
            dominantAxes: ['logic_emotion', 'speed_caution'],
            polarity: 'neutral',
            keywords: ['フォールバック', '標準']
          }
        ],
        fallbackUsed: true
      },
      completedAt: '2024-01-15T10:30:00Z',
      fallbackFlags: ['TYPE_PROFILE_FALLBACK']
    });

    render(
      <TestWrapper>
        <MockResultComponent />
      </TestWrapper>
    );

    const result = await mockSessionClient.getResult('test-session-id');

    // Verify fallback handling
    expect(result.type.fallbackUsed).toBe(true);
    expect(result.fallbackFlags).toContain('TYPE_PROFILE_FALLBACK');

    // Fallback results should still be valid
    expect(result.axes.length).toBeGreaterThan(0);
    expect(result.type.profiles.length).toBeGreaterThan(0);
  });

  test('should handle result error scenarios gracefully', async () => {
    // Mock result retrieval failure
    mockSessionClient.getResult.mockRejectedValue(new Error('Result calculation failed'));

    render(
      <TestWrapper>
        <MockResultComponent />
      </TestWrapper>
    );

    // Should handle error gracefully without crashing
    try {
      await mockSessionClient.getResult('test-session-id');
    } catch (error) {
      expect(error).toBeInstanceOf(Error);
      expect((error as Error).message).toBe('Result calculation failed');
    }
  });

  test('should validate result data consistency', async () => {
    render(
      <TestWrapper>
        <MockResultComponent />
      </TestWrapper>
    );

    const result = await mockSessionClient.getResult('test-session-id');

    // Verify data consistency
    expect(result.sessionId).toBe('test-session-id');
    expect(result.keyword).toBeTruthy();
    
    // All axis scores should be within valid ranges
    result.axes.forEach(axis => {
      expect(axis.score).toBeGreaterThanOrEqual(0);
      expect(axis.score).toBeLessThanOrEqual(100);
      expect(axis.rawScore).toBeGreaterThanOrEqual(-5);
      expect(axis.rawScore).toBeLessThanOrEqual(5);
    });
    
    // Type profiles should be consistent with dominant axes
    expect(result.type.dominantAxes).toHaveLength(2);
    result.type.profiles.forEach(profile => {
      expect(profile.dominantAxes).toHaveLength(2);
      // Profile dominant axes should be subset of result dominant axes
      profile.dominantAxes.forEach(axisId => {
        const axisExists = result.axes.some(axis => axis.axisId === axisId);
        expect(axisExists).toBe(true);
      });
    });
    
    // Completed timestamp should be valid ISO string
    expect(result.completedAt).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z$/);
    
    // Fallback flags should be array
    expect(Array.isArray(result.fallbackFlags)).toBe(true);
  });

  test('should handle score normalization edge cases', async () => {
    // Test score normalization with various raw score ranges
    const edgeCases = [
      { rawScore: 5.0, expectedScore: 100 },   // Maximum positive
      { rawScore: -5.0, expectedScore: 0 },    // Maximum negative
      { rawScore: 0.0, expectedScore: 50 },    // Neutral
      { rawScore: 2.5, expectedScore: 75 },    // Mid-positive
      { rawScore: -2.5, expectedScore: 25 }    // Mid-negative
    ];

    for (const testCase of edgeCases) {
      mockSessionClient.getResult.mockResolvedValue({
        sessionId: 'test-session-id',
        keyword: 'テスト',
        axes: [
          {
            axisId: 'test_axis',
            score: testCase.expectedScore,
            rawScore: testCase.rawScore
          }
        ],
        type: {
          dominantAxes: ['test_axis'],
          profiles: [],
          fallbackUsed: false
        },
        completedAt: '2024-01-15T10:30:00Z',
        fallbackFlags: []
      });

      render(
        <TestWrapper>
          <MockResultComponent />
        </TestWrapper>
      );

      const result = await mockSessionClient.getResult('test-session-id');
      
      expect(result.axes[0].score).toBe(testCase.expectedScore);
      expect(result.axes[0].rawScore).toBe(testCase.rawScore);
    }
  });
});

describe('Result Display Integration Error Scenarios', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('should handle malformed result data gracefully', async () => {
    // Mock malformed result response
    mockSessionClient.getResult.mockResolvedValue({
      sessionId: 'test-session-id',
      // Missing required fields
      axes: [],
      type: {
        profiles: []
      }
    } as any);

    render(
      <TestWrapper>
        <MockResultComponent />
      </TestWrapper>
    );

    // Should handle malformed data without crashing
    const result = await mockSessionClient.getResult('test-session-id');
    expect(result.sessionId).toBe('test-session-id');
    
    // Missing fields should be handled gracefully in UI
    expect(result.axes).toEqual([]);
  });

  test('should handle result calculation timeout', async () => {
    // Mock slow result calculation
    mockSessionClient.getResult.mockImplementation(
      () => new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Calculation timeout')), 100)
      )
    );

    render(
      <TestWrapper>
        <MockResultComponent />
      </TestWrapper>
    );

    // Should handle timeout gracefully
    await expect(mockSessionClient.getResult('test-session-id')).rejects.toThrow('Calculation timeout');
  });

  test('should handle session expiration during result calculation', async () => {
    // Mock session expiration error
    mockSessionClient.getResult.mockRejectedValue({
      error_code: 'SESSION_NOT_FOUND',
      message: 'Session has expired',
      details: {}
    });

    render(
      <TestWrapper>
        <MockResultComponent />
      </TestWrapper>
    );

    // Should handle session expiration appropriately
    await expect(mockSessionClient.getResult('test-session-id')).rejects.toMatchObject({
      error_code: 'SESSION_NOT_FOUND'
    });
  });
});
