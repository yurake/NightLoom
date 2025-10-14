/**
 * AxesScores コンポーネントテスト
 *
 * TDD原則: 実装前にテスト作成、RED状態確認後に実装開始
 */

import { render, screen } from '@testing-library/react';
import { AxesScores } from '@/components/AxesScores';
import type { AxisScore } from '@/components/AxisScoreItem';

describe('AxesScores コンポーネント', () => {
  const mockAxesScores2Axes: AxisScore[] = [
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
  ];

  const mockAxesScores6Axes: AxisScore[] = [
    {
      id: 'axis_1',
      name: '探索性',
      description: '新しい経験への開放性',
      direction: '探索的 ⟷ 慎重的',
      score: 85.2,
      rawScore: 3.5
    },
    {
      id: 'axis_2',
      name: '計画性',
      description: '行動の計画と準備',
      direction: '計画的 ⟷ 直感的',
      score: 35.7,
      rawScore: -1.4
    },
    {
      id: 'axis_3',
      name: '協調性',
      description: 'チームワークと協力',
      direction: '協調的 ⟷ 独立的',
      score: 62.1,
      rawScore: 1.2
    },
    {
      id: 'axis_4',
      name: '分析性',
      description: '情報の分析と検証',
      direction: '分析的 ⟷ 直感的',
      score: 48.9,
      rawScore: -0.1
    },
    {
      id: 'axis_5',
      name: '表現性',
      description: '自己表現と創造性',
      direction: '表現的 ⟷ 内省的',
      score: 71.4,
      rawScore: 1.9
    },
    {
      id: 'axis_6',
      name: '安定性',
      description: 'リスク回避と安定志向',
      direction: '安定的 ⟷ 冒険的',
      score: 28.3,
      rawScore: -2.2
    }
  ];

  it('2軸のスコアが正しく表示される', () => {
    render(<AxesScores axesScores={mockAxesScores2Axes} />);
    
    expect(screen.getByText('論理性')).toBeInTheDocument();
    expect(screen.getByText('社交性')).toBeInTheDocument();
  });

  it('6軸のスコアが正しく表示される', () => {
    render(<AxesScores axesScores={mockAxesScores6Axes} />);
    
    expect(screen.getByText('探索性')).toBeInTheDocument();
    expect(screen.getByText('計画性')).toBeInTheDocument();
    expect(screen.getByText('協調性')).toBeInTheDocument();
    expect(screen.getByText('分析性')).toBeInTheDocument();
    expect(screen.getByText('表現性')).toBeInTheDocument();
    expect(screen.getByText('安定性')).toBeInTheDocument();
  });

  it('AxisScoreItemコンポーネントが軸数分レンダリングされる', () => {
    render(<AxesScores axesScores={mockAxesScores2Axes} />);
    
    // プログレスバー（AxisScoreItem内）が2つ表示される
    const progressBars = screen.getAllByRole('progressbar');
    expect(progressBars).toHaveLength(2);
  });

  it('6軸の場合、AxisScoreItemコンポーネントが6つレンダリングされる', () => {
    render(<AxesScores axesScores={mockAxesScores6Axes} />);
    
    // プログレスバー（AxisScoreItem内）が6つ表示される
    const progressBars = screen.getAllByRole('progressbar');
    expect(progressBars).toHaveLength(6);
  });

  it('レスポンシブグリッドレイアウトのクラスが適用される', () => {
    const { container } = render(<AxesScores axesScores={mockAxesScores2Axes} />);
    const gridContainer = container.querySelector('div[class*="grid"]') as HTMLElement;
    
    expect(gridContainer).toHaveClass('grid');
    expect(gridContainer).toHaveClass('gap-4');
  });

  it('軸数に応じて適切なグリッドレイアウトが適用される', () => {
    // 2軸の場合
    const { container: container2 } = render(<AxesScores axesScores={mockAxesScores2Axes} />);
    const gridContainer2 = container2.querySelector('div[class*="grid"]') as HTMLElement;
    expect(gridContainer2).toHaveClass('grid-cols-1');
    
    // 6軸の場合
    const { container: container6 } = render(<AxesScores axesScores={mockAxesScores6Axes} />);
    const gridContainer6 = container6.querySelector('div[class*="grid"]') as HTMLElement;
    expect(gridContainer6).toHaveClass('md:grid-cols-2');
  });

  it('セクションタイトルが表示される', () => {
    render(<AxesScores axesScores={mockAxesScores2Axes} />);
    
    expect(screen.getByText(/軸スコア/)).toBeInTheDocument();
  });

  describe('エッジケース', () => {
    it('空配列の場合でもエラーが発生しない', () => {
      render(<AxesScores axesScores={[]} />);
      
      expect(screen.getByRole('heading', { name: /軸スコア/ })).toBeInTheDocument();
      const progressBars = screen.queryAllByRole('progressbar');
      expect(progressBars).toHaveLength(0);
    });

    it('1軸の場合でも適切に表示される', () => {
      const singleAxis: AxisScore[] = [mockAxesScores2Axes[0]];
      
      render(<AxesScores axesScores={singleAxis} />);
      
      expect(screen.getByText('論理性')).toBeInTheDocument();
      const progressBars = screen.getAllByRole('progressbar');
      expect(progressBars).toHaveLength(1);
    });

    it('7軸以上の場合でも適切に表示される', () => {
      const manyAxes: AxisScore[] = [
        ...mockAxesScores6Axes,
        {
          id: 'axis_7',
          name: '革新性',
          description: '新しいアイデアの創造',
          direction: '革新的 ⟷ 保守的',
          score: 60.0,
          rawScore: 1.0
        }
      ];
      
      render(<AxesScores axesScores={manyAxes} />);
      
      const progressBars = screen.getAllByRole('progressbar');
      expect(progressBars).toHaveLength(7);
    });

    it('アクセシビリティ構造が適切に設定される', () => {
      render(<AxesScores axesScores={mockAxesScores2Axes} />);
      
      // セクション要素があること
      const section = screen.getByRole('region');
      expect(section).toBeInTheDocument();
      
      // セクションのaria-labelが設定されていること
      expect(section).toHaveAttribute('aria-label', expect.stringContaining('軸スコア'));
    });
  });
});
