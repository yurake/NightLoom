# Data Model - NightLoom MVP診断体験

## Overview
NightLoom MVP は単一セッション診断を前提とし、4シーンの選択結果から評価軸スコアとタイプ分類を生成する。データはセッション期間中のみ保持し、永続ストレージには記録しない。以下では主なエンティティと属性、バリデーション、関係性を定義する。

---

## Entities

### Session
| Field | Type | Description | Validation / Notes |
|-------|------|-------------|--------------------|
| `id` | UUIDv4 | セッション識別子 | 必須 / 128-bit ランダム |
| `state` | Enum(`INIT`, `PLAY`, `RESULT`) | セッション状態 | 遷移: INIT→PLAY→RESULT |
| `initialCharacter` | string | 初期候補の50音文字 | 全角1文字 |
| `keywordCandidates` | array<string> | 候補単語4件 | 各1〜20文字、日本語対応 |
| `selectedKeyword` | string? | ユーザーが確定した単語 | 必須（state >= PLAY） |
| `themeId` | string | UIテーマ識別子 | `serene`, `adventure`, `focus`, `fallback` 等 |
| `scenes` | array<Scene> | シーン一覧（1〜4） | state=PLAY: 現在までのシーンを保持 |
| `choices` | array<ChoiceRecord> | 選択履歴 | シーン番号昇順で保存 |
| `rawScores` | map<axisId, float> | 累積スコア（-5.0〜5.0） | state=RESULT で確定 |
| `normalizedScores` | map<axisId, float> | 正規化スコア（0〜100） | state=RESULT で必須 |
| `typeProfiles` | array<TypeProfile> | 生成されたタイプ | state=RESULT で4〜6件 |
| `fallbackFlags` | array<string> | 発動したフォールバック種別 | 例: `AXIS_FALLBACK` |
| `createdAt` | datetime | セッション開始時刻 |  |
| `completedAt` | datetime? | 結果生成完了時刻 | state=RESULT時に設定 |

### Scene
| Field | Type | Description | Validation / Notes |
|-------|------|-------------|--------------------|
| `sceneIndex` | int | 1〜4のシーン番号 | 必須 |
| `themeId` | string | シーン毎のテーマ（セッションと同一） |  |
| `narrative` | string | 短いストーリーテキスト | 5秒以内で読める長さ |
| `choices` | array<Choice> | 選択肢4件 |  |

### Choice
| Field | Type | Description | Validation / Notes |
|-------|------|-------------|--------------------|
| `id` | string | 選択肢ID（`choice_{scene}_{index}`） | 必須 |
| `text` | string | 表示テキスト | 40文字以内推奨 |
| `weights` | map<axisId, float> | 評価軸重み（-1.0〜1.0） | 軸数分の値を保持 |

### ChoiceRecord
| Field | Type | Description |
|-------|------|-------------|
| `sceneIndex` | int | 選択されたシーン番号 |
| `choiceId` | string | 選択肢ID |
| `timestamp` | datetime | 選択時刻 |

### Axis
| Field | Type | Description | Validation / Notes |
|-------|------|-------------|--------------------|
| `id` | string | 軸識別子 | 一意 |
| `name` | string | 軸名（英語 Title Case） | 20文字以内 |
| `description` | string | 軸説明 |  |
| `direction` | string | 表示用ラベル（例: `論理的 ⟷ 感情的`） | |

### AxisScore
| Field | Type | Description | Validation / Notes |
|-------|------|-------------|--------------------|
| `axisId` | string | 軸識別子 | Axis.id と一致 |
| `score` | float | 正規化スコア（0〜100） | 小数第1位表示 |
| `rawScore` | float | 加重前スコア（-5.0〜5.0） | |

### TypeProfile
| Field | Type | Description | Validation / Notes |
|-------|------|-------------|--------------------|
| `name` | string | タイプ名 | 英語1〜2語、14文字以内 |
| `description` | string | タイプ説明 |  |
| `keywords` | array<string> | 関連キーワード | 例: 行動特性タグ |
| `dominantAxes` | array<string> | 主軸ID（2件） | Axis.id の配列 |
| `polarity` | string | 極性（例: `Hi-Lo`） | |
| `meta` | object | 補助情報（cell, isNeutral等） | 任意 |

### ThemeDescriptor
| Field | Type | Description | Validation / Notes |
|-------|------|-------------|--------------------|
| `themeId` | string | テーマ識別子 | `serene`, `adventure`, `focus`, `fallback` |
| `palette` | ThemeTokens | カラーパレット | CSS変数とTailwindクラスの組み合わせ |
| `typography` | object | フォント設定 | フォントファミリー、サイズ、weight定義 |
| `assets` | array<string> | 使用する背景/イラスト | 背景画像パス配列 |

### ThemeTokens
| Field | Type | Description | Validation / Notes |
|-------|------|-------------|--------------------|
| `primary` | string | メインカラー | HEX形式（例: `#3B82F6`） |
| `secondary` | string | セカンダリカラー | HEX形式 |
| `background` | string | 背景色 | HEX形式 |
| `surface` | string | サーフェス色 | カードや入力フィールド背景 |
| `text` | object | テキスト色定義 | `primary`, `secondary`, `muted`を含む |
| `accent` | string | アクセントカラー | ボタンやハイライト用 |
| `border` | string | ボーダー色 | コンポーネント境界線 |
| `cssVariables` | map<string, string> | CSS変数マッピング | `--color-primary: ${primary}` 形式 |
| `tailwindClasses` | map<string, string> | Tailwindクラスマッピング | セマンティック名からクラス名への変換 |

