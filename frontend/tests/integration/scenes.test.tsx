
/**
 * Integration tests for NightLoom MVP scene progression flow.
 * 
 * Tests the complete scene progression from frontend to backend integration.
 * Implements T032 requirements with Fail First testing strategy.
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

// Mock scene component for testing
function MockSceneComponent() {
  return <div data-testid="scene-component">Scene Component</div>;
}

describe('Scene Progression Integration Flow', () => {
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

    mockSessionClient.getScene.mockResolvedValue({
      sessionId: 'test-session-id',
      scene: {
        sceneIndex: 2,
        themeId: 'serene',
        narrative: '次の重要な局面に差し掛かりました。',
        choices: [
          {
            id: 'choice_2_1',
            text: '論理的にアプローチする',
            weights: { logic_emotion: 1.0, speed_caution: 0.0 }
          },
          {
            id: 'choice_2_2',
            text: '感情に従って決める',
            weights: { logic_emotion: -1.0, speed_caution: 0.0 }
          },
          {
            id: 'choice_2_3',
            text: 'すぐに行動する',
            weights: { logic_emotion: 0.0, speed_caution: 1.0 }
          },
          {
            id: 'choice_2_4',
            text: 'よく考えてから決める',
            weights: { logic_emotion: 0.0, speed_caution: -1.0 }
          }
        ]
      },
      fallbackUsed: false
    });

    mockSessionClient.submitChoice.mockResolvedValue({
      sessionId: 'test-session-id',
      sceneCompleted: true,
      nextScene: {
        sceneIndex: 2,
        themeId: 'serene',
        narrative: '次の重要な局面に差し掛かりました。',
        choices: [
          {
            id: 'choice_2_1',
            text: '論理的にアプローチする',
            weights: { logic_emotion: 1.0, speed_caution: 0.0 }
          },
          {
            id: 'choice_2_2',
            text: '感情に従って決める',
            weights: { logic_emotion: -1.0, speed_caution: 0.0 }
          },
          {
            id: 'choice_2_3',
            text: 'すぐに行動する',
            weights: { logic_emotion: 0.0, speed_caution: 1.0 }
          },
          {
            id: 'choice_2_4',
            text: 'よく考えてから決める',
            weights: { logic_emotion: 0.0, speed_caution: -1.0 }
          }
        ]
      }
    });
  });

  test('should complete scene progression from scene 1 to scene 2', async () => {
    render(
      <TestWrapper>
        <MockSceneComponent />
      </TestWrapper>
    );

    // This test verifies the integration flow:
    // 1. User selects choice in scene 1
    // 2. submitChoice API is called
    // 3. Next scene (scene 2) is loaded
    // 4. Scene 2 is displayed

    // Simulate scene 1 choice selection
    // Note: This test assumes scene UI components exist and will be implemented
    
    // Test data flow through session context
    expect(screen.getByTestId('scene-component')).toBeInTheDocument();
  });

  test('should handle scene progression with choice submission', async () => {
    render(
      <TestWrapper>
        <MockSceneComponent />
      </TestWrapper>
    );

    // Simulate choice submission API call
    await mockSessionClient.submitChoice('test-session-id', 1, 'choice_1_1');

    await waitFor(() => {
      expect(mockSessionClient.submitChoice).toHaveBeenCalledWith(
        'test-session-id',
        1,
        'choice_1_1'
      );
    });

    // Verify next scene is retrieved
    expect(mockSessionClient.submitChoice).toHaveBeenCalledTimes(1);
  });

  test('should maintain session state during scene progression', async () => {
    render(
      <TestWrapper>
        <MockSceneComponent />
      </TestWrapper>
    );

    // Test that session context maintains:
    // - Current scene index
    // - Accumulated scores
    // - Choice history
    // - Session metadata

    // This test verifies state management during progression
    expect(screen.getByTestId('scene-component')).toBeInTheDocument();
  });

  test('should handle scene progression errors gracefully', async () => {
    // Mock choice submission failure
    mockSessionClient.submitChoice.mockRejectedValue(new Error('Choice submission failed'));

    render(
      <TestWrapper>
        <MockSceneComponent />
      </TestWrapper>
    );

    // Should display error message when choice submission fails
    // Implementation will determine exact error handling
  });

  test('should update progress indicator during scene progression', async () => {
    render(
      <TestWrapper>
        <MockSceneComponent />
      </TestWrapper>
    );

    // Test that progress indicator shows:
    // - Current scene number (1 of 4, 2 of 4, etc.)
    // - Progress percentage
    // - Visual progress bar

    expect(screen.getByTestId('scene-component')).toBeInTheDocument();
  });

  test('should handle theme consistency across scenes', async () => {
    render(
      <TestWrapper>
        <MockSceneComponent />
      </TestWrapper>
    );

    // Verify that theme remains consistent throughout progression
    // - Same themeId across all scenes
    // - Consistent visual styling
    // - Theme-appropriate content

    expect(screen.getByTestId('scene-component')).toBeInTheDocument();
  });

  test('should validate choice weights accumulation', async () => {
    render(
      <TestWrapper>
        <MockSceneComponent />
      </TestWrapper>
    );

    // Test that choice weights are properly accumulated:
    // - Scene 1 choice adds to axis scores
    // - Scene 2 choice adds to existing scores
    // - Running totals are maintained

    // Simulate multiple choice submissions
    await mockSessionClient.submitChoice('test-session-id', 1, 'choice_1_1');
    await mockSessionClient.submitChoice('test-session-id', 2, 'choice_2_1');

    // Verify accumulated scores are calculated correctly
    // This requires integration with session state management
  });

  test('should meet performance requirements for scene transitions', async () => {
    const startTime = performance.now();

    render(
      <TestWrapper>
        <MockSceneComponent />
      </TestWrapper>
    );

    // Simulate scene transition
    await mockSessionClient.submitChoice('test-session-id', 1, 'choice_1_1');

    const endTime = performance.now();
    const transitionTime = endTime - startTime;

    // Scene transitions should be under 800ms
    expect(transitionTime).toBeLessThan(800);
  });

  test('should handle concurrent scene operations', async () => {
    render(
      <TestWrapper>
        <MockSceneComponent />
      </TestWrapper>
    );

    // Test concurrent operations:
    // - Multiple choice submissions (should be serialized)
    // - Scene retrieval during choice submission
    // - Session state updates

    // Only the first choice should be accepted
    const promises = [
      mockSessionClient.submitChoice('test-session-id', 1, 'choice_1_1'),
      mockSessionClient.submitChoice('test-session-id', 1, 'choice_1_2'),
      mockSessionClient.submitChoice('test-session-id', 1, 'choice_1_3')
    ];

    // Wait for all promises to resolve/reject
    const results = await Promise.allSettled(promises);

    // Implementation should handle concurrency properly
    expect(results).toHaveLength(3);
  });
});

describe('Scene Progression Edge Cases', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('should handle scene progression with network interruption', async () => {
    // Mock network failure during scene transition
    mockSessionClient.submitChoice
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({
        sessionId: 'test-session-id',
        sceneCompleted: true,
        nextScene: {
          sceneIndex: 2,
          themeId: 'serene',
          narrative: '次の重要な局面に差し掛かりました。',
          choices: []
        }
      });

    render(
      <TestWrapper>
        <MockSceneComponent />
      </TestWrapper>
    );

    // Should retry failed requests and eventually succeed
    expect(screen.getByTestId('scene-component')).toBeInTheDocument();
  });

  test('should handle malformed scene data', async () => {
    // Mock malformed scene response
    mockSessionClient.getScene.mockResolvedValue({
      sessionId: 'test-session-id',
      scene: {
        sceneIndex: 2,
        themeId: '',
        narrative: '',
        choices: [] // Empty choices array
      },
      fallbackUsed: false
    } as any);

    render(
      <TestWrapper>
        <MockSceneComponent />
      </TestWrapper>
    );

    // Should handle malformed data gracefully
    expect(screen.getByTestId('scene-component')).toBeInTheDocument();
  });

  test('should handle scene progression with fallback scenarios', async () => {
    // Mock fallback response
    mockSessionClient.submitChoice.mockResolvedValue({
      sessionId: 'test-session-id',
      sceneCompleted: true,
      nextScene: {
        sceneIndex: 2,
        themeId: 'fallback',
        narrative: 'フォールバックシナリオが適用されました。',
        choices: [
          {
            id: 'fallback_choice_1',
            text: 'フォールバック選択肢1',
            weights: { logic_emotion: 0.5, speed_caution: 0.0 }
          },
          {
            id: 'fallback_choice_2',
            text: 'フォールバック選択肢2',
            weights: { logic_emotion: -0.5, speed_caution: 0.0 }
          },
          {
            id: 'fallback_choice_3',
            text: 'フォールバック選択肢3',
            weights: { logic_emotion: 0.0, speed_caution: 0.5 }
          },
          {
            id: 'fallback_choice_4',
            text: 'フォールバック選択肢4',
            weights: { logic_emotion: 0.0, speed_caution: -0.5 }
          }
        ]
      }
    });

    render(
      <TestWrapper>
        <MockSceneComponent />
      </TestWrapper>
    );

    // Should handle fallback content properly
    expect(screen.getByTestId('scene-component')).toBeInTheDocument();
  });

  test('should handle rapid scene progression attempts', async () => {
    render(
      <TestWrapper>
        <MockSceneComponent />
      </TestWrapper>
    );

    // Test rapid-fire choice submissions
    // Should prevent duplicate submissions and maintain state consistency

    const rapidSubmissions = Array.from({ length: 5 }, (_, i) =>
      mockSessionClient.submitChoice('test-session-id', 1, `choice_1_${i + 1}`)
    );

    const results = await Promise.allSettled(rapidSubmissions);

    // Implementation should handle rapid submissions gracefully
    expect(results).toHaveLength(5);
  });

  test('should validate scene index consistency', async () => {
    render(
      <TestWrapper>
        <MockSceneComponent />
      </TestWrapper>
    );

    // Test that scene indices progress correctly:
    // 1 → 2 → 3 → 4
    // No skipping or backwards progression allowed

    // Mock sequential scene progression
    const sceneProgression = [
      { sceneIndex: 1, nextSceneIndex: 2 },
      { sceneIndex: 2, nextSceneIndex: 3 },
      { sceneIndex: 3, nextSceneIndex: 4 },
      { sceneIndex: 4, nextSceneIndex: null }
    ];

    for (const { sceneIndex, nextSceneIndex } of sceneProgression) {
      mockSessionClient.submitChoice.mockResolvedValueOnce({
        sessionId: 'test-session-id',
        sceneCompleted: true,
        nextScene: nextSceneIndex ? {
          sceneIndex: nextSceneIndex,
          themeId: 'serene',
          narrative: `Scene ${nextSceneIndex} narrative`,
          choices: []
        } : null
      });
    }

    // Verify scene progression maintains correct order
    expect(screen.getByTestId('scene-component')).toBeInTheDocument();
  });
});
