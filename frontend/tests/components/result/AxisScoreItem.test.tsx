/**
 * AxisScoreItem コンポーネントテスト
 *
 * TDD原則: 実装前にテスト作成、RED状態確認後に実装開始
 */

import { render, screen, waitFor } from '@testing-library/react';
import { AxisScoreItem, type AxisScore } from '@/components/AxisScoreItem';

describe('AxisScoreItem コンポーネント', () => {
  const mockAxisScore: AxisScore = {
    id: 'axis_1',
    name: '論理性',
    description: '論理的思考と感情的判断のバランス',
    direction: '論理的 ⟷ 感情的',
    score: 75.5,
    rawScore: 2.1
  };

  it('軸名が正しく表示される', () => {
    render(<AxisScoreItem axisScore={mockAxisScore} />);
    
    expect(screen.getByText('論理性')).toBeInTheDocument();
  });

  it('方向性が正しく表示される', () => {
    render(<AxisScoreItem axisScore={mockAxisScore} />);
    
    expect(screen.getByText('論理的 ⟷ 感情的')).toBeInTheDocument();
  });

  it('スコア数値が小数第1位まで表示される', () => {
    render(<AxisScoreItem axisScore={mockAxisScore} />);
    
    expect(screen.getByText('75.5')).toBeInTheDocument();
  });

  it('プログレスバーが表示される', () => {
    render(<AxisScoreItem axisScore={mockAxisScore} />);
    
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
  });

  it('アクセシビリティ属性が設定される', () => {
    render(<AxisScoreItem axisScore={mockAxisScore} />);
    
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-label', expect.stringContaining('論理性'));
    expect(progressBar).toHaveAttribute('aria-valuenow', '75.5');
    expect(progressBar).toHaveAttribute('aria-valuemin', '0');
    expect(progressBar).toHaveAttribute('aria-valuemax', '100');
  });

  it('スコアバーアニメーションが実行される', async () => {
    render(<AxisScoreItem axisScore={mockAxisScore} />);
    
    const progressBar = screen.getByRole('progressbar');
    const progressFill = progressBar.querySelector('[data-testid="progress-fill"]');
    
    // 初期状態（アニメーション前）
    expect(progressFill).toHaveStyle('width: 0%');
    
    // アニメーション後（100ms遅延 + α）
    await waitFor(() => {
      expect(progressFill).toHaveStyle('width: 75.5%');
    }, { timeout: 2000 });
  });

  it('レスポンシブレイアウトのクラスが適用される', () => {
    const { container } = render(<AxisScoreItem axisScore={mockAxisScore} />);
    const axisItem = container.firstChild as HTMLElement;
    
    expect(axisItem).toHaveClass('p-4');
    expect(axisItem).toHaveClass('rounded-lg');
  });

  describe('エッジケース', () => {
    it('0スコアでも正しく表示される', () => {
      const zeroScoreAxis: AxisScore = {
        ...mockAxisScore,
        score: 0,
        rawScore: -5.0
      };
      
      render(<AxisScoreItem axisScore={zeroScoreAxis} />);
      expect(screen.getByText('0.0')).toBeInTheDocument();
    });

    it('100スコアでも正しく表示される', () => {
      const maxScoreAxis: AxisScore = {
        ...mockAxisScore,
        score: 100,
        rawScore: 5.0
      };
      
      render(<AxisScoreItem axisScore={maxScoreAxis} />);
      expect(screen.getByText('100.0')).toBeInTheDocument();
    });

    it('長い軸名でも適切に表示される', () => {
      const longNameAxis: AxisScore = {
        ...mockAxisScore,
        name: '非常に長い軸名テスト',
        direction: '非常に長い軸の方向性 ⟷ 反対側の非常に長い方向性'
      };
      
      render(<AxisScoreItem axisScore={longNameAxis} />);
      expect(screen.getByText('非常に長い軸名テスト')).toBeInTheDocument();
    });

    it('prefers-reduced-motionが設定されている場合はアニメーションが無効化される', () => {
      // CSS media queryのモック
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query === '(prefers-reduced-motion: reduce)',
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn(),
        })),
      });

      render(<AxisScoreItem axisScore={mockAxisScore} />);
      const progressBar = screen.getByRole('progressbar');
      const progressFill = progressBar.querySelector('[data-testid="progress-fill"]');
      
      // reduced-motionの場合、即座に最終値が設定される
      expect(progressFill).toHaveStyle('width: 75.5%');
    });
  });
});
