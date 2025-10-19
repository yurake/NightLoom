/**
 * SkipLinks component for keyboard navigation accessibility
 * Provides quick navigation to main content sections
 */

'use client';

import React from 'react';

interface SkipLinksProps {
  className?: string;
}

export const SkipLinks: React.FC<SkipLinksProps> = ({ className = '' }) => {
  const handleMainContentSkip = (e: React.MouseEvent | React.KeyboardEvent) => {
    e.preventDefault();
    const mainContent = document.getElementById('main-content');
    if (mainContent) {
      mainContent.focus();
      mainContent.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const handleChoiceSkip = (e: React.MouseEvent | React.KeyboardEvent) => {
    e.preventDefault();
    const choiceOptions = document.getElementById('choice-options');
    if (choiceOptions) {
      const firstChoice = choiceOptions.querySelector('[role="radio"]') as HTMLElement;
      if (firstChoice) {
        firstChoice.focus();
        firstChoice.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  };

  const handleResultSkip = (e: React.MouseEvent | React.KeyboardEvent) => {
    e.preventDefault();
    const resultContent = document.getElementById('result-content');
    if (resultContent) {
      resultContent.focus();
      resultContent.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <nav
      className={`skip-links ${className}`}
      aria-label="スキップリンク"
    >
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        onClick={handleMainContentSkip}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            handleMainContentSkip(e);
          }
        }}
      >
        メインコンテンツへスキップ
      </a>
      
      <a
        href="#choice-options"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ml-2"
        onClick={handleChoiceSkip}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            handleChoiceSkip(e);
          }
        }}
      >
        選択肢へスキップ
      </a>

      <a
        href="#result-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ml-4"
        onClick={handleResultSkip}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            handleResultSkip(e);
          }
        }}
      >
        結果へスキップ
      </a>
    </nav>
  );
};

export default SkipLinks;
