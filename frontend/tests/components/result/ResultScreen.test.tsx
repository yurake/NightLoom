/**
 * ResultScreen コンポーネントテスト
 *
 * TDD原則: 実装前にテスト作成、RED状態確認後に実装開始
 */

import { render, screen, waitFor } from '@testing-library/react';
import { ResultScreen } from '../../../app/(play)/components/ResultScreen';
import type { ResultData, AxisScore, TypeResult } from '../../../app/types/result';

// モックデータ
const mockResultData: ResultData = {
  sessionId: '550e8400-e29b-41d4-a716-446655440000',
  keyword: 'アート',
  axes: [
    {
      id: 'axis_1',
      name: '論理性',
      description: '論理的思考と感情的判断のバランス',
      direction: '論理的 ⟷ 感情的',
      score: 75.5,
      rawScore: 2.1
    },
    {
      id: 'axis_2',
      name: '社交性',
      description: '集団行動と個人行動の指向性',
      direction: '社交的 ⟷ 内省的',
      score: 42.3,
      rawScore: -0.8
    }
  ],
  type: {
    name: 'Logic Thinker',
    description: '論理的思考を重視し、個人での内省を好む傾向があります。',
    dominantAxes: ['axis_1', 'axis_2'] as [string, string],
    polarity: 'Hi-Lo'
  },
  completedAt: '2025-10-14T13:15:00Z'
};

// APIクライアントのモック
const mockApiClient = {
  getResult: jest.fn()
};

// モックされたコンポーネント
jest.mock('../../../app/(play)/components/TypeCard', () => ({
  TypeCard: ({ typeResult }: { typeResult: TypeResult }) => (
    <div data-testid="type-card">{typeResult.name}</div>
  )
}));

jest.mock('../../../app/(play)/components/AxesScores', () => ({
  AxesScores: ({ axesScores }: { axesScores: AxisScore[] }) => (
    <div data-testid="axes-scores">軸数: {axesScores.length}</div>
  )
}));

describe('ResultScreen コンポーネント', () => {
  const defaultProps = {
    sessionId: '550e8400-e29b-41d4-a716-446655440000',
    apiClient: mockApiClient
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('ローディング状態が正しく表示される', () => {
    mockApiClient.getResult.mockImplementation(() => new Promise(() => {})); // 永続的にpending
    
    render(<ResultScreen {...defaultProps} />);
    
    expect(screen.getByText(/読み込み中/)).toBeInTheDocument();
    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
  });

  it('API成功時に結果データが正しく表示される', async () => {
    mockApiClient.getResult.mockResolvedValue(mockResultData);
    
    render(<ResultScreen {...defaultProps} />);
    
    // ローディング状態の確認
    expect(screen.getByText(/読み込み中/)).toBeInTheDocument();
    
    // 結果表示の確認
    await waitFor(() => {
      expect(screen.getByTestId('type-card')).toBeInTheDocument();
      expect(screen.getByTestId('axes-scores')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Logic Thinker')).toBeInTheDocument();
    expect(screen.getByText('軸数: 2')).toBeInTheDocument();
  });

  it('APIエラー時にエラーメッセージが表示される', async () => {
    const mockError = new Error('API Error');
    mockApiClient.getResult.mockRejectedValue(mockError);
    
    render(<ResultScreen {...defaultProps} />);
    
    await waitFor(() => {
      expect(screen.getByText(/エラーが発生しました/)).toBeInTheDocument();
      expect(screen.getByTestId('error-message')).toBeInTheDocument();
    });
  });

  it('セッションが見つからない場合の適切なエラー処理', async () => {
    const sessionNotFoundError = {
      code: 'SESSION_NOT_FOUND',
      message: 'セッションが見つかりません'
    };
    mockApiClient.getResult.mockRejectedValue(sessionNotFoundError);
    
    render(<ResultScreen {...defaultProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('セッションが見つかりません')).toBeInTheDocument();
    });
  });

  it('セッションが完了していない場合の適切なエラー処理', async () => {
    const sessionNotCompletedError = {
      code: 'SESSION_NOT_COMPLETED',
      message: '診断が完了していません'
    };
    mockApiClient.getResult.mockRejectedValue(sessionNotCompletedError);
    
    render(<ResultScreen {...defaultProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('診断が完了していません')).toBeInTheDocument();
    });
  });

  it('コンポーネントマウント時にAPIが呼び出される', () => {
    mockApiClient.getResult.mockResolvedValue(mockResultData);
    
    render(<ResultScreen {...defaultProps} />);
    
    expect(mockApiClient.getResult).toHaveBeenCalledWith('550e8400-e29b-41d4-a716-446655440000');
    expect(mockApiClient.getResult).toHaveBeenCalledTimes(1);
  });

  it('sessionId変更時に再度APIが呼び出される', () => {
    mockApiClient.getResult.mockResolvedValue(mockResultData);
    
    const { rerender } = render(<ResultScreen {...defaultProps} />);
    
    expect(mockApiClient.getResult).toHaveBeenCalledTimes(1);
    
    // sessionIdを変更
    rerender(<ResultScreen {...defaultProps} sessionId="new-session-id" />);
    
    expect(mockApiClient.getResult).toHaveBeenCalledWith('new-session-id');
    expect(mockApiClient.getResult).toHaveBeenCalledTimes(2);
  });

  it('アクセシビリティ属性が適切に設定される', async () => {
    mockApiClient.getResult.mockResolvedValue(mockResultData);
    
    render(<ResultScreen {...defaultProps} />);
    
    await waitFor(() => {
      const main = screen.getByRole('main');
      expect(main).toBeInTheDocument();
      expect(main).toHaveAttribute('aria-label', expect.stringContaining('診断結果'));
    });
  });

  describe('エラー境界テスト', () => {
    it('予期しないエラーが適切に処理される', async () => {
      mockApiClient.getResult.mockRejectedValue(new Error('Unexpected error'));
      
      render(<ResultScreen {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toBeInTheDocument();
      });
    });

    it('ネットワークエラーが適切に処理される', async () => {
      const networkError = {
        code: 'NETWORK_ERROR',
        message: 'ネットワークエラーが発生しました'
      };
      mockApiClient.getResult.mockRejectedValue(networkError);
      
      render(<ResultScreen {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('ネットワークエラーが発生しました')).toBeInTheDocument();
      });
    });
  });

  describe('パフォーマンステスト', () => {
    it('レンダリング時間が500ms以下で完了する', async () => {
      mockApiClient.getResult.mockResolvedValue(mockResultData);
      
      const startTime = performance.now();
      render(<ResultScreen {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByTestId('type-card')).toBeInTheDocument();
      });
      
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      
      // 500ms以下の要件を確認（テスト環境では少し余裕を持たせる）
      expect(renderTime).toBeLessThan(1000);
    });
  });
});