### ThemeState
| Field | Type | Description | Validation / Notes |
|-------|------|-------------|--------------------|
| `currentThemeId` | string | 現在適用中のテーマ | デフォルト: `serene` |
| `availableThemes` | array<string> | 選択可能テーマ一覧 | 4種類固定 |
| `isLoading` | bool | テーマ切替処理中フラグ | 切替アニメーション制御用 |
| `persistenceEnabled` | bool | ローカル保存の有効性 | ブラウザサポート状況に依存 |

---

## Relationships
- **Session 1 - n Scene**: `Session.scenes` はシーンデータを保持。Scene.themeId は Session.themeId と一致する。
- **Session 1 - n ChoiceRecord**: 選択履歴はセッション内で時系列に並び、Scene.sceneIndex と ChoiceRecord.sceneIndex が一致する。
- **Scene 1 - 4 Choice**: 各シーンに4つの選択肢が紐づく。
- **Session 1 - n AxisScore**: state=RESULT 時に評価軸の結果を保持。Axis に対するスコア。
- **Session 1 - n TypeProfile**: 結果画面で提示するタイプ集合。dominantAxes が Axis に紐づく。
- **ThemeDescriptor 1 - 1 ThemeTokens**: 各テーマは専用のカラーパレットを持つ。
- **ThemeState 1 - 1 Session**: セッション開始時にテーマが選択され、全画面で一貫適用される。
- **ThemeTokens 1 - n cssVariables**: 各テーマトークンは複数のCSS変数として展開される。

---

## Validation Rules & State Transitions

### State Transitions
```
INIT --(keyword確定)--> PLAY --(各シーン選択)--> RESULT
```
- INIT state: `selectedKeyword` が未設定、`choices` 空。シーン取得は禁止。
- PLAY state: `selectedKeyword` が必須。`sceneIndex` が進むたびに ChoiceRecord が追加される。
- RESULT state: `rawScores` → `normalizedScores` → `typeProfiles` が確定し、`completedAt` を記録。結果取得後にセッション破棄。

### Validation
- `keywordCandidates` は常に 4 件返却。自由入力は1〜20文字、禁止語フィルタで検証。
- `weights` の範囲は [-1.0, 1.0]。計算後の `rawScores` は [-5.0, 5.0] に収まるようチェック。
- `normalizedScores` は線形変換で [0, 100] にクランプ。全軸同値なら 50.0 に補正。
- `typeProfiles` は重複不可、名称はユニーク。
- セッションの API はステートに応じたガード（INITで結果取得を禁止など）を実施する。

---

## Logging & Metrics Data
- `sessionId`, `state`, `themeId`
- `request_latency_ms`（bootstrap, keyword, scene, result）
- `fallback_used`（bool）と `fallback_reason`
- `llm_provider`, `retry_count`, `prompt_tokens`
- `result_generation_ms`, `animation_duration_ms`（クライアント側測定予定）

---

---

## テーマ切替実装方式

### 技術アーキテクチャ

#### 1. テーマデータ管理
```typescript
// frontend/app/theme/tokens/[themeId].ts
interface ThemeTokens {
  primary: string;
  secondary: string;
  background: string;
  surface: string;
  text: {
    primary: string;
    secondary: string;
    muted: string;
  };
  accent: string;
  border: string;
  cssVariables: Record<string, string>;
  tailwindClasses: Record<string, string>;
}
```

#### 2. テーマ切替メカニズム
- **Context API**: `ThemeProvider` でアプリ全体のテーマ状態を管理
- **ローカルストレージ連携**: `localStorage.setItem('nightloom-theme', themeId)` で永続化
- **セッション復元**: ページリロード時に保存されたテーマを自動復元
- **フォールバック**: ストレージ無効時は `serene` テーマを既定で適用

#### 3. 動的スタイル適用方式
```typescript
// CSS変数の動的更新
const applyTheme = (theme: ThemeTokens) => {
  Object.entries(theme.cssVariables).forEach(([key, value]) => {
    document.documentElement.style.setProperty(key, value);
  });
};

// Tailwindクラスの動的切替
const getThemeClasses = (semantic: string) => {
  return currentTheme.tailwindClasses[semantic] || 'bg-gray-100';
};
```

#### 4. パフォーマンス最適化
- **遅延読み込み**: テーマトークンは初回選択時に動的インポート
- **メモ化**: React.useMemo でテーマ計算結果をキャッシュ
- **CSS変数**: 再レンダリング最小化のため Tailwind より CSS変数を優先
- **アニメーション制御**: `prefers-reduced-motion` 考慮でテーマ切替時間を調整

#### 5. 実装コンポーネント
```typescript
// frontend/app/theme/ThemeProvider.tsx
interface ThemeContextValue {
  currentTheme: ThemeTokens;
  themeId: string;
  setTheme: (themeId: string) => Promise<void>;
  availableThemes: string[];
  isLoading: boolean;
}

// frontend/app/theme/ThemeSwitcher.tsx
const ThemeSwitcher: React.FC = () => {
  const { setTheme, availableThemes, currentTheme } = useTheme();
  // テーマ選択UI実装
};
```

### セッション統合
- **セッション開始時**: 選択されたテーマIDを `Session.themeId` に記録
- **シーン表示**: `Scene.themeId` と統一してビジュアル一貫性を保持
- **結果画面**: 診断中と同一テーマで結果を表示

### エラーハンドリング
- **テーマ読み込み失敗**: `fallback` テーマに自動切り替え
- **ローカルストレージエラー**: セッション中はメモリ保持、次回は既定テーマ
- **CSS適用失敗**: システムの既定スタイルで表示継続

## Open Questions
現時点でデータ構造に関する未解決事項はない。将来、履歴保存や共有機能を実装する際に永続スキーマを再設計する。
