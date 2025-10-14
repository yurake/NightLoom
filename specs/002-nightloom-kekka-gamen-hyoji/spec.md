# Feature Specification: NightLoom結果画面表示機能

**Feature Branch**: `002-nightloom-kekka-gamen-hyoji`  
**Created**: 2025-10-14  
**Status**: Draft  
**Input**: User description: "NightLoomの結果画面表示機能 - ユーザーの診断結果（軸スコア、タイプ分類）を視覚的に表示する機能"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 診断結果の基本表示 (Priority: P1)

ユーザーが4シーンの選択を完了した後、自分のタイプ分類と軸スコアを即座に確認できる。

**Why this priority**: 診断体験の最も重要なゴールとして、ユーザーが自分の結果を理解できることが必須である。

**Independent Test**: シーン4完了後に結果画面にアクセスし、タイプ名・説明・軸スコアが全て表示されることで独立して価値を提供する。

**Acceptance Scenarios**:

1. **Given** セッション状態が`RESULT`、**When** 結果画面にアクセス、**Then** タイプ名、説明、キーワードが表示される
2. **Given** 正規化されたスコアデータ、**When** 画面読み込み、**Then** 2〜6軸のスコアが0〜100の範囲で表示される
3. **Given** モバイルデバイス（360px幅）、**When** 結果画面表示、**Then** レスポンシブレイアウトで適切に表示される

---

### User Story 2 - スコア可視化とアニメーション (Priority: P2)

各評価軸のスコアがプログレスバーでアニメーション付きで可視化され、ユーザーが直感的に理解できる。

**Why this priority**: スコアの数値だけでなく視覚的な表現により、ユーザーの理解度と満足度を向上させる。

**Independent Test**: 結果画面読み込み時にスコアバーが0%から実際の値まで1秒でアニメーションすることで独立して価値を提供する。

**Acceptance Scenarios**:

1. **Given** 軸スコアデータ、**When** 結果画面読み込み、**Then** プログレスバーが0%から実スコアまで1秒でアニメーション
2. **Given** 各軸の方向性情報、**When** スコア表示、**Then** 軸の方向性（例：「論理的 ⟷ 感情的」）が表示される
3. **Given** 軸の説明文、**When** スコア項目表示、**Then** 各軸の詳細説明が読みやすく配置される

---

### User Story 3 - 再診断機能 (Priority: P3)

ユーザーが結果を確認した後、簡単に新しい診断を開始できる。

**Why this priority**: ユーザーのリピート体験を促進し、プロダクトのエンゲージメントを向上させる。

**Independent Test**: 結果画面から「もう一度診断する」ボタンをクリックして初期画面に戻ることで独立して価値を提供する。

**Acceptance Scenarios**:

1. **Given** 結果画面表示中、**When** 「もう一度診断する」ボタンクリック、**Then** 初期画面（`/`）に遷移
2. **Given** 新規診断開始、**When** セッション作成、**Then** 前回の結果データは影響しない
3. **Given** 再診断実行、**When** セッション初期化、**Then** 現在セッション完全クリーンアップ・履歴置換でブラウザバック無効化

**Data Isolation Requirements**:
- 現在セッションのメモリクリア（sessionId、結果データ、テーマ状態）
- LocalStorage の一時データ削除
- 新セッションIDの自動生成と完全独立性保証

---

### Edge Cases

- スコア生成に失敗した場合の代替表示
- LLMタイプ生成失敗時のプリセットタイプ表示
- APIレスポンス遅延時のローディング状態
- 不正なセッションIDでのアクセス時のエラー処理
- 軸数が範囲外（2未満または6超過）の場合の表示調整

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムはセッション完了時に結果データ（タイプ分類、軸スコア）を取得して表示しなければならない
- **FR-002**: システムは2〜6軸の評価スコアを0〜100の正規化された値で表示しなければならない  
- **FR-003**: システムはタイプ名、説明、キーワード、極性情報を視覚的に表示しなければならない
- **FR-004**: システムはスコアバーアニメーションを1秒以内で実行しなければならない
- **FR-005**: システムは結果画面から初期画面への遷移機能を提供しなければならない
- **FR-006**: システムは360px以上の画面幅でレスポンシブに表示しなければならない
- **FR-007**: システムはAPI呼び出し中のローディング状態を適切に表示しなければならない
- **FR-008**: システムはエラー発生時に適切なエラーメッセージを表示しなければならない
- **FR-009**: システムは各軸の方向性表示（例：「論理的 ⟷ 感情的」）を含めなければならない

