/**
 * TypeCard コンポーネントテスト
 *
 * TDD原則: 実装前にテスト作成、RED状態確認後に実装開始
 */

import { render, screen } from '@testing-library/react';
import { TypeCard } from '../../../app/(play)/components/TypeCard';
import { type TypeResult } from '../../../app/types/result';

describe('TypeCard コンポーネント', () => {
  const mockTypeResult: TypeResult = {
    name: 'Logic Thinker',
    description: '論理的思考を重視し、個人での内省を好む傾向があります。',
    dominantAxes: ['axis_1', 'axis_2'] as [string, string],
    polarity: 'Hi-Lo'
  };

  it('タイプ名が正しく表示される', () => {
    render(<TypeCard typeResult={mockTypeResult} />);
    
    expect(screen.getByText('Logic Thinker')).toBeInTheDocument();
  });

  it('タイプ説明が正しく表示される', () => {
    render(<TypeCard typeResult={mockTypeResult} />);
    
    expect(screen.getByText('論理的思考を重視し、個人での内省を好む傾向があります。')).toBeInTheDocument();
  });

  it('極性バッジが正しく表示される', () => {
    render(<TypeCard typeResult={mockTypeResult} />);
    
    expect(screen.getByText('Hi-Lo')).toBeInTheDocument();
  });

  it('主軸情報が表示される', () => {
    render(<TypeCard typeResult={mockTypeResult} />);
    
    // 主軸数が表示されることを確認
    expect(screen.getByText(/主軸/)).toBeInTheDocument();
  });

  it('レスポンシブレイアウトのクラスが適用される', () => {
    const { container } = render(<TypeCard typeResult={mockTypeResult} />);
    const typeCard = container.firstChild as HTMLElement;
    
    // Tailwind CSS のレスポンシブクラスが適用されることを確認
    expect(typeCard).toHaveClass('p-4');
    expect(typeCard).toHaveClass('rounded-lg');
  });

  it('グラデーション背景が適用される', () => {
    const { container } = render(<TypeCard typeResult={mockTypeResult} />);
    const typeCard = container.firstChild as HTMLElement;
    
    expect(typeCard).toHaveClass('bg-gradient-to-br');
  });

  it('アクセシビリティ属性が設定される', () => {
    render(<TypeCard typeResult={mockTypeResult} />);
    
    const typeCard = screen.getByRole('article');
    expect(typeCard).toHaveAttribute('aria-label', expect.stringContaining('Logic Thinker'));
  });

  describe('エッジケース', () => {
    it('長いタイプ名でも適切に表示される', () => {
      const longNameType: TypeResult = {
        ...mockTypeResult,
        name: 'Very Long Type Name'
      };
      
      render(<TypeCard typeResult={longNameType} />);
      expect(screen.getByText('Very Long Type Name')).toBeInTheDocument();
    });

    it('長い説明文でも適切に表示される', () => {
      const longDescriptionType: TypeResult = {
        ...mockTypeResult,
        description: 'これは非常に長い説明文です。50文字を超える場合でも適切に表示されることを確認します。このテストは重要です。'
      };
      
      render(<TypeCard typeResult={longDescriptionType} />);
      expect(screen.getByText(/これは非常に長い説明文です/)).toBeInTheDocument();
    });

    it('異なる極性タイプでも正しく表示される', () => {
      const hiHiType: TypeResult = {
        ...mockTypeResult,
        polarity: 'Hi-Hi'
      };
      
      render(<TypeCard typeResult={hiHiType} />);
      expect(screen.getByText('Hi-Hi')).toBeInTheDocument();
    });
  });
});
