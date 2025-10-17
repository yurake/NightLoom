
import { render } from '@testing-library/react';
import { axe } from 'jest-axe';
import Scene from '../../app/(play)/components/Scene';
import ChoiceOptions from '../../app/(play)/components/ChoiceOptions';
import ResultScreen from '../../app/(play)/components/ResultScreen';
import AxesScores from '../../app/(play)/components/AxesScores';
import TypeCard from '../../app/(play)/components/TypeCard';
import SkipLinks from '../../app/components/SkipLinks';
import { SessionProvider } from '../../app/state/SessionContext';
import { ThemeProvider } from '../../app/theme/ThemeProvider';
import { mockResult2Axes } from '../../app/types/result';

jest.setTimeout(20000);

// テスト用のモックデータ
const mockChoices = [
  { id: 'choice_0_1', text: '選択肢A', weights: { adventure: 1, social: 0, creativity: 0, focus: 0 } },
  { id: 'choice_0_2', text: '選択肢B', weights: { adventure: 0, social: 1, creativity: 0, focus: 0 } },
  { id: 'choice_0_3', text: '選択肢C', weights: { adventure: 0, social: 0, creativity: 1, focus: 0 } },
  { id: 'choice_0_4', text: '選択肢D', weights: { adventure: 0, social: 0, creativity: 0, focus: 1 } }
];

// モックAPIクライアント
const mockApiClient = {
  getResult: jest.fn().mockResolvedValue(mockResult2Axes)
};

// テスト用のWrapper コンポーネント
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <SessionProvider>
    <ThemeProvider>
      {children}
    </ThemeProvider>
  </SessionProvider>
);