### Key Entities *(include if feature involves data)*

- **ResultData**: セッション結果の完全なデータセット（sessionId, keyword, axes, type, completedAt）
- **AxisScore**: 個別評価軸の情報（id, name, description, direction, score, rawScore）
- **TypeResult**: タイプ分類結果（name, description, dominantAxes, polarity）

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 結果画面のレンダリング時間が500ms以下で完了する
  - **計測開始**: API response受信時点
  - **計測終了**: First Contentful Paint完了時点
  - **計測方式**: `performance.mark()`使用
- **SC-002**: スコアバーアニメーションが正確に1秒で完了する
  - **判定方式**: `transitionend`イベント検出
  - **許容誤差**: ±50ms以内
  - **フォールバック**: 1200ms後にタイムアウト処理
- **SC-003**: 360px〜1920pxの画面幅で表示崩れなく動作する
- **SC-004**: 「もう一度診断する」機能の成功率が99%以上である
- **SC-005**: API エラー時のフォールバック表示が適切に機能する

### Technical Requirements

- **TR-001**: Next.js 14 + TypeScript + Tailwind CSS での実装
- **TR-002**: セッション内一時データ保持（永続化なし）
- **TR-003**: LLMフェイルオーバー対応（プリセットタイプ利用）
- **TR-004**: レスポンシブデザインでのPC/モバイル両対応

### Performance Requirements

- **PR-001**: 結果データ取得API（`GET /api/sessions/{sessionId}/result`）のレスポンス時間 < 1.2秒
- **PR-002**: 初回レンダリング時間 < 500ms
- **PR-003**: スコアバーアニメーション実行時間 = 1秒（±50ms）

### UI/UX Requirements

- **UX-001**: 全軸スコア、タイプ情報が一画面で確認可能
- **UX-002**: 視覚的なスコア表現（プログレスバー）による直感的理解
- **UX-003**: モバイル優先のレスポンシブレイアウト
- **UX-004**: アクセシビリティ対応（スクリーンリーダー、キーボードナビゲーション）

### Component Structure Requirements

- **CS-001**: ResultScreen（ルートコンポーネント）
- **CS-002**: TypeCard（タイプ情報表示）
- **CS-003**: AxesScores（軸スコア一覧）
- **CS-004**: AxisScoreItem（個別軸スコア）
- **CS-005**: ActionButtons（再診断等のアクション）
- **CS-006**: LoadingIndicator、ErrorMessage（状態表示）

### API Integration Requirements

- **API-001**: `GET /api/sessions/{sessionId}/result` エンドポイントとの統合
- **API-002**: エラーレスポンス（404, 400, 500）の適切な処理
- **API-003**: セッション状態（`RESULT`）の検証
- **API-004**: タイムアウト・ネットワークエラーのフォールバック

### Data Validation Requirements

- **DV-001**: スコア値が0〜100の範囲内であることの検証
- **DV-002**: 軸数が2〜6の範囲内であることの確認
- **DV-003**: 必須フィールド（sessionId, type.name, axes）の存在確認
- **DV-004**: 不正なデータ構造に対するエラーハンドリング

## Technical Implementation Details

### Component Architecture

#### ResultScreen（メインコンテナ）
```tsx
interface ResultScreenProps {
  sessionId: string;
}

const ResultScreen: React.FC<ResultScreenProps> = ({ sessionId }) => {
  const [result, setResult] = useState<ResultData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // API呼び出しとエラーハンドリング
  // 子コンポーネントへのデータ配信
};
```

#### TypeCard（タイプ情報表示）
- タイプ名（英語1〜2語、最大14文字）
- キーワード表示
- タイプ説明（50文字以内）
- 極性バッジ（Hi-Lo, Hi-Hi等）
- グラデーション背景による視覚的強調

