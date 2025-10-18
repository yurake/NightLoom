/**
 * SkipLinks コンポーネントテスト
 * キーボードナビゲーション、フォーカス管理、アクセシビリティ対応のテスト
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { SkipLinks } from '../../app/components/SkipLinks';

// Mock window.scrollIntoView
Object.defineProperty(Element.prototype, 'scrollIntoView', {
  writable: true,
  value: jest.fn(),
});

// Mock element.focus
Object.defineProperty(HTMLElement.prototype, 'focus', {
  writable: true,
  value: jest.fn(),
});

describe('SkipLinks コンポーネント', () => {
  afterEach(() => {
    jest.clearAllMocks();
    // Clean up any created DOM elements
    document.body.innerHTML = '';
  });

  beforeEach(() => {
    // Create target elements for skip links
    const mainContent = document.createElement('main');
    mainContent.id = 'main-content';
    mainContent.setAttribute('tabindex', '-1');
    document.body.appendChild(mainContent);

    const choiceOptions = document.createElement('div');
    choiceOptions.id = 'choice-options';
    const radioButton = document.createElement('button');
    radioButton.setAttribute('role', 'radio');
    radioButton.setAttribute('tabindex', '0');
    choiceOptions.appendChild(radioButton);
    document.body.appendChild(choiceOptions);

    const resultContent = document.createElement('div');
    resultContent.id = 'result-content';
    resultContent.setAttribute('tabindex', '-1');
    document.body.appendChild(resultContent);
  });

  describe('レンダリングとアクセシビリティ', () => {
    it('正しくレンダリングされる', () => {
      render(<SkipLinks />);
      
      const skipNav = screen.getByRole('navigation', { name: 'スキップリンク' });
      expect(skipNav).toBeInTheDocument();
    });

    it('3つのスキップリンクが表示される', () => {
      render(<SkipLinks />);
      
      expect(screen.getByText('メインコンテンツへスキップ')).toBeInTheDocument();
      expect(screen.getByText('選択肢へスキップ')).toBeInTheDocument();
      expect(screen.getByText('結果へスキップ')).toBeInTheDocument();
    });

    it('適切なaria-labelが設定される', () => {
      render(<SkipLinks />);
      
      const navigation = screen.getByRole('navigation');
      expect(navigation).toHaveAttribute('aria-label', 'スキップリンク');
    });

    it('カスタムクラス名が適用される', () => {
      render(<SkipLinks className="custom-class" />);
      
      const skipLinks = screen.getByRole('navigation');
      expect(skipLinks).toHaveClass('skip-links', 'custom-class');
    });
  });

  describe('キーボードナビゲーション', () => {
    it('Tabキーでスキップリンクにフォーカスできる', () => {
      render(<SkipLinks />);
      
      const mainSkipLink = screen.getByText('メインコンテンツへスキップ');
      const choiceSkipLink = screen.getByText('選択肢へスキップ');
      const resultSkipLink = screen.getByText('結果へスキップ');

      // スキップリンクがフォーカス可能であることを確認
      expect(mainSkipLink).toHaveAttribute('href', '#main-content');
      expect(choiceSkipLink).toHaveAttribute('href', '#choice-options');
      expect(resultSkipLink).toHaveAttribute('href', '#result-content');
    });

    it('Enterキーでスキップリンクを実行できる', () => {
      render(<SkipLinks />);
      
      const mainSkipLink = screen.getByText('メインコンテンツへスキップ');
      
      fireEvent.keyDown(mainSkipLink, { key: 'Enter', code: 'Enter' });
      
      const mainContent = document.getElementById('main-content');
      expect(mainContent?.focus).toHaveBeenCalled();
    });

    it('Spaceキーでスキップリンクを実行できる', () => {
      render(<SkipLinks />);
      
      const choiceSkipLink = screen.getByText('選択肢へスキップ');
      
      fireEvent.keyDown(choiceSkipLink, { key: ' ', code: 'Space' });
      
      const choiceOptions = document.getElementById('choice-options');
      const firstChoice = choiceOptions?.querySelector('[role="radio"]');
      expect((firstChoice as HTMLElement)?.focus).toHaveBeenCalled();
    });
  });

  describe('フォーカス管理', () => {
    it('メインコンテンツスキップでメインコンテンツにフォーカス', () => {
      render(<SkipLinks />);
      
      const mainSkipLink = screen.getByText('メインコンテンツへスキップ');
      fireEvent.click(mainSkipLink);
      
      const mainContent = document.getElementById('main-content');
      expect(mainContent?.focus).toHaveBeenCalled();
      expect(mainContent?.scrollIntoView).toHaveBeenCalledWith({
        behavior: 'smooth',
        block: 'start'
      });
    });

    it('選択肢スキップで最初の選択肢にフォーカス', () => {
      render(<SkipLinks />);
      
      const choiceSkipLink = screen.getByText('選択肢へスキップ');
      fireEvent.click(choiceSkipLink);
      
      const choiceOptions = document.getElementById('choice-options');
      const firstChoice = choiceOptions?.querySelector('[role="radio"]');
      expect((firstChoice as HTMLElement)?.focus).toHaveBeenCalled();
      expect(firstChoice?.scrollIntoView).toHaveBeenCalledWith({
        behavior: 'smooth',
        block: 'center'
      });
    });

    it('結果スキップで結果コンテンツにフォーカス', () => {
      render(<SkipLinks />);
      
      const resultSkipLink = screen.getByText('結果へスキップ');
      fireEvent.click(resultSkipLink);
      
      const resultContent = document.getElementById('result-content');
      expect(resultContent?.focus).toHaveBeenCalled();
      expect(resultContent?.scrollIntoView).toHaveBeenCalledWith({
        behavior: 'smooth',
        block: 'start'
      });
    });
  });

  describe('エラーハンドリング', () => {
    it('対象要素が存在しない場合でもエラーが発生しない', () => {
      // Remove target elements
      document.getElementById('main-content')?.remove();
      document.getElementById('choice-options')?.remove();
      document.getElementById('result-content')?.remove();

      render(<SkipLinks />);
      
      const mainSkipLink = screen.getByText('メインコンテンツへスキップ');
      
      expect(() => {
        fireEvent.click(mainSkipLink);
      }).not.toThrow();
    });

    it('選択肢要素内にradioボタンが存在しない場合でもエラーが発生しない', () => {
      // Remove radio button from choice options
      const choiceOptions = document.getElementById('choice-options');
      if (choiceOptions) {
        choiceOptions.innerHTML = '';
      }

      render(<SkipLinks />);
      
      const choiceSkipLink = screen.getByText('選択肢へスキップ');
      
      expect(() => {
        fireEvent.click(choiceSkipLink);
      }).not.toThrow();
    });
  });

  describe('イベント処理', () => {
    it('クリック時にデフォルトのリンク動作を防ぐ', () => {
      render(<SkipLinks />);
      
      const mainSkipLink = screen.getByText('メインコンテンツへスキップ');
      const event = new MouseEvent('click', { bubbles: true, cancelable: true });
      
      Object.defineProperty(event, 'preventDefault', {
        value: jest.fn(),
        writable: true
      });
      
      mainSkipLink.dispatchEvent(event);
      
      expect(event.preventDefault).toHaveBeenCalled();
    });

    it('各スキップリンクが独立して機能する', () => {
      render(<SkipLinks />);
      
      // Test all three skip links
      const links = [
        { text: 'メインコンテンツへスキップ', targetId: 'main-content' },
        { text: '選択肢へスキップ', targetId: 'choice-options' },
        { text: '結果へスキップ', targetId: 'result-content' }
      ];
      
      links.forEach(({ text, targetId }) => {
        const skipLink = screen.getByText(text);
        fireEvent.click(skipLink);
        
        if (targetId === 'choice-options') {
          const choiceOptions = document.getElementById(targetId);
          const firstChoice = choiceOptions?.querySelector('[role="radio"]');
          expect((firstChoice as HTMLElement)?.focus).toHaveBeenCalled();
        } else {
          const targetElement = document.getElementById(targetId);
          expect(targetElement?.focus).toHaveBeenCalled();
        }
      });
    });
  });

  describe('CSS スタイリング', () => {
    it('フォーカス時に適切なスタイルクラスが適用される', () => {
      render(<SkipLinks />);
      
      const skipLinks = screen.getAllByRole('link');
      
      skipLinks.forEach(link => {
        expect(link).toHaveClass('sr-only');
        expect(link).toHaveClass('focus:not-sr-only');
        expect(link).toHaveClass('focus:absolute');
        expect(link).toHaveClass('focus:top-4');
        expect(link).toHaveClass('focus:left-4');
        expect(link).toHaveClass('focus:z-50');
      });
    });

    it('適切なフォーカスリングスタイルが適用される', () => {
      render(<SkipLinks />);
      
      const skipLinks = screen.getAllByRole('link');
      
      skipLinks.forEach(link => {
        expect(link).toHaveClass('focus:outline-none');
        expect(link).toHaveClass('focus:ring-2');
        expect(link).toHaveClass('focus:ring-blue-500');
        expect(link).toHaveClass('focus:ring-offset-2');
      });
    });
  });

  describe('スクリーンリーダー対応', () => {
    it('スクリーンリーダー専用クラスが設定される', () => {
      render(<SkipLinks />);
      
      const skipLinks = screen.getAllByRole('link');
      
      skipLinks.forEach(link => {
        expect(link).toHaveClass('sr-only');
      });
    });

    it('適切な説明テキストが設定される', () => {
      render(<SkipLinks />);
      
      expect(screen.getByText('メインコンテンツへスキップ')).toBeInTheDocument();
      expect(screen.getByText('選択肢へスキップ')).toBeInTheDocument();
      expect(screen.getByText('結果へスキップ')).toBeInTheDocument();
    });

    it('ナビゲーション要素にaria-labelが設定される', () => {
      render(<SkipLinks />);
      
      const navigation = screen.getByRole('navigation');
      expect(navigation).toHaveAttribute('aria-label', 'スキップリンク');
    });
  });
});