describe('WCAG 2.1 AA Compliance Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Level A Compliance', () => {
    it('should pass WCAG 2.1 Level A requirements for main page', async () => {
      const { container } = render(
        <TestWrapper>
          <main id="main-content" tabIndex={-1}>
            <SkipLinks />
            <h1>NightLoom 診断</h1>
            <section>
              <h2>キーワード選択</h2>
              <p>診断を開始するためのキーワードを選択してください</p>
            </section>
          </main>
        </TestWrapper>
      );

      const results = await axe(container, {
        tags: ['wcag2a'],
        rules: {
          // Level A 必須ルール
          'aria-allowed-attr': { enabled: true },
          'aria-required-attr': { enabled: true },
          'aria-required-children': { enabled: true },
          'aria-required-parent': { enabled: true },
          'aria-roles': { enabled: true },
          'aria-valid-attr-value': { enabled: true },
          'aria-valid-attr': { enabled: true },
          'button-name': { enabled: true },
          'bypass': { enabled: true },
          'color-contrast': { enabled: true },
          'document-title': { enabled: true },
          'duplicate-id': { enabled: true },
          'form-field-multiple-labels': { enabled: true },
          'frame-title': { enabled: true },
          'html-has-lang': { enabled: true },
          'html-lang-valid': { enabled: true },
          'image-alt': { enabled: true },
          'input-image-alt': { enabled: true },
          'label': { enabled: true },
          'landmark-one-main': { enabled: true },
          'link-name': { enabled: true },
          'list': { enabled: true },
          'listitem': { enabled: true },
          'marquee': { enabled: true },
          'meta-refresh': { enabled: true },
          'object-alt': { enabled: true },
          'role-img-alt': { enabled: true },
          'td-headers-attr': { enabled: true },
          'th-has-data-cells': { enabled: true },
          'valid-lang': { enabled: true },
          'video-caption': { enabled: true }
        }
      });
      expect(results).toHaveNoViolations();
    });

    it('should pass WCAG 2.1 Level A requirements for choice selection', async () => {
      const { container } = render(
        <TestWrapper>
          <main id="main-content" tabIndex={-1}>
            <h1>シーン選択</h1>
            <ChoiceOptions 
              choices={mockChoices}
              onChoiceSelect={jest.fn()}
              sceneIndex={0}
            />
          </main>
        </TestWrapper>
      );

      const results = await axe(container, {
        tags: ['wcag2a']
      });
      expect(results).toHaveNoViolations();
    });

    it('should pass WCAG 2.1 Level A requirements for result display', async () => {
      const { container } = render(
        <TestWrapper>
          <main id="main-content" tabIndex={-1}>
            <h1>診断結果</h1>
            <TypeCard typeResult={mockResult2Axes.type} />
            <AxesScores axesScores={mockResult2Axes.axes} />
          </main>
        </TestWrapper>
      );

      const results = await axe(container, {
        tags: ['wcag2a']
      });
      expect(results).toHaveNoViolations();
    });
  });

  describe('Level AA Compliance', () => {
    it('should pass WCAG 2.1 Level AA requirements for main interface', async () => {
      const { container } = render(
        <TestWrapper>
          <div>
            <SkipLinks />
            <main id="main-content" tabIndex={-1}>
              <header>
                <h1>NightLoom パーソナリティ診断</h1>
                <nav aria-label="メインナビゲーション">
                  <ul>
                    <li><a href="/">ホーム</a></li>
                    <li><a href="/about">このサイトについて</a></li>
                  </ul>
                </nav>
              </header>
              
              <section aria-labelledby="diagnosis-heading">
                <h2 id="diagnosis-heading">診断開始</h2>
                <ChoiceOptions 
                  choices={mockChoices}
                  onChoiceSelect={jest.fn()}
                  sceneIndex={0}
                />
              </section>
            </main>
          </div>
        </TestWrapper>
      );

      const results = await axe(container, {
        tags: ['wcag2aa'],
        rules: {
          // Level AA 必須ルール
          'color-contrast': { enabled: true },
          'focus-order-semantics': { enabled: true },
          'heading-order': { enabled: true },
          'label-title-only': { enabled: true },
          'landmark-banner-is-top-level': { enabled: true },
          'landmark-contentinfo-is-top-level': { enabled: true },
          'landmark-main-is-top-level': { enabled: true },
          'landmark-no-duplicate-banner': { enabled: true },
          'landmark-no-duplicate-contentinfo': { enabled: true },
          'landmark-unique': { enabled: true },
          'meta-viewport': { enabled: true },
          'page-has-heading-one': { enabled: true },
          'region': { enabled: true },
          'scope-attr-valid': { enabled: true },
          'server-side-image-map': { enabled: true }
        }
      });
      expect(results).toHaveNoViolations();
    });

    it('should pass WCAG 2.1 Level AA color contrast requirements', async () => {
      const { container } = render(
        <TestWrapper>
          <div className="bg-white p-8">
            {/* 高コントラストのテキスト要素 */}
            <h1 className="text-gray-900 text-2xl font-bold mb-4">
              メインタイトル (4.5:1 以上)
            </h1>
            <p className="text-gray-800 text-base mb-4">
              通常テキスト - 十分なコントラスト比を確保
            </p>
            <p className="text-gray-700 text-sm mb-4">
              小さなテキスト - 4.5:1 以上のコントラスト
            </p>
            
            {/* ボタン要素 */}
            <button className="bg-blue-600 text-white px-4 py-2 rounded mr-2">
              プライマリボタン
            </button>
            <button className="bg-gray-600 text-white px-4 py-2 rounded mr-2">
              セカンダリボタン
            </button>
            
            {/* リンク要素 */}
            <a href="#" className="text-blue-700 underline">
              リンクテキスト (4.5:1 以上)
            </a>
            
            {/* フォーム要素 */}
            <div className="mt-4">
              <label htmlFor="test-input" className="block text-gray-900 font-medium mb-2">
                入力フィールド
              </label>
              <input 
                id="test-input"
                type="text" 
                className="border border-gray-400 px-3 py-2 text-gray-900"
                placeholder="プレースホルダーテキスト"
              />
            </div>
          </div>
        </TestWrapper>
      );

      const results = await axe(container, {
        rules: {
          'color-contrast': { enabled: true }
        }
      });
      expect(results).toHaveNoViolations();
    });

    it('should pass WCAG 2.1 Level AA keyboard navigation requirements', async () => {
      const { container } = render(
        <TestWrapper>
          <main id="main-content" tabIndex={-1}>
            <h1>キーボードナビゲーションテスト</h1>
            
            {/* フォーカス可能な要素の順序テスト */}
            <nav aria-label="テストナビゲーション">
              <a href="#section1">セクション1へ</a>
              <a href="#section2">セクション2へ</a>
            </nav>
            
            <section id="section1">
              <h2>セクション1</h2>
              <button type="button">ボタン1</button>
              <button type="button">ボタン2</button>
            </section>
            
            <section id="section2">
              <h2>セクション2</h2>
              <input type="text" placeholder="入力フィールド" />
              <label htmlFor="section2-select" className="sr-only">
                セクション2の選択肢
              </label>
              <select id="section2-select">
                <option>選択肢1</option>
                <option>選択肢2</option>
              </select>
            </section>
            
            <ChoiceOptions 
              choices={mockChoices}
              onChoiceSelect={jest.fn()}
              sceneIndex={0}
            />
          </main>
        </TestWrapper>
      );

      const results = await axe(container, {
        rules: {
          'focus-order-semantics': { enabled: true },
          'tabindex': { enabled: true }
        }
      });
      expect(results).toHaveNoViolations();
    });
  });

  describe('WCAG 2.1 Specific Requirements', () => {
    it('should pass WCAG 2.1 AA requirements for form elements', async () => {
      const { container } = render(
        <TestWrapper>
          <form>
            <fieldset>
              <legend>診断設定</legend>
              
              <div className="mb-4">
                <label htmlFor="username">ユーザー名</label>
                <input 
                  id="username"
                  type="text" 
                  required
                  aria-describedby="username-help"
                />
                <div id="username-help">
                  3文字以上で入力してください
                </div>
              </div>
              
              <div className="mb-4">
                <label htmlFor="age-group">年齢層</label>
                <select id="age-group" required>
                  <option value="">選択してください</option>
                  <option value="teens">10代</option>
                  <option value="twenties">20代</option>
                  <option value="thirties">30代</option>
                </select>
              </div>
              
              <fieldset>
                <legend>診断タイプ</legend>
                <div>
                  <input type="radio" id="basic" name="type" value="basic" />
                  <label htmlFor="basic">基本診断</label>
                </div>
                <div>
                  <input type="radio" id="advanced" name="type" value="advanced" />
                  <label htmlFor="advanced">詳細診断</label>
                </div>
              </fieldset>
              
              <div>
                <input type="checkbox" id="newsletter" />
                <label htmlFor="newsletter">ニュースレターを受け取る</label>
              </div>
              
              <button type="submit">診断開始</button>
            </fieldset>
          </form>
        </TestWrapper>
      );

      const results = await axe(container, {
        tags: ['wcag21aa'],
        rules: {
          'label': { enabled: true },
          'label-title-only': { enabled: true },
          'form-field-multiple-labels': { enabled: true },
          'button-name': { enabled: true }
        }
      });
      expect(results).toHaveNoViolations();
    });
it('should pass WCAG 2.1 AA requirements for data tables', async () => {
  const { container } = render(
    <TestWrapper>
      <main>
        <h1>診断結果サマリー</h1>
        <table>
          <caption>パーソナリティ軸スコア一覧</caption>
          <thead>
            <tr>
              <th scope="col">軸名</th>
              <th scope="col">スコア</th>
              <th scope="col">レベル</th>
              <th scope="col">説明</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th scope="row">冒険性</th>
              <td>75.5</td>
              <td>高</td>
              <td>新しい体験への開放性</td>
            </tr>
            <tr>
              <th scope="row">社交性</th>
              <td>42.3</td>
              <td>中</td>
              <td>他者との関わり度合い</td>
            </tr>
          </tbody>
        </table>
      </main>
    </TestWrapper>
  );

  const results = await axe(container, {
    rules: {
      'table-duplicate-name': { enabled: true },
      'table-fake-caption': { enabled: true },
      'td-has-header': { enabled: true },
      'td-headers-attr': { enabled: true },
      'th-has-data-cells': { enabled: true },
      'scope-attr-valid': { enabled: true }
    }
  });
  expect(results).toHaveNoViolations();
});

it('should pass WCAG 2.1 AA requirements for images and media', async () => {
  const { container } = render(
    <TestWrapper>
      <main>
        <h1>メディア要素テスト</h1>
        
        {/* 装飾的画像 */}
        <img src="/decoration.png" alt="" role="presentation" />
        
        {/* 意味のある画像 */}
        <img
          src="/chart.png"
          alt="診断結果チャート: 冒険性75点、社交性42点を示すグラフ"
        />
        
        {/* SVGアイコン */}
        <svg role="img" aria-label="成功アイコン" width="24" height="24">
          <circle cx="12" cy="12" r="10" fill="green" />
          <path d="M9 12l2 2 4-4" stroke="white" strokeWidth="2" />
        </svg>
        
        {/* ビデオ（字幕付き） */}
        <video controls>
          <source src="/intro.mp4" type="video/mp4" />
          <track kind="captions" src="/captions.vtt" srcLang="ja" label="日本語字幕" />
          動画を再生するには、対応ブラウザをご使用ください。
        </video>
      </main>
    </TestWrapper>
  );

  const results = await axe(container, {
    rules: {
      'image-alt': { enabled: true },
      'role-img-alt': { enabled: true },
      'svg-img-alt': { enabled: true },
      'video-caption': { enabled: true }
    }
  });
  expect(results).toHaveNoViolations();
}, 20000);
});