#### AxesScores & AxisScoreItem（軸スコア表示）
- 2〜6軸の動的レンダリング
- スコアバーアニメーション（1秒、easing: ease-out）
  - 100ms遅延後に開始、バーと数値を同時実行
  - スコア数値は小数第1位表示（toFixed(1)）で統一
  - アニメーション中は最終値のみ表示（中間値なし）
- 軸方向性表示（例：「論理的 ⟷ 感情的」）
- rawScoreとnormalizedScoreの両方保持

### Data Flow & State Management

#### API Integration
- エンドポイント: `GET /api/sessions/{sessionId}/result`
- レスポンス時間要件: p95 ≤ 1.2s
- フェイルオーバー: LLM失敗時はプリセットタイプ使用
- エラーコード対応：
  - `SESSION_NOT_FOUND` (404)
  - `SESSION_NOT_COMPLETED` (400)
  - `TYPE_GEN_FAILED` (500)

#### Result Data Structure
```tsx
interface ResultData {
  sessionId: string;
  keyword: string;
  axes: AxisScore[];
  type: TypeResult;
  completedAt: string; // ISO 8601
}

interface AxisScore {
  id: string;           // axis_1, axis_2, etc.
  name: string;         // "論理性", "社交性"
  description: string;  // 軸の詳細説明
  direction: string;    // "論理的 ⟷ 感情的"
  score: number;        // 正規化後 0〜100
  rawScore: number;     // 正規化前 -5.0〜5.0
}

interface TypeResult {
  name: string;         // "Logical Thinker"
  description: string;  // 50文字以内の説明
  dominantAxes: string[]; // ["axis_1", "axis_2"]
  polarity: string;     // "Hi-Lo", "Mid-Mid"等
}
```

### Scoring Algorithm Integration

#### 正規化処理の理解
- キーワード修正値: -1.0 〜 1.0
- 4シーン重み累積: -4.0 〜 4.0
- 合計理論範囲: -5.0 〜 5.0
- 線形変換式: `(raw_score - (-5.0)) / (5.0 - (-5.0)) * 100`
- 全軸同値時: 一律50.0のNeutral扱い

#### タイプ分類ロジックの対応
- 主軸選定: 分散最大の2軸を使用
- 動的閾値: `max(5, 10 * sqrt(variance / 100))`
- 極性判定: High(≥60), Low(≤40), Mid(41-59)
- タイプ数: 基本4、条件により5-6に拡張

### Visual Design & Animation

#### Theme Integration（将来対応）
- テーマID: serene, adventure, focus, fallback
- CSS カスタムプロパティによる動的スタイル切替
- `themeId` をAPI レスポンスから取得（次回開発）

#### Animation Specifications
```css
.axis-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  transition: width 1s ease-out;
  width: 0%; /* 初期状態 */
}
```

#### Responsive Breakpoints（詳細仕様）
- **極小モバイル: 320px - 359px**
  - padding: 0.75rem、type-name: 1.25rem
- **標準モバイル: 360px - 767px**
  - padding: 1rem、type-name: 1.5rem（既存仕様）
- **タブレット: 768px - 1023px**
  - padding: 1.5rem、axis-score-item: grid 2列表示
- **デスクトップ: 1024px以上**
  - 最大幅: 800px（中央配置）、full padding適用

### Error Handling & Fallbacks

#### エラー状態の分類と具体的UI動作
1. **SESSION_NOT_FOUND (404)**:
   - メッセージ: "セッションが見つかりません"
   - 動作: 3秒後に初期画面へ自動リダイレクト
   - ボタン: "初期画面へ戻る"

2. **SESSION_NOT_COMPLETED (400)**:
   - メッセージ: "診断が完了していません"
   - 動作: 現在のシーン画面へリダイレクト
   - ボタン: "診断を続ける"

3. **TYPE_GEN_FAILED (500)**:
   - メッセージ: "結果を生成しています..."
   - 動作: プリセットタイプを透明的に使用（ユーザーには告知しない）
   - 表示: 通常の結果画面として表示

