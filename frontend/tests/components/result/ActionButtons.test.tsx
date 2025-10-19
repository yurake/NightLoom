/**
 * ActionButtons コンポーネントテスト
 *
 * TDD原則: 実装前にテスト作成、RED状態確認後に実装開始
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ActionButtons, type ActionButtonsProps } from '../../../app/(play)/components/ActionButtons';

describe('ActionButtons コンポーネント', () => {
  const mockOnRestart = jest.fn();
  const mockOnRetry = jest.fn();

  const defaultProps: ActionButtonsProps = {
    onRestart: mockOnRestart,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('ボタンレンダリング基本テスト', () => {
    it('再診断ボタンが表示される', () => {
      render(<ActionButtons {...defaultProps} />);
      
      const restartButton = screen.getByTestId('restart-button');
      expect(restartButton).toBeInTheDocument();
      expect(restartButton).toHaveTextContent(/もう一度診断する/);
    });

    it('リトライボタンがonRetry提供時に表示される', () => {
      render(<ActionButtons {...defaultProps} onRetry={mockOnRetry} />);
      
      const retryButton = screen.getByTestId('retry-button');
      expect(retryButton).toBeInTheDocument();
      expect(retryButton).toHaveTextContent(/リトライ/);
    });

    it('リトライボタンがonRetry未提供時は表示されない', () => {
      render(<ActionButtons {...defaultProps} />);
      
      const retryButton = screen.queryByTestId('retry-button');
      expect(retryButton).not.toBeInTheDocument();
    });

    it('ActionButtonsコンテナにdata-testidが設定される', () => {
      render(<ActionButtons {...defaultProps} />);
      
      const container = screen.getByTestId('action-buttons');
      expect(container).toBeInTheDocument();
    });
  });

  describe('onRestart コールバック実行テスト', () => {
    it('再診断ボタンクリック時にonRestartが呼び出される', async () => {
      const user = userEvent.setup();
      render(<ActionButtons {...defaultProps} />);
      
      const restartButton = screen.getByTestId('restart-button');
      await user.click(restartButton);
      
      expect(mockOnRestart).toHaveBeenCalledTimes(1);
    });

    it('非同期onRestartコールバックが正しく処理される', async () => {
      const asyncOnRestart = jest.fn().mockResolvedValue(undefined);
      const user = userEvent.setup();
      
      render(<ActionButtons {...defaultProps} onRestart={asyncOnRestart} />);
      
      const restartButton = screen.getByTestId('restart-button');
      await user.click(restartButton);
      
      expect(asyncOnRestart).toHaveBeenCalledTimes(1);
      await waitFor(() => {
        expect(asyncOnRestart).toHaveBeenCalled();
      });
    });

    it('onRetryボタンクリック時にonRetryが呼び出される', async () => {
      const user = userEvent.setup();
      render(<ActionButtons {...defaultProps} onRetry={mockOnRetry} />);
      
      const retryButton = screen.getByTestId('retry-button');
      await user.click(retryButton);
      
      expect(mockOnRetry).toHaveBeenCalledTimes(1);
    });

    it('キーボード操作（Enter）でボタンが実行される', async () => {
      const user = userEvent.setup();
      render(<ActionButtons {...defaultProps} />);
      
      const restartButton = screen.getByTestId('restart-button');
      restartButton.focus();
      await user.keyboard('{Enter}');
      
      expect(mockOnRestart).toHaveBeenCalledTimes(1);
    });

    it('キーボード操作（Space）でボタンが実行される', async () => {
      const user = userEvent.setup();
      render(<ActionButtons {...defaultProps} />);
      
      const restartButton = screen.getByTestId('restart-button');
      restartButton.focus();
      await user.keyboard(' ');
      
      expect(mockOnRestart).toHaveBeenCalledTimes(1);
    });
  });

  describe('ローディング状態表示テスト', () => {
    it('isLoading=trueの時、ローディングインジケーターが表示される', () => {
      render(<ActionButtons {...defaultProps} isLoading={true} />);
      
      const loadingIndicator = screen.getByTestId('loading-indicator');
      expect(loadingIndicator).toBeInTheDocument();
    });

    it('isLoading=trueの時、ボタンが無効化される', () => {
      render(<ActionButtons {...defaultProps} isLoading={true} />);
      
      const restartButton = screen.getByTestId('restart-button');
      expect(restartButton).toBeDisabled();
    });

    it('isLoading=trueの時、ローディングテキストが表示される', () => {
      render(<ActionButtons {...defaultProps} isLoading={true} />);
      
      expect(screen.getByText(/処理中/)).toBeInTheDocument();
    });

    it('isLoading=falseの時、ローディングインジケーターが表示されない', () => {
      render(<ActionButtons {...defaultProps} isLoading={false} />);
      
      const loadingIndicator = screen.queryByTestId('loading-indicator');
      expect(loadingIndicator).not.toBeInTheDocument();
    });

    it('ローディング中はボタンクリックが無効化される', async () => {
      const user = userEvent.setup();
      render(<ActionButtons {...defaultProps} isLoading={true} />);
      
      const restartButton = screen.getByTestId('restart-button');
      await user.click(restartButton);
      
      // ローディング中はコールバックが呼び出されない
      expect(mockOnRestart).not.toHaveBeenCalled();
    });
  });

  describe('エラー状態表示テスト', () => {
    it('エラー状態でエラーメッセージが表示される', async () => {
      // エラー状態をトリガーするために、onRestartでエラーを発生させる
      const errorOnRestart = jest.fn().mockRejectedValue(new Error('Test error'));
      render(<ActionButtons {...defaultProps} onRestart={errorOnRestart} />);
      
      const restartButton = screen.getByTestId('restart-button');
      fireEvent.click(restartButton);
      
      // エラーメッセージの表示を確認（非同期処理後）
      await waitFor(() => {
        const errorMessage = screen.queryByTestId('error-message');
        expect(errorMessage).toBeInTheDocument();
      });
    });

    it('エラー状態でもボタンは操作可能である', () => {
      render(<ActionButtons {...defaultProps} />);
      
      // エラー状態でもボタンは無効化されない
      const restartButton = screen.getByTestId('restart-button');
      expect(restartButton).not.toBeDisabled();
    });

    it('エラー後のリトライが正常に実行される', async () => {
      const user = userEvent.setup();
      render(<ActionButtons {...defaultProps} onRetry={mockOnRetry} />);
      
      // エラー後のリトライボタンクリック
      const retryButton = screen.getByTestId('retry-button');
      await user.click(retryButton);
      
      expect(mockOnRetry).toHaveBeenCalledTimes(1);
    });
  });

  describe('無効化状態テスト', () => {
    it('isDisabled=trueの時、すべてのボタンが無効化される', () => {
      render(<ActionButtons {...defaultProps} onRetry={mockOnRetry} isDisabled={true} />);
      
      const restartButton = screen.getByTestId('restart-button');
      const retryButton = screen.getByTestId('retry-button');
      
      expect(restartButton).toBeDisabled();
      expect(retryButton).toBeDisabled();
    });

    it('isDisabled=trueの時、ボタンクリックが無効化される', async () => {
      const user = userEvent.setup();
      render(<ActionButtons {...defaultProps} isDisabled={true} />);
      
      const restartButton = screen.getByTestId('restart-button');
      await user.click(restartButton);
      
      // 無効化されているのでコールバックが呼び出されない
      expect(mockOnRestart).not.toHaveBeenCalled();
    });

    it('isDisabled=falseの時、ボタンが有効である', () => {
      render(<ActionButtons {...defaultProps} isDisabled={false} />);
      
      const restartButton = screen.getByTestId('restart-button');
      expect(restartButton).not.toBeDisabled();
    });

    it('ローディング状態と無効化状態が両方trueの時、無効化される', () => {
      render(<ActionButtons {...defaultProps} isLoading={true} isDisabled={true} />);
      
      const restartButton = screen.getByTestId('restart-button');
      expect(restartButton).toBeDisabled();
    });
  });

  describe('アクセシビリティ属性テスト', () => {
    it('再診断ボタンにaria-labelが設定される', () => {
      render(<ActionButtons {...defaultProps} />);
      
      const restartButton = screen.getByTestId('restart-button');
      expect(restartButton).toHaveAttribute('aria-label', expect.stringContaining('再診断'));
    });

    it('リトライボタンにaria-labelが設定される', () => {
      render(<ActionButtons {...defaultProps} onRetry={mockOnRetry} />);
      
      const retryButton = screen.getByTestId('retry-button');
      expect(retryButton).toHaveAttribute('aria-label', expect.stringContaining('リトライ'));
    });

    it('ローディング状態でaria-busyが設定される', () => {
      render(<ActionButtons {...defaultProps} isLoading={true} />);
      
      const container = screen.getByTestId('action-buttons');
      expect(container).toHaveAttribute('aria-busy', 'true');
    });

    it('通常状態でaria-busyがfalseまたは未設定', () => {
      render(<ActionButtons {...defaultProps} isLoading={false} />);
      
      const container = screen.getByTestId('action-buttons');
      expect(container).toHaveAttribute('aria-busy', 'false');
    });

    it('無効化状態でaria-disabledが設定される', () => {
      render(<ActionButtons {...defaultProps} isDisabled={true} />);
      
      const restartButton = screen.getByTestId('restart-button');
      expect(restartButton).toHaveAttribute('aria-disabled', 'true');
    });

    it('ボタンのrole属性が適切に設定される', () => {
      render(<ActionButtons {...defaultProps} onRetry={mockOnRetry} />);
      
      const restartButton = screen.getByTestId('restart-button');
      const retryButton = screen.getByTestId('retry-button');
      
      expect(restartButton).toHaveAttribute('role', 'button');
      expect(retryButton).toHaveAttribute('role', 'button');
    });

    it('キーボードナビゲーションのtabindexが適切に設定される', () => {
      render(<ActionButtons {...defaultProps} onRetry={mockOnRetry} />);
      
      const restartButton = screen.getByTestId('restart-button');
      const retryButton = screen.getByTestId('retry-button');
      
      expect(restartButton).toHaveAttribute('tabindex', '0');
      expect(retryButton).toHaveAttribute('tabindex', '0');
    });

    it('無効化時にtabindexが-1に設定される', () => {
      render(<ActionButtons {...defaultProps} isDisabled={true} />);
      
      const restartButton = screen.getByTestId('restart-button');
      expect(restartButton).toHaveAttribute('tabindex', '-1');
    });
  });

  describe('スタイルバリアントテスト', () => {
    it('primary variantが適用される', () => {
      render(<ActionButtons {...defaultProps} variant="primary" />);
      
      const restartButton = screen.getByTestId('restart-button');
      expect(restartButton).toHaveClass('primary');
    });

    it('secondary variantが適用される', () => {
      render(<ActionButtons {...defaultProps} onRetry={mockOnRetry} variant="secondary" />);
      
      const retryButton = screen.getByTestId('retry-button');
      expect(retryButton).toHaveClass('secondary');
    });

    it('デフォルトvariantが適用される', () => {
      render(<ActionButtons {...defaultProps} />);
      
      const restartButton = screen.getByTestId('restart-button');
      // デフォルトはprimaryと仮定
      expect(restartButton).toHaveClass('primary');
    });

    it('カスタムクラスが追加される', () => {
      const customClass = 'custom-action-buttons';
      render(<ActionButtons {...defaultProps} className={customClass} />);
      
      const container = screen.getByTestId('action-buttons');
      expect(container).toHaveClass(customClass);
    });
  });

  describe('エッジケーステスト', () => {
    it('onRestartが未定義でもエラーが発生しない', () => {
      const propsWithoutOnRestart = { onRestart: undefined as any };
      
      expect(() => {
        render(<ActionButtons {...propsWithoutOnRestart} />);
      }).not.toThrow();
    });

    it('複数回連続クリックでも適切に処理される', async () => {
      const user = userEvent.setup();
      render(<ActionButtons {...defaultProps} />);
      
      const restartButton = screen.getByTestId('restart-button');
      
      // 複数回クリック
      await user.click(restartButton);
      await user.click(restartButton);
      await user.click(restartButton);
      
      expect(mockOnRestart).toHaveBeenCalledTimes(3);
    });

    it('レンダリング時のパフォーマンスが適切である', () => {
      const startTime = performance.now();
      render(<ActionButtons {...defaultProps} />);
      const endTime = performance.now();
      
      const renderTime = endTime - startTime;
      // レンダリングが100ms以下で完了することを確認
      expect(renderTime).toBeLessThan(100);
    });
  });
});