describe('Complete Application Flow', () => {
it('should pass full WCAG 2.1 AA compliance for complete diagnosis flow', async () => {
  const { container } = render(
    <TestWrapper>
      <div>
        <SkipLinks />
        
        <header role="banner">
          <h1>NightLoom パーソナリティ診断システム</h1>
          <nav aria-label="メインナビゲーション">
            <ul>
              <li><a href="/">ホーム</a></li>
              <li><a href="/about">概要</a></li>
            </ul>
          </nav>
        </header>
        
        <main id="main-content" tabIndex={-1}>
          <section aria-labelledby="diagnosis-section">
            <h2 id="diagnosis-section">診断セクション</h2>
            
            <div className="keyword-selection">
              <h3>キーワード選択</h3>
              <p>診断のベースとなるキーワードを選択してください</p>
              
              <div role="radiogroup" aria-labelledby="keyword-group-label">
                <h4 id="keyword-group-label">提案キーワード</h4>
                <button role="radio" aria-checked="false">冒険</button>
                <button role="radio" aria-checked="false">平和</button>
                <button role="radio" aria-checked="false">創造</button>
              </div>
            </div>
            
            <div className="choice-selection">
              <h3>シーン選択</h3>
              <ChoiceOptions
                choices={mockChoices}
                onChoiceSelect={jest.fn()}
                sceneIndex={0}
              />
            </div>
          </section>
          
          <section aria-labelledby="results-section">
            <h2 id="results-section">診断結果</h2>
            <TypeCard typeResult={mockResult2Axes.type} />
            <AxesScores axesScores={mockResult2Axes.axes} />
          </section>
        </main>
        
        <footer role="contentinfo">
          <p>&copy; 2024 NightLoom. All rights reserved.</p>
        </footer>
      </div>
    </TestWrapper>
  );

  const results = await axe(container, {
    tags: ['wcag2a', 'wcag2aa', 'wcag21aa'],
    options: {
      runOnly: {
        type: 'tag',
        values: ['wcag2a', 'wcag2aa', 'wcag21aa']
      }
    }
  });
  expect(results).toHaveNoViolations();
}, 22000);
});
});
                