4. **ネットワークエラー/タイムアウト**:
   - メッセージ: "接続エラーが発生しました"
   - ボタン: "再試行" + "初期画面へ戻る"

#### フォールバック戦略
- API失敗: プリセットタイプ6種を使用（シームレス表示）
- スコア異常: デフォルト値（50）で表示継続
- 軸数範囲外: 2軸（Exploration, Convergence）で表示

### Performance Optimization

#### レンダリング最適化
- 初回レンダリング: < 500ms
- スコアバー遅延実行: 100ms後にアニメーション開始
- コンポーネント分割による段階的レンダリング

#### メモリ管理
- セッション内一時保持（永続化なし）
- 不要データの早期クリーンアップ
- 大きなオブジェクトの ref 化

## Quality Assurance

### Testing Strategy

#### Unit Tests (Jest + Testing Library)
- ResultScreen データレンダリング
- TypeCard プロパティ表示
- AxisScoreItem アニメーション
- エラー状態の適切な処理
- レスポンシブレイアウト

#### Integration Tests
- API client との結合テスト
- セッションContext との連携
- ルーティング動作確認

#### E2E Tests (Playwright)
- シーン完了 → 結果画面遷移
- スコアバーアニメーション確認
- 「もう一度診断する」フロー
- モバイル/デスクトップ表示確認
- エラー状態の再現テスト

### Accessibility Requirements（具体的実装指針）
- **スクリーンリーダー対応**:
  - 軸スコア: `aria-label="評価軸 {axisName}: {score}点"`
  - プログレスバー: `aria-label="{axisName}の進捗: {percentage}パーセント"`
  - タイプカード: `aria-label="診断結果: {typeName}タイプ"`
- **キーボードナビゲーション**: Tab順序 type-card → retry-button
- **カラーコントラスト比**: 4.5:1以上（WCAG AA準拠、axe-coreで検証）
- **フォーカス可視化**: 全インタラクティブ要素に明確なフォーカスリング

### Browser Compatibility
- Modern browsers（Chrome 90+, Firefox 88+, Safari 14+）
- iOS Safari、Android Chrome 対応
- IE11サポート対象外

## Implementation Phases

### Phase 1: Core Display (P1)
1. ResultScreen コンポーネント基本実装
2. API クライアント統合
3. TypeCard 基本表示
4. AxesScores 基本表示
5. エラー/ローディング状態

### Phase 2: Enhanced UX (P2)
1. スコアバーアニメーション
2. レスポンシブ対応
3. ActionButtons 実装
4. アクセシビリティ対応

### Phase 3: Polish & Testing (P3)
1. E2E テスト実装
2. パフォーマンス最適化
3. エラーハンドリング強化
4. ドキュメント整備

## Dependencies & Constraints

### Technical Dependencies
- Next.js 14 App Router
- React 18 (useState, useEffect)
- TypeScript 5.0+
- Tailwind CSS 3.0+
- React Router (useNavigate)

### External Dependencies
- Backend API (`/api/sessions/{id}/result`)
- セッション状態管理（Context/Store）
- エラーハンドリングユーティリティ

### Design System Integration
- 既存のThemeProvider活用
- CSS カスタムプロパティ標準化
- アニメーションライブラリ選定

## Risk Mitigation

### Technical Risks
- **LLM応答遅延**: タイムアウト設定（5s）とフォールバック
- **大量データ表示**: 軸数制限（max 6）と段階表示
- **モバイル性能**: アニメーション最適化とprefers-reduced-motion対応

### UX Risks
- **理解困難**: 軸説明文の充実とツールチップ
- **待機時間**: プログレッシブローディングとスケルトンUI
- **操作迷い**: 明確なCTAと直感的レイアウト

## Success Metrics

### Technical Metrics
- 結果画面レンダリング時間 < 500ms (95%ile)
- API エラー率 < 1%
- スコアアニメーション完了率 > 99%

### User Experience Metrics
- 結果画面滞在時間 > 30秒
- 再診断実行率 > 20%
- モバイル表示エラー率 < 0.1%

### Business Metrics
- 診断完了率向上（結果表示までの離脱率低下）
- ユーザー満足度（結果内容の理解度）
- リピート率向上（再診断機能活用）
